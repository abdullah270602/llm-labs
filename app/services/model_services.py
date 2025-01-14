import os
from openai import OpenAI
from app.database.connection import PostgresConnection
from app.database.queries import get_model_name_and_service_by_id
from app.routes.constant import SYSTEM_ROLE
from app.services.constants import SERVICE_CONFIG
from app.services.prompts import SYSTEM_PROMPT



def get_client_for_service(service: str) -> OpenAI:
    config = SERVICE_CONFIG[service]
    base_url = config["base_url"]
    api_key = os.getenv(config["api_key_env_var"])  
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    return client


def get_reply_from_model(model_id: str, chat: list[str]) -> str:
    """
    Main entrypoint to retrieve a reply from the specified model.
    """
    
    with PostgresConnection() as conn:
        model_data = get_model_name_and_service_by_id(conn, model_id)
        service = model_data['service']
        model_name = model_data['model_name']
        print("🐍 File: services/model_services.py | Line: 32 | get_reply_from_model ~ model_name",model_name)
    
    # Dynamically get the client based on service
    client = get_client_for_service(service)

    chat.insert(0, {"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT})

    response = client.chat.completions.create(
        model=model_name,
        messages=chat
    )

    return response.choices[0].message.content