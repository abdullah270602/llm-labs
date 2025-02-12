from fastapi import HTTPException, status
import psycopg2
from psycopg2.extensions import connection as PGConnection
from typing import Any, Dict, List, Optional
from uuid import UUID
from app.schemas.folders import FolderInfo
from app.schemas.movements import LocationType
from app.schemas.workspaces import DeletionMode


def create_folder_query(
    conn: PGConnection,
    name: str,
    user_id: UUID,
    location_type: LocationType,
    workspace_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Creates a new folder in either a workspace or global space.

    Args:
        conn: Database connection
        name: Name of the folder
        user_id: UUID of the user creating the folder
        location_type: LocationType enum (GLOBAL or WORKSPACE)
        workspace_id: UUID of workspace if location_type is WORKSPACE, None for GLOBAL

    Returns:
        Dict containing the created folder's information
    """

    # If creating in workspace, validate workspace exists and user has access
    if location_type == LocationType.WORKSPACE and workspace_id:
        workspace_access_query = """
        SELECT EXISTS(
            SELECT 1 
            FROM workspaces 
            WHERE workspace_id = %s AND user_id = %s
        )
        """
        with conn.cursor() as cur:
            cur.execute(workspace_access_query, (workspace_id, user_id))
            if not cur.fetchone()[0]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace not found for the user",
                )

    # Create folder query
    query = """
    INSERT INTO folders (
        name,
        user_id,
        workspace_id,
        created_at,
        updated_at
    )
    VALUES (
        %s,
        %s,
        %s,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    RETURNING 
        folder_id,
        name,
        user_id,
        workspace_id,
        created_at,
        updated_at
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            query, (name, user_id, workspace_id)  # Will be NULL for global folders
        )
        conn.commit()
        folder = cur.fetchone()

        return dict(folder)



def delete_folder_query(
    conn: PGConnection,
    folder_id: UUID,
    mode: DeletionMode
) -> None:
    """
    Deletes a folder using the specified deletion mode.
    
    Args:
        conn: Database connection
        folder_id: UUID of the folder to delete
        user_id: UUID of the user requesting deletion
        mode: DeletionMode.ARCHIVE (move contents to global) or DeletionMode.PERMANENT (delete all)
    """
    
    VERIFY_FOLDER_ACCESS = """
    SELECT EXISTS(
        SELECT 1 
        FROM folders 
        WHERE folder_id = %s
    )
    """
    
    ARCHIVE_CONVERSATIONS = """
    UPDATE conversations 
    SET folder_id = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE folder_id = %s
    """
    
    DELETE_CONVERSATIONS = """
    DELETE FROM conversations 
    WHERE folder_id = %s
    """
    
    DELETE_FOLDER = """
    DELETE FROM folders 
    WHERE folder_id = %s
    """
    
    # First verify folder exists and belongs to user
    with conn.cursor() as cur:
        cur.execute(VERIFY_FOLDER_ACCESS, (folder_id,))
        if not cur.fetchone()[0]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
    
    if mode == DeletionMode.ARCHIVE:
        with conn.cursor() as cur:
            # Move conversations to global space
            cur.execute(ARCHIVE_CONVERSATIONS, (folder_id,))
            # Delete the folder
            cur.execute(DELETE_FOLDER, (folder_id,))
            
    else:  # PERMANENT deletion
        with conn.cursor() as cur:
            # Delete all conversations in the folder
            cur.execute(DELETE_CONVERSATIONS, (folder_id,))
            # Delete the folder
            cur.execute(DELETE_FOLDER, (folder_id,))
    
    conn.commit()
    
    
def get_user_global_folders_query(
    conn: PGConnection,
    user_id: UUID
) -> List[Dict[str, Any]]:
    """
    Retrieves all personal folders (not associated with any workspace) 
    belonging to a specific user, along with their conversations.
    
    Args:
        conn: Database connection
        user_id: UUID of the user whose folders to retrieve
        
    Returns:
        List of folder objects with their associated conversations
    """
    query = """
    WITH folder_conversations AS (
        -- Aggregate conversations for each folder
        SELECT 
            f.folder_id,
            COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'conversation_id', c.conversation_id,
                        'title', c.title,
                        'created_at', c.created_at,
                        'updated_at', c.updated_at
                    ) ORDER BY c.updated_at DESC
                ) FILTER (WHERE c.conversation_id IS NOT NULL),
                '[]'::jsonb
            ) as conversations
        FROM folders f
        LEFT JOIN conversations c ON c.folder_id = f.folder_id
        WHERE f.user_id = %s 
        AND f.workspace_id IS NULL
        GROUP BY f.folder_id
    )
    SELECT 
        f.folder_id,
        f.name,
        f.created_at,
        f.updated_at,
        f.user_id,
        COALESCE(fc.conversations, '[]'::jsonb) as conversations
    FROM folders f
    LEFT JOIN folder_conversations fc ON f.folder_id = fc.folder_id
    WHERE f.user_id = %s
    AND f.workspace_id IS NULL
    ORDER BY f.created_at DESC;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (user_id, user_id))
        results = cur.fetchall()
        
        return [FolderInfo(**row) for row in results]