from uuid import uuid4
from fastapi import APIRouter, HTTPException

from app.models.chats import (
    ChatCreateRequest,
    ChatCreateResponse,
    MessageAddResponse,
    MessageCreateRequest,
    MessageResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory storage for demonstration (replace with database logic)
chats = {}


@router.post("/", response_model=ChatCreateResponse)
async def create_chat(request: ChatCreateRequest):
    """
    Create a new chat and add the first message.
    """

    chat_id = uuid4()

    # Simulate bot response
    bot_response = "Hi! This is a bot's response."

    message_response = MessageResponse(
        user_prompt=request.message.user_prompt,
        bot_response=bot_response,
    )

    # Save chat to in-memory storage
    chats[chat_id] = {
        "user_id": request.user_id,
        "conversation": [message_response],
    }

    # Return the response
    return ChatCreateResponse(
        user_id=request.user_id,
        chat_id=chat_id,
        message=message_response,
    )


@router.post("/send_message", response_model=MessageAddResponse)
async def send_message(request: MessageCreateRequest):
    """
    Add a new message to an existing chat.
    """
    # Validate chat ID
    chat_data = chats.get(request.chat_id)
    if not chat_data:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Simulate bot response
    bot_response = "This is the bot's response to your message."

    # Create the response message
    new_message = MessageResponse(
        user_prompt=request.message.user_prompt,
        bot_response=bot_response,
    )

    # Append the new message to the chat's conversation
    chat_data["conversation"].append(new_message)

    # Return the response
    return MessageAddResponse(
        chat_id=request.chat_id,
        message=new_message,
    )
