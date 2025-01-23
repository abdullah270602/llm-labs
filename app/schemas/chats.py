import datetime
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

# Request model for creating a new chat 
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
    model_id: Optional[UUID] = None 

# Response model for a chat including its messages
class CreateChatResponse(BaseModel):
    conversation_id: UUID
    current_model_id: UUID
    title: str
    messages: List[MessageResponse] = []

class CreateMessageRequest(BaseModel):
    conversation_id: UUID
    content: str
    model_id: Optional[UUID] = None  # NEW: user can override or specify a model

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