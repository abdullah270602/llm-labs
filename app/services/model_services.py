import logging
import os
from openai import OpenAI
from app.database.connection import PostgresConnection
from app.database.model_queries import get_model_name_and_service_by_id
from app.routes.constant import SYSTEM_ROLE
from app.services.constants import SERVICE_CONFIG
from app.services.prompts import SYSTEM_PROMPT


logger = logging.getLogger(__name__)


def get_client_for_service(service: str) -> OpenAI:
    try:
        config = SERVICE_CONFIG[service]
        base_url = config["base_url"]
        api_key = os.getenv(config["api_key_env_var"])
        
        if not api_key:
            raise ValueError(f"API key for service {service} not found in environment variables.")
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        return client
    except KeyError as e:
        logger.error(f"Service configuration for '{service}' is missing: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error creating client for service '{service}': {e}", exc_info=True)
        raise



def get_reply_from_model(model_id: str, chat: list[str]) -> str:
    """
    Main entrypoint to retrieve a reply from the specified model.
    """
    try:
        with PostgresConnection() as conn:
            model_data = get_model_name_and_service_by_id(conn, model_id)
            service = model_data['service']
            model_name = model_data['model_name']
            logger.info(f"Retrieved model info: model_name={model_name}, service={service}")
    except Exception as e:
        logger.error(f"Database error or model lookup failure for model_id {model_id}: {e}", exc_info=True)
        raise
    
    try:
        # Dynamically get the client based on service
        client = get_client_for_service(service)
    except Exception as e:
        logger.error(f"Failed to create client for service {service}: {e}", exc_info=True)
        raise

    try:
        # Prepend system prompt to chat sequence
        chat.insert(0, {"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT})

        response = client.chat.completions.create(
            model=model_name,
            messages=chat
        )
        # Validate response structure before accessing
        if not response.choices or not response.choices[0].message:
            raise ValueError("Incomplete response received from LLM service.")

        reply = response.choices[0].message.content
        return reply
    except Exception as e:
        logger.error(f"Error during chat completion call for model {model_name}: {e}", exc_info=True)
        raise