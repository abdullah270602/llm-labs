from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ValidationInfo, field_validator


class LocationType(str, Enum):
    GLOBAL = 'global'  # Items not in any workspace or folder
    WORKSPACE = 'workspace'
    FOLDER = 'folder'
    
class ItemType(str, Enum):
    CHAT = 'chat'
    FOLDER = 'folder'
    

class Location(BaseModel):
    type: LocationType
    id: Optional[UUID] = None
    
    @field_validator('id')
    def validate_id(cls, v: Optional[UUID], info: ValidationInfo) -> Optional[UUID]:
        # In v2, we access other field values through info.data
        type_value = info.data.get('type')

        if type_value == LocationType.GLOBAL and v is not None:
            raise ValueError("Global location should not have an ID")
        if type_value != LocationType.GLOBAL and v is None:
            raise ValueError("Non-global locations must have an ID")
        return v
    
    
class MoveRequest(BaseModel):
    item_type: ItemType
    item_id: UUID
    destination: Location
    
    @field_validator('destination')
    def validate_destination(cls, v: Location, info: ValidationInfo) -> Location:
        # Access other field values through info.data
        current_data = info.data
        
        # Check if trying to move a folder into itself
        if (current_data.get('item_type') == ItemType.FOLDER and 
            v.type == LocationType.FOLDER and 
            v.id == current_data.get('item_id')):
            raise ValueError("Cannot move folder into itself")
            
        return v


class MoveResponse(BaseModel):
    item_type: ItemType
    item_id: UUID
    previous_location: Location
    new_location: Location