from typing import List
from fastapi import APIRouter, HTTPException
from app.database.queries import get_all_models
from app.database.connection import PostgresConnection
from app.schemas.models import ModelInfo

router = APIRouter(prefix="/models", tags=["models"])




@router.get("/", response_model=List[ModelInfo])
def list_models():
    """  List all available models. """
    with PostgresConnection() as conn:
        rows = get_all_models(conn)
        models = [ModelInfo(**rows)for rows in rows]
        print("🐍 File: routes/models.py | Line: 18 | list_models ~ models",models)
        return models