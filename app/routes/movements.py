import logging
from fastapi import APIRouter, HTTPException, status
from app.custom_exceptions import MovementError
from app.database.connection import PostgresConnection
from app.database.queries import move_item
from app.schemas.movements import MoveRequest, MoveResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/move", tags=["movement"])

@router.post(
    "/",
    response_model=MoveResponse,
    description="Move an item (chat or folder) to a new location",
    status_code=status.HTTP_201_CREATED,
)
async def move_item_route(request: MoveRequest):
    """
    Handles the movement of items (chats or folders) between different locations.
    This endpoint orchestrates the movement process by:
    1. Validating the request
    2. Moving the item to its new location
    3. Returning the previous and new locations
    """
    try:
        # Establish database connection using context manager
        with PostgresConnection() as conn:
            # The move_item function will handle getting the current location
            # and performing the move in a single operation
            new_location, previous_location = move_item(
                conn=conn,
                item_type=request.item_type,
                item_id=request.item_id,
                destination=request.destination
            )
            
            # Return the response with movement details
            return MoveResponse(
                item_type=request.item_type,
                item_id=request.item_id,
                previous_location=previous_location,
                new_location=new_location
            )
            
    except MovementError as e:
        # Handle specific movement-related errors (like item not found or invalid moves)
        logger.warning(f"Movement error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during movement operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while moving the item"
        )