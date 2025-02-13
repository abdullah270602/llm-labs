
from uuid import UUID
import psycopg2
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
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()
    
    
    
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
