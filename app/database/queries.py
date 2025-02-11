from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from psycopg2.extensions import connection as PGConnection
import psycopg2.extras

from app.custom_exceptions import MovementError, WorkspaceLimitExceeded
from app.schemas.movements import ItemType, Location, LocationType
from app.schemas.workspaces import DeletionMode


def get_all_models(conn: PGConnection) -> list:
    """
    List all available models.
    """
    query = """
        SELECT
            model_id,
            model_name
        FROM models;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def select_chat_context_by_id(conn: PGConnection, chat_id: UUID) -> dict:
    """
    Retrieve a specific chat context by its ID.
    """
    query = """
    SELECT
        c.current_model_id,
        json_agg(
          json_build_object(
            'role', m.role,
            'content', m.content
          ) ORDER BY m.created_at, m.message_id
        ) AS messages
    FROM conversations c
    JOIN messages m ON c.conversation_id = m.conversation_id
    WHERE c.conversation_id = %s
    GROUP BY c.current_model_id;
    """
    # Use RealDictCursor for JSON output
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(query, (chat_id,))
        records = cursor.fetchone()
        return records


def select_chat_by_id(conn: PGConnection, chat_id: UUID) -> dict:
    """
    Retrieve a specific chat by its ID.
    """
    query = """
    SELECT
        c.current_model_id,
        c.conversation_id,
        c.created_at,
        c.updated_at,
        json_agg(
          json_build_object(
            'role', m.role,
            'model_id', m.model_id,
            'content', m.content
          ) ORDER BY m.created_at, m.message_id
        ) AS messages
    FROM conversations c
    JOIN messages m ON c.conversation_id = m.conversation_id
    WHERE c.conversation_id = %s
    GROUP BY c.current_model_id, c.conversation_id, c.created_at, c.updated_at;
    """
    # Use RealDictCursor for JSON output
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(query, (chat_id,))
        records = cursor.fetchone()
        return records


def select_user_chat_titles(
    conn: PGConnection, user_id: int, limit: int, offset
) -> list:  # NOt being used
    """
    List all chat IDs and titles for a given user.
    """
    query = """
        SELECT conversation_id, title
        FROM conversations
        WHERE user_id = %s AND workspace_id IS NULL AND folder_id IS NULL
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s;
        """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id, limit, offset))
        return cursor.fetchall()


def insert_chat(
    conn: PGConnection,
    user_id: UUID,
    current_model_id: UUID,
    title: str,
    workspace_id: UUID = None,
    folder_id: UUID = None,
) -> dict:
    """
    Create a new chat and return the inserted record.
    """
    query = """
    INSERT INTO conversations (user_id, current_model_id, title, workspace_id, folder_id)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING conversation_id, current_model_id, title, workspace_id, folder_id;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id, current_model_id, title, workspace_id, folder_id))
        chat_id = cursor.fetchone()
        conn.commit()
        return chat_id


def insert_chat_messages(conn: PGConnection, messages_data: list) -> list:
    """
    Insert multiple messages into the messages table in a single query.
    Each element in messages_data should be a tuple: (conversation_id, role, model_id, content)
    Returns a list of inserted records.
    """
    placeholders = ", ".join(["(%s, %s, %s, %s)"] * len(messages_data))
    query = f"""
    INSERT INTO messages (conversation_id, role, model_id, content)
    VALUES {placeholders}
    RETURNING message_id, conversation_id, role, model_id, content;
    """
    # Flatten the list of tuples into a single list of values for the SQL query
    flattened_values = [value for message in messages_data for value in message]

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, flattened_values)
        new_messages = cursor.fetchall()
        conn.commit()
        return new_messages


