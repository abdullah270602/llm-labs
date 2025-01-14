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
    insert_chat,
    insert_chat_messages,
    select_chat_by_id,
    select_chat_context_by_id,
    select_user_chat_titles,
)
from app.schemas.chats import (
    ChatTitlesResponse,
    CreateChatRequest,
    CreateChatResponse,
    CreateMessageRequest,
    MessageResponse,
)

router = APIRouter(prefix="/api/chats", tags=["chats"])

# TODO Add error handling

@router.post("/", response_model=CreateChatResponse, status_code=201)
async def create_chat(request: CreateChatRequest):
        
    generated_title = get_chat_title(request.initial_message)
    
    chat = [{"role": USER_ROLE, "content": request.initial_message},]
    # Call LLM to generate a response
    llm_response = get_reply_from_model(
        model_id=request.model_id,
        chat=chat
    )

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
    with PostgresConnection() as conn:  # TODO replace with async connection
        
        # Retrieve conversation context to get model_id and existing messages
        chat_record = select_chat_context_by_id(conn, request.conversation_id)
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

    return messages


@router.get("/{chat_id}/",status_code=200)
async def get_chat_by(chat_id: UUID):
    with PostgresConnection() as conn:
        chat = select_chat_by_id(conn, chat_id)
        
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return chat
        
        
@router.get("/titles/{user_id}/", response_model=List[ChatTitlesResponse])
async def get_user_chat_titles(
    user_id: UUID,
    limit: int = Query(10, ge=1, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    with PostgresConnection() as conn:
        rows = select_user_chat_titles(conn, user_id, limit, offset)
        if not rows:
            conversations = []
            
        # Convert each row into a ConversationSummary model
        conversations = [ChatTitlesResponse(**row) for row in rows]
        
    return conversations

