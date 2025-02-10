import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.custom_exceptions import WorkspaceLimitExceeded
from app.database.connection import PostgresConnection
from app.database.queries import add_chat_to_workspace_query, create_workspace_query, delete_workspace_query, get_workspace_contents_query, remove_chat_from_workspace_query
from app.schemas.workspaces import AddChatToWorkspaceRequest, AddChatToWorkspaceResponse, CreateWorkspaceRequest, WorkspaceContents, WorkspaceResponse


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.post(
    '/', 
    response_model=WorkspaceResponse, 
    status_code=status.HTTP_201_CREATED, 
    description='Creates a new workspace'
)
async def create_workspace(request: CreateWorkspaceRequest):
    try:
        with PostgresConnection() as conn:
            workspace = create_workspace_query(conn, request.user_id, request.name, request.description)
    except WorkspaceLimitExceeded as e:
        # Return a 400 Bad Request error if the workspace limit is exceeded.
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f'Error creating workspace: {e}')
        raise HTTPException(status_code=500, detail='Failed to create workspace')
    
    return WorkspaceResponse(**workspace)
    

@router.delete(
    '/{workspace_id}', 
    status_code=status.HTTP_204_NO_CONTENT, 
    description='Deletes a workspace'
)
async def delete_workspace(workspace_id: UUID):
    try:
        with PostgresConnection() as conn:
            deleted = delete_workspace_query(conn, workspace_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail='Workspace not found')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error deleting workspace: {e}')
        raise HTTPException(status_code=500, detail='Failed to delete workspace')


@router.post(
    "/{workspace_id}/chats",
    response_model=AddChatToWorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    description="Adds a chat to a workspace"
)
async def add_chat_to_workspace(workspace_id: UUID, request: AddChatToWorkspaceRequest):
    try:
        with PostgresConnection() as conn:
            result = add_chat_to_workspace_query(conn, workspace_id, request.conversation_id)
            
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail="Chat does not exist"
                )
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error adding chat to workspace: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to add chat to workspace"
        )
    
    return AddChatToWorkspaceResponse(**result)


@router.delete(
    "/chat/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Removes a chat from its workspace"
)
async def remove_chat_from_workspace(chat_id: UUID):
        try:
            with PostgresConnection() as conn:
                removed = remove_chat_from_workspace_query(conn, chat_id)
            if not removed:
                raise HTTPException(
                    status_code=404,
                    detail="Chat does not exist"
                )

        except HTTPException:
            raise
    
        except Exception as e:
            logger.error(f"Error removing chat from workspace: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to remove chat from workspace"
            )


@router.get(
    "/{workspace_id}/contents",
    response_model=WorkspaceContents,
    description="Retrieves complete workspace contents including chats and folders"
)
async def get_workspace_contents(workspace_id: UUID):
    try:
        with PostgresConnection() as conn:
            result = get_workspace_contents_query(conn, workspace_id)
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace not found"
                )
            
            return WorkspaceContents(**result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workspace contents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workspace contents"
        )