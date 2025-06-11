import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.database.connection import PostgresConnection
from app.database.folder_queries import create_folder_query, delete_folder_query, get_user_global_folders_query
from app.schemas.folders import CreateFolderRequest, DeleteFolderRequest, FolderInfo, FolderResponse
from app.schemas.movements import LocationType


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/folders", tags=["folders"], dependencies=[Depends(get_current_user)])


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
            
            

@router.delete(
    "/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a Folder. By default, contents are moved to global space. Set mode=permanent to delete all contents."
)
async def delete_folder(
    folder_id: UUID,
    request: DeleteFolderRequest
):
    """
    Delete a folder with specified deletion mode:
    - ARCHIVE (default): Moves all conversations to global space
    - PERMANENT: Permanently deletes the folder and all its contents

    """
    try:
        # Use default mode if request not provided
        mode = request.mode if request else DeletionMode.ARCHIVE
        
        with PostgresConnection() as conn:
            delete_folder_query(
                conn=conn,
                folder_id=folder_id,
                mode=mode
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete folder"
        )
        
  
@router.get(
    "/global/{user_id}",
    response_model=List[FolderInfo],
    summary="Get User's Global Folders",
    description="Retrieves all global folders (not in workspaces) for the specified user"
)
async def get_user_global_folders(
    user_id: UUID,
) -> List[FolderInfo]:
    """
    Retrieves all personal folders and their conversations for the specified user.
    These are folders that don't belong to any workspace.
    """
    try:
        with PostgresConnection() as conn:
            folders = get_user_global_folders_query(
                conn=conn,
                user_id=user_id
            )
            return folders
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving personal folders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve personal folders"
        )