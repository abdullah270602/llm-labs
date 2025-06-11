import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from app.auth.dependencies import get_current_user
from app.database.chat_queries import delete_chat_query, insert_chat, insert_chat_messages, select_chat_by_id, select_chat_context_by_id, select_user_chat_titles_and_count_single_row, update_chat_title_query, update_conversation_model
from app.database.connection import PostgresConnection
import psycopg2.extras

from app.routes.constant import ASSISTANT_ROLE, DEFAULT_MODEL, USER_ROLE
from app.services.generate_title import get_chat_title
from app.services.model_services import get_reply_from_model
from app.services.agents import call_loop_agent

psycopg2.extras.register_uuid()

from app.schemas.chats import (
    CreateChatRequest,
    CreateChatResponse,
    CreateMessageRequest,
    MessageResponse,
    PaginatedChatResponse,
    UpdateChatTitleRequest,
    UpdateChatTitleResponse,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/chats", tags=["chats"], dependencies=[Depends(get_current_user)])


@router.post(
    "/",
    response_model=CreateChatResponse,
    status_code=status.HTTP_201_CREATED,
    description="Creates a new chat",
)
async def create_chat(request: CreateChatRequest):
    try:

        generated_title = get_chat_title(request.initial_message)

        chat = [
            {"role": USER_ROLE, "content": request.initial_message},
        ]
        current_model = DEFAULT_MODEL

        if request.model_id:
            current_model = request.model_id
                
        # Call LLM to generate a response
        llm_response = get_reply_from_model(model_id=current_model, chat=chat)

    except Exception as e:
        logger.error(f"Error during LLM call for title generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate chat response")

    try:
        with PostgresConnection() as conn:  # TODO replace with async connection
            # Insert chat record
            chat_record = insert_chat(
                conn, request.user_id, current_model, generated_title, request.workspace_id
            )

            # Prepare messages: user first, then assistant
            messages_data = [
                (
                    chat_record["conversation_id"],
                    USER_ROLE,
                    None,
                    request.initial_message,
                ),
                (
                    chat_record["conversation_id"],
                    ASSISTANT_ROLE,
                    current_model,
                    llm_response,
                ),
            ]

            # Insert both messages in one query
            inserted_messages = insert_chat_messages(conn, messages_data)
            # Convert inserted messages to Pydantic models
            messages = [MessageResponse(**msg) for msg in inserted_messages]
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    except Exception as e:
        logger.error(f"Database error during chat creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create chat in database")

    # Construct and return response
    chat_response = CreateChatResponse(
        conversation_id=chat_record["conversation_id"],
        current_model_id=current_model,
        workspace_id=request.workspace_id,
        title=generated_title,
        messages=messages,
    )

    return chat_response


@router.post(
    "/message/",
    response_model=List[MessageResponse],
    status_code=status.HTTP_201_CREATED,
    description="Creates a new message in a chat",
)
async def create_message(request: CreateMessageRequest):
    try:
        with PostgresConnection() as conn:  # TODO replace with async connection

            # Retrieve conversation context to get model_id and existing messages
            chat_record = select_chat_context_by_id(conn, request.conversation_id)
            if not chat_record:
                logger.info(
                    f"Chat context for conversation_id {request.conversation_id} not found."
                )
                raise HTTPException(status_code=404, detail="Conversation not found")

            current_model = chat_record["current_model_id"]
            chat_history = chat_record["messages"]
            chat_history.append({"role": USER_ROLE, "content": request.content})

            # If the request has a new model_id, switch conversation's current_model_id
            # Otherwise, we keep using the existing one.
            if request.model_id and request.model_id != current_model:
                # Update DB so this model becomes the new default
                update_conversation_model(
                    conn, request.conversation_id, request.model_id
                )
                current_model = request.model_id
                logger.info(
                    f"Switched conversation {request.conversation_id} to model {current_model}"
                )

            # Call LLM to generate a response
            llm_response = get_reply_from_model(
                model_id=current_model, chat=chat_history
            )

            # Prepare messages: user first, then assistant
            messages_data = [
                (request.conversation_id, USER_ROLE, None, request.content),
                (request.conversation_id, ASSISTANT_ROLE, current_model, llm_response),
            ]

            # Insert both messages in one query
            inserted_messages = insert_chat_messages(conn, messages_data)

            # Convert inserted messages to Pydantic models
            messages = [MessageResponse(**msg) for msg in inserted_messages]

    except Exception as e:
        logger.error(
            f"Error in creating message for conversation {request.conversation_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to process message creation"
        )

    return messages


@router.get(
    "/{chat_id}/", status_code=status.HTTP_200_OK, description="Get whole chat by ID"
)
async def get_chat_by(chat_id: UUID):
    try:
        with PostgresConnection() as conn:
            chat = select_chat_by_id(conn, chat_id)
    except Exception as e:
        logger.error(
            f"Database error when retrieving chat {chat_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve chat from database"
        )

    if not chat:
        logger.info(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    return chat


@router.put(
    "/title/{chat_id}",
    response_model=UpdateChatTitleResponse,
    status_code=status.HTTP_200_OK,
    description="Update chat title",
)
async def update_chat_title(chat_id: UUID, request: UpdateChatTitleRequest):
    try:
        with PostgresConnection() as conn:
            updated_record = update_chat_title_query(conn, chat_id, request.new_title)
            if not updated_record:
                logger.info(f"Chat {chat_id} not found for title update")
                raise HTTPException(status_code=404, detail="Chat not found")

        response = UpdateChatTitleResponse(**updated_record)

    except Exception as e:
        logger.error(f"Error updating chat title for {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update chat title")

    return response


@router.delete(
    "/{chat_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete chat by ID",
)
async def delete_chat(chat_id: UUID):
    try:
        with PostgresConnection() as conn:
            deleted = delete_chat_query(conn, chat_id)
            if not deleted:
                logger.info(f"Chat {chat_id} not found for deletion")
                raise HTTPException(status_code=404, detail="Chat not found")

    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete chat")


@router.get(
    "/titles/{user_id}/",
    response_model=PaginatedChatResponse,
    status_code=status.HTTP_200_OK,
    description="Get chat titles within the global space for a user",
)
async def get_user_global_chats(
    user_id: UUID,
    limit: int = Query(default=10, ge=1),
    offset: int = Query(default=0, ge=0),
):
    """
    Return paginated conversations for a given user,
    along with the total_count in the same response.
    """
    try:
        # Using a context manager for a synchronous DB connection
        with PostgresConnection() as conn:
            result = select_user_chat_titles_and_count_single_row(
                conn, user_id, limit, offset
            )
    except Exception as e:
        logger.error(f"DB error fetching chats for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not fetch user chats")

    # Build the Pydantic response object
    response_data = PaginatedChatResponse(
        total_count=result["total_count"], conversations=result["conversations"]
    )
    return response_data
