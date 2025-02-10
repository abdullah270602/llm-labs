from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field


class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CreateWorkspaceRequest(WorkspaceBase):
    user_id: UUID


class WorkspaceResponse(WorkspaceBase):
    workspace_id: UUID
    user_id: UUID
    created_at: datetime
    

class AddChatToWorkspaceRequest(BaseModel):
    conversation_id: UUID


class AddChatToWorkspaceResponse(BaseModel):
    conversation_id: UUID
    workspace_id: UUID
    

class WorkspaceChat(BaseModel):
    conversation_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    current_model_id: UUID
    

class WorkspaceFolder(BaseModel):
    pass


class WorkspaceContents(BaseModel):
    workspace_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    chats: List[WorkspaceChat] = []  # Default empty list
    folders: List[WorkspaceFolder] = []  # Default empty list until implemented


class Workspace(BaseModel):
    workspace_id: UUID
    name: str
    created_at: datetime

class UserWorkspacesResponse(BaseModel):
    workspaces: List[Workspace]
    

class DeletionMode(str, Enum):
    ARCHIVE = "archive"     # Move contents to global space (default)
    PERMANENT = "permanent" # Delete everything

class DeleteWorkspaceRequest(BaseModel):
    mode: Optional[DeletionMode] = Field(
        default=DeletionMode.ARCHIVE,
        description="Defaults to 'archive' which moves contents to global space. Use 'permanent' to delete all contents."
    )