import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer


from app.auth.dependencies import get_current_user
from app.database.connection import PostgresConnection
from app.database.model_queries import get_all_models
from app.schemas.models import ModelInfo


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"], dependencies=[Depends(get_current_user)])


@router.get(
    "/",
    response_model=List[ModelInfo],
    status_code=status.HTTP_200_OK,
    description="List all available models",
)
def list_models():
    """List all available models."""
    try:
        with PostgresConnection() as conn:
            rows = get_all_models(conn)
    except Exception as e:
        logger.critical(f"Database error when retrieving models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve model from database"
        )

    models = [ModelInfo(**rows) for rows in rows]

    return models
