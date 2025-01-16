import datetime
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
    role: str
    content: str

# Response model for a chat including its messages
class CreateChatResponse(BaseModel):
    conversation_id: UUID
    model_id: UUID
    title: str
    messages: List[MessageResponse] = []

# Request model for creating a new message in a chat
class CreateMessageRequest(BaseModel):
    conversation_id: UUID
    content: str

class ChatTitlesResponse(BaseModel):
    conversation_id: UUID
    title: str

class UpdateChatTitleRequest(BaseModel):
    new_title: str

class UpdateChatTitleResponse(BaseModel):
    conversation_id: UUID
    model_id: UUID
    userid: UUID
    title: str