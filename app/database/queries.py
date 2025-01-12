from uuid import UUID
from psycopg2.extensions import connection as PGConnection
import psycopg2.extras


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
    with conn.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def select_chat_context_by_id(conn: PGConnection, chat_id: UUID) -> dict:
    """
    Retrieve a specific chat context by its ID.
    """
    query = """
    SELECT
        c.model_id,
        json_agg(
          json_build_object(
            'sender_role', m.sender_role,
            'content', m.content,
          ) ORDER BY m.created_at, m.message_id
        ) AS messages
    FROM conversations c
    JOIN messages m ON c.conversation_id = m.conversation_id
    WHERE c.conversation_id = %s
    GROUP BY c.model_id;
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
        c.model_id,
        c.conversation_id,
        c.created_at,
        c.updated_at,
        json_agg(
          json_build_object(
            'sender_role', m.sender_role,
            'content', m.content
          ) ORDER BY m.created_at, m.message_id
        ) AS messages
    FROM conversations c
    JOIN messages m ON c.conversation_id = m.conversation_id
    WHERE c.conversation_id = %s
    GROUP BY c.model_id, c.conversation_id, c.created_at, c.updated_at;
    """
    # Use RealDictCursor for JSON output
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:  
        cursor.execute(query, (chat_id,))
        records = cursor.fetchone()
        return records


def select_user_chat_titles(conn: PGConnection, user_id: int, limit: int, offset) -> list:
    """
    List all chat IDs and titles for a given user.
    """
    query = """
        SELECT conversation_id, title
        FROM conversations
        WHERE userid = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s;
        """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id, limit, offset))
        return cursor.fetchall()


def insert_chat(conn: PGConnection, user_id: UUID, model_id: UUID, title: str) -> dict:
    """
    Create a new chat and return the inserted record.
    """
    query = """
    INSERT INTO conversations (userid, model_id, title)
    VALUES (%s, %s, %s)
    RETURNING conversation_id, model_id, title;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id, model_id, title))
        chat_id = cursor.fetchone()
        conn.commit()
        return chat_id


def insert_chat_message(conn: PGConnection, chat_id: int, sender_role: str,  content: str) -> dict:
    """
    Create a new message in a given chat, returning the inserted record.
    """
    query = """
    INSERT INTO messages (conversation_id, sender_role, content)
    VALUES ( %s, %s, %s)
    RETURNING message_id, conversation_id, sender_role, content;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (chat_id, sender_role, content))
        new_message = cursor.fetchone()
        conn.commit()
        return new_message
