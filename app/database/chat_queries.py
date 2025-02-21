from datetime import datetime
from typing import Any, Dict
from uuid import UUID
from psycopg2.extensions import connection as PGConnection
import psycopg2.extras


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
        chat = cursor.fetchone()
        conn.commit()
        return chat


def insert_chat_messages(conn: PGConnection, messages_data: list) -> list:
    """
    Insert multiple messages into the messages table in a single query.
    Each element in messages_data should be a tuple: (conversation_id, role, model_id, content)
    Returns a list of inserted records.
    """
    placeholders = ", ".join(["(%s, %s, %s, %s, %s)"] * len(messages_data))
    updated_at = datetime.now()
    query = f"""
    INSERT INTO messages (conversation_id, role, model_id, content, updated_at)
    VALUES {placeholders}
    RETURNING message_id, conversation_id, role, model_id, content;
    """
   
    # Add updated_at to each message's values
    flattened_values = []
    for message in messages_data:
        flattened_values.extend([*message, updated_at])  # Add updated_at to each message

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, flattened_values)
        new_messages = cursor.fetchall()
        conn.commit()
        return new_messages


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
        ORDER BY updated_at DESC
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


