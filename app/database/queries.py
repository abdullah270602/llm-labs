from psycopg2.extensions import connection as PGConnection

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


def get_chat_by_id(conn: PGConnection, chat_id: int) -> dict:
    """
    Retrieve a specific chat by its ID.
    """
    query = """"""
    with conn.cursor() as cursor:
        cursor.execute(query, (chat_id,))
        record = cursor.fetchone()
        return record  # handle None or transform to a dict


def get_user_chat_titles(conn: PGConnection, user_id: int) -> list:
    """
    List all chat IDs and titles for a given user.
    """
    query = """"""
    with conn.cursor() as cursor:
        cursor.execute(query, (user_id,))
        return cursor.fetchall()


def create_chat(conn: PGConnection, user_id: int, title: str) -> dict:
    """
    Create a new chat and return the inserted record.
    """
    query = """"""
    with conn.cursor() as cursor:
        cursor.execute(query, (user_id, title))
        new_chat = cursor.fetchone()
        conn.commit()
        return new_chat


def create_chat_message(conn: PGConnection, chat_id: int, content: str) -> dict:
    """
    Create a new message in a given chat, returning the inserted record.
    """
    query = """"""
    with conn.cursor() as cursor:
        cursor.execute(query, (chat_id, content))
        new_message = cursor.fetchone()
        conn.commit()
        return new_message
