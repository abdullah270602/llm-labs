from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.movements import Location



class CreateFolderRequest(BaseModel):
    name: str
    user_id: UUID
    location: Location  # Using your existing Location model

class FolderResponse(BaseModel):
    folder_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    workspace_id: Optional[UUID] = None  # Optional since it could be in global space
    
class DeletionMode(str, Enum):
    ARCHIVE = "archive"     # Move contents to global space (default)
    PERMANENT = "permanent" # Delete everything

class DeleteFolderRequest(BaseModel):
    mode: Optional[DeletionMode] = Field(
        default=DeletionMode.ARCHIVE,
        description="Defaults to 'archive' which moves contents to global space. Use 'permanent' to delete all contents."
    )
    
class ChatInFolder(BaseModel):
    conversation_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

class FolderInfo(BaseModel):  # Renamed from FolderWithChats and removed workspace_id
    folder_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    conversations: List[ChatInFolder] = []  # Default empty list