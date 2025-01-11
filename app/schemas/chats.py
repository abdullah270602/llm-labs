from uuid import UUID
from typing import List
from pydantic import BaseModel

# Request model for creating a new chat (without requiring a title)
class CreateChatRequest(BaseModel):
    user_id: UUID
    model_id: UUID
    initial_message: str  # Required initial user message

# Response model for a single message
class MessageResponse(BaseModel):
    message_id: int
    conversation_id: UUID
    sender_role: str
    content: str

# Response model for a chat including its messages
class ChatResponse(BaseModel):
    conversation_id: UUID
    model_id: UUID
    title: str
    messages: List[MessageResponse] = []
