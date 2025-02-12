from datetime import datetime
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.movements import Location, LocationType
from app.schemas.workspaces import DeletionMode


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