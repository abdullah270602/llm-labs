from typing import List
from fastapi import APIRouter, HTTPException
from app.database import queries
from app.database.connection import PostgresConnection
from app.schemas.models import ModelInfo

router = APIRouter(prefix="/models", tags=["models"])




@router.get("/", response_model=List[ModelInfo])
def list_models():
    """  List all available models. """
    with PostgresConnection() as conn:
        rows = queries.get_all_models(conn)  # Each row is (id, model_name)
        print(rows)
        # Convert tuples to ModelInfo objects
        models = [ModelInfo(model_id=row[0], model_name=row[1]) for row in rows]
        return models