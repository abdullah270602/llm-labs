import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from app.database.connection import PostgresConnection
import psycopg2.extras

from app.routes.constant import ASSISTANT_ROLE, USER_ROLE
from app.services.generate_title import get_chat_title
from app.services.model_services import get_reply_from_model
psycopg2.extras.register_uuid()
from app.database.queries import (
    delete_chat_query,
    insert_chat,
    insert_chat_messages,
    select_chat_by_id,
    select_chat_context_by_id,
    select_user_chat_titles,
    update_chat_title_query,
)
from app.schemas.chats import (
    ChatTitlesResponse,
    CreateChatRequest,
    CreateChatResponse,
    CreateMessageRequest,
    MessageResponse,
    UpdateChatTitleRequest,
    UpdateChatTitleResponse,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("/", response_model=CreateChatResponse, status_code=201)
async def create_chat(request: CreateChatRequest):
    
    try:
        
        generated_title = get_chat_title(request.initial_message)
        
        chat = [{"role": USER_ROLE, "content": request.initial_message},]
        # Call LLM to generate a response
        llm_response = get_reply_from_model(
            model_id=request.model_id,
            chat=chat
        )
    except Exception as e:
        logger.error(f"Error during LLM call or title generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate chat response")

    try:
        with PostgresConnection() as conn: # TODO replace with async connection        
            # Insert chat record
            chat_record = insert_chat(conn, request.user_id, request.model_id, generated_title)

            # Prepare message data for both user and assistant
            messages_data = [
                (chat_record["conversation_id"], USER_ROLE, request.initial_message),
                (chat_record["conversation_id"], ASSISTANT_ROLE, llm_response)
            ]
            
            # Insert both messages in one query
            inserted_messages = insert_chat_messages(conn, messages_data)
            # Convert inserted messages to Pydantic models
            messages = [MessageResponse(**msg) for msg in inserted_messages]

    except Exception as e:
        logger.error(f"Database error during chat creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create chat in database")

    # Construct and return response
    chat_response = CreateChatResponse(
        conversation_id=chat_record["conversation_id"],
        model_id=chat_record["model_id"],
        title=generated_title,
        messages=messages
    )
    return chat_response


@router.post("/message/", response_model=List[MessageResponse], status_code=201)
async def create_message(request: CreateMessageRequest):
    try:
        with PostgresConnection() as conn:  # TODO replace with async connection
            
            # Retrieve conversation context to get model_id and existing messages
            chat_record = select_chat_context_by_id(conn, request.conversation_id)
            if not chat_record:
                    logger.info(f"Chat context for conversation_id {request.conversation_id} not found.")
                    raise HTTPException(status_code=404, detail="Conversation not found")

            model_id = chat_record["model_id"]
            chat = chat_record["messages"]
            chat.append({"role": USER_ROLE, "content": request.content})
            
            # Call LLM to generate a response
            llm_response = get_reply_from_model(
                model_id=model_id,
                chat=chat
            )
            
            # Prepare message data for both user and assistant
            messages_data = [
                (request.conversation_id, USER_ROLE, request.content),
                (request.conversation_id, ASSISTANT_ROLE, llm_response)
            ]
            
            # Insert both messages in one query
            inserted_messages = insert_chat_messages(conn, messages_data)
            
            # Convert inserted messages to Pydantic models
            messages = [MessageResponse(**msg) for msg in inserted_messages]

    except Exception as e:
        logger.error(f"Error in creating message for conversation {request.conversation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process message creation")

    return messages


@router.get("/{chat_id}/",status_code=200)
async def get_chat_by(chat_id: UUID):
    try:
        with PostgresConnection() as conn:
            chat = select_chat_by_id(conn, chat_id)
    except Exception as e:
        logger.error(f"Database error when retrieving chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve chat from database")
        
    if not chat:
        logger.info(f"Chat {chat_id} not found")
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return chat
        
        
@router.get("/titles/{user_id}/", response_model=List[ChatTitlesResponse])
async def get_user_chat_titles(
    user_id: UUID,
    limit: int = Query(10, ge=1, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    try:
        with PostgresConnection() as conn:
            rows = select_user_chat_titles(conn, user_id, limit, offset)
    except Exception as e:
        logger.error(f"Database error when retrieving chat titles for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve chat titles from database")
    
    if not rows:
        logger.info(f"No chat titles found for user {user_id}")
        conversations = []
            
        # Convert each row into a ChatTitlesResponse model
    conversations = [ChatTitlesResponse(**row) for row in rows]
        
    return conversations


@router.put("/title/{chat_id}", response_model=UpdateChatTitleResponse, status_code=200)
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


@router.delete("/{chat_id}/", status_code=204)
async def delete_chat(chat_id: UUID):
    try:
        with PostgresConnection() as conn:
            deleted= delete_chat_query(conn, chat_id)
            if not deleted:
                logger.info(f"Chat {chat_id} not found for deletion")
                raise HTTPException(status_code=404, detail="Chat not found")

    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete chat")
