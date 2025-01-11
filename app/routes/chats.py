from uuid import UUID
from fastapi import APIRouter
from app.database.connection import PostgresConnection
import psycopg2.extras

from app.routes.constant import MODEL_ROLE, USER_ROLE
psycopg2.extras.register_uuid()
from app.database.queries import create_chat, create_chat_message
from app.schemas.chats import CreateChatRequest, MessageResponse, ChatResponse

router = APIRouter(prefix="/chats", tags=["chats"])


def call_llm(model_id: UUID, conversation_id: UUID, message: str) -> str:
    # Placeholder function to simulate LLM response.
    # Replace this with actual logic to call your LLM service.
    return f"Assumed LLM response (Testing)"


@router.post("/", response_model=ChatResponse, status_code=201)
async def create_chat_endpoint(request: CreateChatRequest):
    generated_title = "-- TESTING --"  # TODO  generate a title based on the chat content

    with PostgresConnection() as conn: # TODO replace with async connection
        # Create chat record
        chat_record = create_chat(conn, request.user_id, request.model_id, generated_title)

        messages = []

        # Insert user initial message
        user_message_record = create_chat_message(
            conn, chat_record["conversation_id"], USER_ROLE, request.initial_message 
        )
        messages.append(MessageResponse(**user_message_record))

        # Call LLM to generate a response
        llm_response = call_llm(
            model_id=request.model_id,
            conversation_id=chat_record["conversation_id"],
            message=request.initial_message
        )

        # Insert LLM response as assistant message
        assistant_message_record = create_chat_message(
            conn, chat_record["conversation_id"], MODEL_ROLE, llm_response
        )
        messages.append(MessageResponse(**assistant_message_record))

    # Construct and return response
    chat_response = ChatResponse(
        conversation_id=chat_record["conversation_id"],
        model_id=chat_record["model_id"],
        title=chat_record["title"],
        messages=messages
    )
    return chat_response
