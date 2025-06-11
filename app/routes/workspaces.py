import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.custom_exceptions import WorkspaceLimitExceeded
from app.database.connection import PostgresConnection
from app.database.workspace_queries import (
    create_workspace_query,
    delete_workspace_query,
    get_user_workspaces_query,
    get_workspace_chats_query,
    get_workspace_folders_query,
)
from app.schemas.workspaces import (
    CreateWorkspaceRequest,
    DeleteWorkspaceRequest,
    UserWorkspacesResponse,
    WorkspaceChats,
    WorkspaceFoldersResponse,
    WorkspaceResponse,
)


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/workspaces", tags=["workspaces"], dependencies=[Depends(get_current_user)])


@router.post(
    '/', 
    response_model=WorkspaceResponse, 
    status_code=status.HTTP_201_CREATED, 
    description='Creates a new workspace'
)
async def create_workspace(request: CreateWorkspaceRequest):
    try:
        with PostgresConnection() as conn:
            workspace = create_workspace_query(conn, request.user_id, request.name)
    except WorkspaceLimitExceeded as e:
        # Return a 400 Bad Request error if the workspace limit is exceeded.
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f'Error creating workspace: {e}')
        raise HTTPException(status_code=500, detail='Failed to create workspace')
    
    return WorkspaceResponse(**workspace)


@router.get(
    "/user/{user_id}",
    response_model=UserWorkspacesResponse,
    description="Get all workspaces for a user"
)
async def get_user_workspaces(user_id: UUID):
    try:
        with PostgresConnection() as conn:
            workspaces = get_user_workspaces_query(conn, user_id)
        return UserWorkspacesResponse(workspaces=workspaces)
            
    except Exception as e:
        logger.error(f"Error retrieving user workspaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workspaces"
        )

@router.delete(
    '/{workspace_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    description='Delete a workspace. By default, contents are moved to global space. Set mode=permanent to delete all contents.'
)
async def delete_workspace(
    workspace_id: UUID,
    request: DeleteWorkspaceRequest
):
    try:
        with PostgresConnection() as conn:
            workspace_existed = delete_workspace_query(
                conn, 
                workspace_id, 
                request.mode
            )
            
        if not workspace_existed:
            raise HTTPException(
                status_code=404,
                detail='Workspace not found'
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error deleting workspace: {e}')
        raise HTTPException(
            status_code=500,
            detail='Failed to delete workspace'
        )


@router.get(
    "/{workspace_id}/chats",
    response_model=WorkspaceChats,
    description="Retrieves all chats within a workspace."
)
async def get_workspace_chats(workspace_id: UUID):
    try:
        with PostgresConnection() as conn:
            result = get_workspace_chats_query(conn, workspace_id)
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace not found"
                )
            
            return WorkspaceChats(**result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workspace chats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workspace chats"
        )


@router.get(
    "/{workspace_id}/folders",
    response_model=WorkspaceFoldersResponse,
    description="Retrieve workspace with all folders and their conversations"
)
async def get_workspace_folders(workspace_id: UUID):
    try:
        with PostgresConnection() as conn:
            workspace_data = get_workspace_folders_query(conn, workspace_id)
            return WorkspaceFoldersResponse(**workspace_data)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workspace folders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workspace folders"
        )