def get_model_name_and_service_by_id(conn: PGConnection, model_id: UUID) -> str:
    """
    Retrieve the model name by its ID.
    """
    query = """
    SELECT model_name, service
    FROM models
    WHERE model_id = %s;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (model_id,))
        result = cursor.fetchone()
        return result


def update_chat_title_query(conn: PGConnection, chat_id: UUID, new_title: str) -> dict:
    """
    Update the title of a chat conversation by its ID.
    Returns the updated record with conversation_id, model_id, userid, and new title.
    """
    query = """
    UPDATE conversations
    SET title = %s
    WHERE conversation_id = %s
    RETURNING conversation_id, title;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (new_title, chat_id))
        updated_record = cursor.fetchone()
        conn.commit()
        return updated_record


def delete_chat_query(conn: PGConnection, chat_id: UUID) -> None:
    """
    Delete a chat conversation by its ID.
    """
    query = """
    DELETE FROM conversations
    WHERE conversation_id = %s
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (chat_id,))
        conn.commit()
        # Check how many rows were affected
        return cursor.rowcount > 0


def update_conversation_model(
    conn: PGConnection, chat_id: UUID, model_id: UUID
) -> dict:
    """
    Update the current model for a chat conversation.
    """
    query = """
    UPDATE conversations
    SET current_model_id = %s
    WHERE conversation_id = %s
    RETURNING conversation_id, current_model_id;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (model_id, chat_id))
        updated_record = cursor.fetchone()
        conn.commit()
        return updated_record


