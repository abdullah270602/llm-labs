from typing import Tuple
from uuid import UUID
from psycopg2.extensions import connection as PGConnection
import psycopg2.extras

from app.custom_exceptions import MovementError
from app.schemas.movements import ItemType, Location, LocationType


def get_current_location(conn: PGConnection, item_type: ItemType, item_id: UUID) -> Location:
    """
    Determines the current location of an item.
    For chats: Can be in workspace, folder, or global
    For folders: Can only be in workspace or global
    """
    if item_type == ItemType.CHAT:
        query = """
        SELECT workspace_id, folder_id
        FROM conversations
        WHERE conversation_id = %s;
        """
    else:  # FOLDER
        query = """
        SELECT workspace_id
        FROM folders
        WHERE folder_id = %s;
        """
        
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(query, (item_id,))
        result = cursor.fetchone()
        
        if not result:
            raise MovementError(f"{item_type} with id {item_id} not found")
            
        if item_type == ItemType.CHAT:
            if result['workspace_id']:
                return Location(type=LocationType.WORKSPACE, id=result['workspace_id'])
            elif result['folder_id']:
                return Location(type=LocationType.FOLDER, id=result['folder_id'])
            else:
                return Location(type=LocationType.GLOBAL)
        else:  # FOLDER
            if result['workspace_id']:
                return Location(type=LocationType.WORKSPACE, id=result['workspace_id'])
            else:
                return Location(type=LocationType.GLOBAL)


def move_item(
    conn: PGConnection, 
    item_type: ItemType,
    item_id: UUID,
    destination: Location
) -> Tuple[Location, Location]:
    """
    Moves an item to a new location.
    For chats: Can move to workspace, folder, or global
    For folders: Can only move to workspace or global
    
    Returns:
        Tuple[Location, Location]: (new_location, previous_location)
    """
    # Get current location first
    previous_location = get_current_location(conn, item_type, item_id)
    
    # Validate movement for folders
    if item_type == ItemType.FOLDER and destination.type == LocationType.FOLDER:
        raise MovementError("Folders cannot be nested inside other folders")
    
    # Prepare update values based on destination
    update_values = {
        'item_id': item_id,
        'workspace_id': None
    }
    
    if destination.type == LocationType.WORKSPACE:
        update_values['workspace_id'] = destination.id
    
    # Choose appropriate update query
    if item_type == ItemType.CHAT:
        update_values['folder_id'] = destination.id if destination.type == LocationType.FOLDER else None
        
        update_query = """
        UPDATE conversations
        SET 
            workspace_id = %(workspace_id)s,
            folder_id = %(folder_id)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE conversation_id = %(item_id)s
        RETURNING conversation_id;
        """
    else:  # FOLDER
        update_query = """
        UPDATE folders
        SET 
            workspace_id = %(workspace_id)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE folder_id = %(item_id)s
        RETURNING folder_id;
        """
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute(update_query, update_values)
        if not cursor.fetchone():
            raise MovementError(f"Failed to update {item_type}")
        conn.commit()
    
    return destination, previous_location
