import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.database.connection import PostgresConnection
from app.database.folder_queries import create_folder_query
from app.schemas.folders import CreateFolderRequest, FolderResponse
from app.schemas.movements import LocationType


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/folders", tags=["folders"])


@router.post(
    '/',
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
    description='Creates a new folder in either a workspace or global space, if global the id will be NULL'
)
async def create_folder(request: CreateFolderRequest):
    """
    Create a new folder in either a workspace or global space.
    Folders cannot be created inside other folders.
    """
    try:
        with PostgresConnection() as conn:
            # Validate location type
            if request.location.type == LocationType.FOLDER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Folders cannot be created inside other folders"
                )
                
            folder = create_folder_query(
                conn=conn,
                name=request.name,
                user_id=request.user_id,
                location_type=request.location.type,
                workspace_id=request.location.id  # Will be None for global space
            )
            
            return FolderResponse(**folder)
    
    except HTTPException:
        raise
            
    except Exception as e:
        logger.error(f'Error creating folder: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail='Failed to create folder'
        )
            