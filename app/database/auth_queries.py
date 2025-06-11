import random
from uuid import UUID, uuid4
from psycopg2.extensions import connection as PGConnection
from psycopg2.extras import DictCursor

def get_user_by_email(conn: PGConnection, email: str) -> dict | None:
    query = "SELECT id, username, email FROM users WHERE email = %s;"
    
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        return dict(result) if result else None


def create_user(conn: PGConnection, email: str, name: str) -> dict:
    user_id = uuid4()
    
    query = """
    INSERT INTO users (id, username, email)
    VALUES (%s, %s, %s)
    RETURNING id, username, email;
    """
    
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute(query, (user_id, name, email))
        user = cursor.fetchone()

        conn.commit()

    return dict(user)
