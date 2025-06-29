from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.folders import FolderInfo


class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class CreateWorkspaceRequest(WorkspaceBase):
    user_id: UUID


class WorkspaceResponse(WorkspaceBase):
    workspace_id: UUID
    user_id: UUID
    created_at: datetime
    

class WorkspaceChat(BaseModel):
    conversation_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    

class WorkspaceChats(BaseModel):
    workspace_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    chats: List[WorkspaceChat] = []  # Default empty list


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
    

class WorkspaceFoldersResponse(BaseModel):  # Updated to include workspace info
    workspace_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    folders: List[FolderInfo] = []  # Default empty list