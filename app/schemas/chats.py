import datetime
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field

# Request model for creating a new chat 
class CreateChatRequest(BaseModel):
    user_id: UUID
    model_id: Optional[UUID] = Field(
        default=None,
        description="Defaults to DEFAULT_MODEL if null, otherwise set to model_id"
    ) 
    workspace_id: Optional[UUID] = Field(
        default=None,
        description="Defaults to None if chat is in global space, otherwise set to workspace_id"
    )
    initial_message: str
    

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
    workspace_id:  Optional[UUID] = None
    title: str
    messages: List[MessageResponse] = []

    

class CreateMessageRequest(BaseModel):
    conversation_id: UUID
    content: str
    model_id: Optional[UUID] = Field(
        default=None,
        description="Defaults to last used model if null, otherwise set to new model_id"
    )

class ChatTitlesResponse(BaseModel): # not being used
    conversation_id: UUID
    title: str

class UpdateChatTitleRequest(BaseModel):
    new_title: str = Field(..., min_length=1, max_length=100)

class UpdateChatTitleResponse(BaseModel):
    conversation_id: UUID
    title: str
    
class ChatTitles(BaseModel):
    conversation_id: UUID
    title: str

class PaginatedChatResponse(BaseModel):
    total_count: int
    conversations: List[ChatTitles]