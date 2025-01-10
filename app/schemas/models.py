from uuid import UUID
from pydantic import BaseModel


class ModelInfo(BaseModel):
    model_id: UUID
    model_name: str