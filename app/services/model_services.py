

from app.database.queries import get_model_name_by_id
from app.services import deepseek_services, groq_service, openai_service


def get_reply_from_model(model_id: str, chat: list[str] | None) -> str:
    """
    Main entrypoint to retrieve a reply from the specified model.
    """
    model_name = get_model_name_by_id(model_id)
    
    if model_name.startswith("openai"):
        return openai_service.get_reply(chat)
    elif model_name.startswith("groq"):
        return groq_service.get_reply(chat)
    elif model_name.startswith("deepseek"):
        return deepseek_services.get_reply(chat)
    else:
        raise ValueError(f"Unsupported Model: {model_name}")
