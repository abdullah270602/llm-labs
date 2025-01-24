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


def select_user_chat_titles(conn: PGConnection, user_id: int, limit: int, offset) -> list:
    """
    List all chat IDs and titles for a given user.
    """
    query = """
        SELECT conversation_id, title
        FROM conversations
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s;
        """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id, limit, offset))
        return cursor.fetchall()


def insert_chat(conn: PGConnection, user_id: UUID, current_model_id: UUID, title: str) -> dict:
    """
    Create a new chat and return the inserted record.
    """
    query = """
    INSERT INTO conversations (user_id, current_model_id, title)
    VALUES (%s, %s, %s)
    RETURNING conversation_id, current_model_id, title;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (user_id, current_model_id, title))
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
    RETURNING conversation_id, model_id, userid, title;
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


def update_conversation_model(conn: PGConnection, chat_id: UUID, model_id: UUID) -> dict:
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