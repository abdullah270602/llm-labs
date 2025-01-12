from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from app.database.connection import PostgresConnection
import psycopg2.extras

from app.routes.constant import MODEL_ROLE, USER_ROLE
psycopg2.extras.register_uuid()
from app.database.queries import (
    insert_chat,
    insert_chat_message,
    select_chat_by_id,
    select_chat_context_by_id,
    select_user_chat_titles,
)
from app.schemas.chats import (
    ConversationSummary,
    CreateChatRequest,
    CreateChatResponse,
    CreateMessageRequest,
    MessageResponse,
)

router = APIRouter(prefix="/chats", tags=["chats"])


def call_llm(model_id: UUID, conversation_id: UUID, message: str, context) -> str:
    # Placeholder function to simulate LLM response.
    # Replace this with actual logic to call your LLM service.
    return f"Assumed LLM response (Testing)"

# TODO Add error handling

@router.post("/", response_model=CreateChatResponse, status_code=201)
async def create_chat(request: CreateChatRequest):
    generated_title = "-- TESTING --"  # TODO  generate a title based on the chat content

    with PostgresConnection() as conn: # TODO replace with async connection
        # Create chat record
        chat_record = insert_chat(conn, request.user_id, request.model_id, generated_title)

        messages = []

        # Insert user initial message
        user_message_record = insert_chat_message(
            conn, chat_record["conversation_id"], USER_ROLE, request.initial_message 
        )
        messages.append(MessageResponse(**user_message_record))

        # Call LLM to generate a response
        llm_response = call_llm(
            model_id=request.model_id,
            conversation_id=chat_record["conversation_id"],
            message=request.initial_message,
            context=[]
        )

        # Insert LLM response as assistant message
        model_response_record = insert_chat_message(
            conn, chat_record["conversation_id"], MODEL_ROLE, llm_response
        )
        messages.append(MessageResponse(**model_response_record))

    # Construct and return response
    chat_response = CreateChatResponse(
        conversation_id=chat_record["conversation_id"],
        model_id=chat_record["model_id"],
        title=chat_record["title"],
        messages=messages
    )
    return chat_response


@router.post("/message/", response_model=List[MessageResponse], status_code=201)
async def create_message(request: CreateMessageRequest):
    with PostgresConnection() as conn:  # TODO replace with async connection
        
        # Retrieve conversation context to get model_id and existing messages
        chat_context = select_chat_context_by_id(conn, request.conversation_id)
        
        # Insert user message
        user_message_record = insert_chat_message(
            conn, request.conversation_id, USER_ROLE, request.content
        )
        messages = []
        
        messages.append(MessageResponse(**user_message_record))


        llm_response = call_llm(
            model_id= chat_context["model_id"],
            conversation_id=request.conversation_id,
            message=request.content,
            context=chat_context["messages"]
        )

        # Insert LLM response as assistant message
        model_response_record = insert_chat_message(
            conn, request.conversation_id, MODEL_ROLE, llm_response
        )
        messages.append(MessageResponse(**model_response_record))


    return messages


@router.get("/{chat_id}/",status_code=200)
async def get_chat_by(chat_id: UUID):
    with PostgresConnection() as conn:
        chat = select_chat_by_id(conn, chat_id)
        
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return chat
        
        
@router.get("/titles/{user_id}/", response_model=List[ConversationSummary])
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
        conversations = [ConversationSummary(**row) for row in rows]
        
        return conversations
    
    
    # GET /conversations/?userid=123e4567-e89b-12d3-a456-426614174000&limit=5&offset=10
