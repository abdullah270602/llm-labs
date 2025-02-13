from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from psycopg2.extensions import connection as PGConnection
import psycopg2.extras

from app.custom_exceptions import WorkspaceLimitExceeded
from app.schemas.workspaces import DeletionMode


def get_user_workspace_count(conn: PGConnection, user_id: UUID) -> int:
    """
    Get the number of workspaces a user currently has.

    Args:
        conn (PGConnection): PostgreSQL database connection
        user_id (UUID): ID of the user

    Returns:
        int: Number of workspaces owned by the user
    """
    query = """
    SELECT COUNT(*)
    FROM workspaces
    WHERE user_id = %s;
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (user_id,))
        return cursor.fetchone()[0]


def create_workspace_query(
    conn: PGConnection, user_id: UUID, name: str) -> Dict[str, Any]:
    """
    Create a new workspace and return the inserted record.

    Args:
        conn (PGConnection): PostgreSQL database connection
        user_id (UUID): ID of the user creating the workspace
        name (str): Name of the workspace

    Returns:
        Dict[str, Any]: Dictionary containing the created workspace details
    """
    current_count = get_user_workspace_count(conn, user_id)
    if current_count >= 5:
        raise WorkspaceLimitExceeded()

    query = """
    INSERT INTO workspaces (
        user_id,
        name
    )
    VALUES (
        %s,
        %s
    )
    RETURNING 
        workspace_id,
        user_id,
        name,
        created_at
    """

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id, name))
        workspace = cursor.fetchone()
        conn.commit()
        return workspace


def delete_workspace_query(
    conn: PGConnection, workspace_id: UUID, mode: DeletionMode = DeletionMode.ARCHIVE
) -> bool:
    """
    Delete a workspace with specified deletion mode.

    Args:
        conn: PostgreSQL database connection
        workspace_id: ID of the workspace to delete
        mode: DeletionMode specifying how to handle workspace contents.
             Defaults to ARCHIVE which preserves contents in global space.

    Returns:
        bool: True if workspace was found and deleted
    """
    # SQL queries
    archive_contents_query = """
        UPDATE conversations 
        SET workspace_id = NULL
        WHERE workspace_id = %s
    """

    delete_contents_query = """
        DELETE FROM conversations
        WHERE workspace_id = %s
    """
    
    archive_folders_query = """
        UPDATE folders
        SET workspace_id = NULL
        WHERE workspace_id = %s
    """

    delete_folders_query = """
        DELETE FROM folders
        WHERE workspace_id = %s
    """

    delete_workspace_query = """
        DELETE FROM workspaces
        WHERE workspace_id = %s
    """

    try:
        with conn.cursor() as cursor:
            if mode == DeletionMode.ARCHIVE:
                # Move contents to global space first
                cursor.execute(archive_contents_query, (workspace_id,))
                cursor.execute(archive_folders_query, (workspace_id,))

            else:  # PERMANENT deletion
                # Delete all contents first
                cursor.execute(delete_contents_query, (workspace_id,))
                cursor.execute(delete_folders_query, (workspace_id,))


            # Then delete the workspace
            cursor.execute(delete_workspace_query, (workspace_id,))
            rows_affected = cursor.rowcount
            conn.commit()

            return rows_affected > 0

    except Exception as e:
        conn.rollback()
        raise e


def get_workspace_chats_query(
    conn: PGConnection, workspace_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Retrieves complete workspace contents including chats and folders.

    Args:
        conn (PGConnection): PostgreSQL database connection
        workspace_id (UUID): ID of the workspace

    Returns:
        Optional[Dict[str, Any]]: Complete workspace data if found, None if workspace doesn't exist
    """
    query = """
    WITH workspace_data AS (
        SELECT 
            w.workspace_id,
            w.name,
            w.created_at,
            w.updated_at
        FROM workspaces w
        WHERE w.workspace_id = %s
    ),
    workspace_chats AS (
        SELECT 
            c.conversation_id,
            c.title,
            c.created_at,
            c.updated_at
        FROM conversations c
        WHERE c.workspace_id = %s
        ORDER BY c.created_at DESC
    )
    SELECT 
        wd.*,
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'conversation_id', wc.conversation_id,
                    'title', wc.title,
                    'created_at', wc.created_at,
                    'updated_at', wc.updated_at
                )
            ) FILTER (WHERE wc.conversation_id IS NOT NULL),
            '[]'
        ) as chats
    FROM workspace_data wd
    LEFT JOIN workspace_chats wc ON true
    GROUP BY 
        wd.workspace_id,
        wd.name,
        wd.created_at,
        wd.updated_at;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(query, (workspace_id, workspace_id))
        result = cursor.fetchone()

        return result


def get_workspace_folders_query(
    conn: PGConnection, 
    workspace_id: UUID
) -> Dict[str, Any]:
    """
    Retrieves workspace information along with all its folders and their conversations.
    Returns a structured response matching the WorkspaceFoldersResponse model.
    """
    query = """
    WITH workspace_info AS (
        -- Get workspace details
        SELECT 
            w.workspace_id,
            w.name,
            w.created_at,
            w.updated_at
        FROM workspaces w
        WHERE w.workspace_id = %s
    ),
    folder_conversations AS (
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
        WHERE f.workspace_id = %s
        GROUP BY f.folder_id
    )
    SELECT 
        wi.workspace_id,
        wi.name,
        wi.created_at,
        wi.updated_at,
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'folder_id', f.folder_id,
                    'name', f.name,
                    'created_at', f.created_at,
                    'updated_at', f.updated_at,
                    'conversations', COALESCE(fc.conversations, '[]'::jsonb)
                ) ORDER BY f.created_at DESC
            ) FILTER (WHERE f.folder_id IS NOT NULL),
            '[]'::jsonb
        ) as folders
    FROM workspace_info wi
    LEFT JOIN folders f ON f.workspace_id = wi.workspace_id
    LEFT JOIN folder_conversations fc ON f.folder_id = fc.folder_id
    GROUP BY wi.workspace_id, wi.name, wi.created_at, wi.updated_at;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (workspace_id, workspace_id))
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
            
        return dict(result)


def get_user_workspaces_query(
    conn: PGConnection, user_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get all workspaces (id and title only) for a user.

    Args:
        conn (PGConnection): PostgreSQL database connection
        user_id (UUID): ID of the user

    Returns:
        List[Dict[str, Any]]: List of workspace summaries
    """
    query = """
    SELECT 
        workspace_id,
        name,
        created_at
    FROM workspaces 
    WHERE user_id = %s
    ORDER BY created_at DESC;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

