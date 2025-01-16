import logging
from app.routes.constant import SYSTEM_ROLE, USER_ROLE
from app.services.model_services import get_client_for_service
from app.services.prompts import CHAT_TITLE_PROMPT


logger = logging.getLogger(__name__)


def get_chat_title(initial_message) -> str:
    """
    Generate chat title based on the initial message.
    """
    try:
        client = get_client_for_service("groq") # TODO add to constants
        chat = [
            {"role": SYSTEM_ROLE, "content": CHAT_TITLE_PROMPT},
            {"role": USER_ROLE, "content": initial_message},
        ]

    except Exception as e:
        logger.error(f"Error setting up client or preparing chat for title generation: {e}", exc_info=True)
        raise

    try:
        response = client.chat.completions.create(
            model= "llama-3.3-70b-versatile", # TODO add to constants
            messages= chat,
            temperature= 0.0
        )
        
    except Exception as e:
        logger.error(f"LLM call failed during title generation: {e}", exc_info=True)
        raise

    try:
        title = response.choices[0].message.content.strip()
        logger.info(f"Generated title: {title}")
        
        if len(title.split()) > 8:
            logger.warning(f"Generated title is unusually long: {title}")
            title = "-- LONG TITLE ERROR --" # TODO Handle this in a better way
        
        return str(title)
    except Exception as e:
        logger.error(f"Error processing LLM response for title: {e}", exc_info=True)
        raise