def select_user_chat_titles_and_count_single_row(
    conn: PGConnection, user_id: int, limit: int, offset: int
) -> Dict[str, Any]:
    """
    Returns one dictionary with:
      {
        "total_count": <int>,
        "conversations": [
            { "conversation_id": <uuid>, "title": <str> },
            ...
        ]
      }
    """
    query = """
    WITH total AS (
        SELECT COUNT(*)::int AS total_count
        FROM conversations
        WHERE user_id = %s AND workspace_id IS NULL AND folder_id IS NULL
    ),
    paged AS (
        SELECT
            conversation_id,
            title
        FROM conversations
        WHERE user_id = %s AND workspace_id IS NULL AND folder_id IS NULL
        ORDER BY created_at DESC
        LIMIT %s
        OFFSET %s
    )
    SELECT
        total.total_count,
        COALESCE(
            JSON_AGG(
                JSON_BUILD_OBJECT(
                    'conversation_id', paged.conversation_id,
                    'title', paged.title
                )
                ORDER BY paged.conversation_id
            ), '[]'::json
        ) AS conversations
    FROM total
    CROSS JOIN paged
    GROUP BY total.total_count;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(query, (user_id, user_id, limit, offset))
        row = (
            cursor.fetchone()
        )  # Could be None if user has zero conversations or offset out of range

        if not row:
            # If there are no rows, user might have zero conversations
            # or the offset is out of range. We'll handle that gracefully.
            return {"total_count": 0, "conversations": []}

        return {
            "total_count": row["total_count"],
            # row["conversations"] is a JSON array => RealDictCursor returns it as a Python list
            "conversations": row["conversations"] or [],
        }


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
    conn: PGConnection, user_id: UUID, name: str, description: str = None
) -> Dict[str, Any]:
    """
    Create a new workspace and return the inserted record.

    Args:
        conn (PGConnection): PostgreSQL database connection
        user_id (UUID): ID of the user creating the workspace
        name (str): Name of the workspace
        description (str, optional): Description of the workspace

    Returns:
        Dict[str, Any]: Dictionary containing the created workspace details
    """
    current_count = get_user_workspace_count(conn, user_id)
    if current_count >= 5:
        raise WorkspaceLimitExceeded()

    query = """
    INSERT INTO workspaces (
        user_id,
        name,
        description
    )
    VALUES (
        %s,
        %s,
        %s
    )
    RETURNING 
        workspace_id,
        user_id,
        name,
        description,
        created_at
    """

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id, name, description))
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

    delete_workspace_query = """
        DELETE FROM workspaces
        WHERE workspace_id = %s
    """

    try:
        with conn.cursor() as cursor:
            if mode == DeletionMode.ARCHIVE:
                # Move contents to global space first
                cursor.execute(archive_contents_query, (workspace_id,))
            else:  # PERMANENT deletion
                # Delete all contents first
                cursor.execute(delete_contents_query, (workspace_id,))

            # Then delete the workspace
            cursor.execute(delete_workspace_query, (workspace_id,))
            rows_affected = cursor.rowcount
            conn.commit()

            return rows_affected > 0

    except Exception as e:
        conn.rollback()
        raise e


def get_workspace_contents_query(
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
            w.description,
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
            c.updated_at,
            c.current_model_id
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
                    'updated_at', wc.updated_at,
                    'current_model_id', wc.current_model_id
                )
            ) FILTER (WHERE wc.conversation_id IS NOT NULL),
            '[]'
        ) as chats
    FROM workspace_data wd
    LEFT JOIN workspace_chats wc ON true
    GROUP BY 
        wd.workspace_id,
        wd.name,
        wd.description,
        wd.created_at,
        wd.updated_at;
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(query, (workspace_id, workspace_id))
        result = cursor.fetchone()

        if result:
            # Add empty folders list for now
            result["folders"] = []

        return result


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


def get_current_location(conn: PGConnection, item_type: ItemType, item_id: UUID) -> Location:
    """
    Determines the current location of an item.
    For chats: Can be in workspace, folder, or global
    For folders: Can only be in workspace or global
    """
    if item_type == ItemType.CHAT:
        query = """
        SELECT workspace_id, folder_id
        FROM conversations
        WHERE conversation_id = %s;
        """
    else:  # FOLDER
        query = """
        SELECT workspace_id
        FROM folders
        WHERE folder_id = %s;
        """
        
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (item_id,))
        result = cursor.fetchone()
        
        if not result:
            raise MovementError(f"{item_type} with id {item_id} not found")
            
        if item_type == ItemType.CHAT:
            if result['workspace_id']:
                return Location(type=LocationType.WORKSPACE, id=result['workspace_id'])
            elif result['folder_id']:
                return Location(type=LocationType.FOLDER, id=result['folder_id'])
            else:
                return Location(type=LocationType.GLOBAL)
        else:  # FOLDER
            if result['workspace_id']:
                return Location(type=LocationType.WORKSPACE, id=result['workspace_id'])
            else:
                return Location(type=LocationType.GLOBAL)


def move_item(
    conn: PGConnection, 
    item_type: ItemType,
    item_id: UUID,
    destination: Location
) -> Tuple[Location, Location]:
    """
    Moves an item to a new location.
    For chats: Can move to workspace, folder, or global
    For folders: Can only move to workspace or global
    
    Returns:
        Tuple[Location, Location]: (new_location, previous_location)
    """
    # Get current location first
    previous_location = get_current_location(conn, item_type, item_id)
    
    # Validate movement for folders
    if item_type == ItemType.FOLDER and destination.type == LocationType.FOLDER:
        raise MovementError("Folders cannot be nested inside other folders")
    
    # Prepare update values based on destination
    update_values = {
        'item_id': item_id,
        'workspace_id': None
    }
    
    if destination.type == LocationType.WORKSPACE:
        update_values['workspace_id'] = destination.id
    
    # Choose appropriate update query
    if item_type == ItemType.CHAT:
        update_values['folder_id'] = destination.id if destination.type == LocationType.FOLDER else None
        
        update_query = """
        UPDATE conversations
        SET 
            workspace_id = %(workspace_id)s,
            folder_id = %(folder_id)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE conversation_id = %(item_id)s
        RETURNING conversation_id;
        """
    else:  # FOLDER
        update_query = """
        UPDATE folders
        SET 
            workspace_id = %(workspace_id)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE folder_id = %(item_id)s
        RETURNING folder_id;
        """
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(update_query, update_values)
        if not cursor.fetchone():
            raise MovementError(f"Failed to update {item_type}")
        conn.commit()
    
    return destination, previous_location
