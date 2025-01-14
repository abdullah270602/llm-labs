from app.routes.constant import SYSTEM_ROLE, USER_ROLE
from app.services.model_services import get_client_for_service
from app.services.prompts import CHAT_TITLE_PROMPT


def get_chat_title(initial_message) -> str:
    """
    Generate chat title based on the initial message.
    """
    client = get_client_for_service("groq") # TODO add to constants
    chat = [
        {"role": SYSTEM_ROLE, "content": CHAT_TITLE_PROMPT},
        {"role": USER_ROLE, "content": initial_message},
    ]

    response = client.chat.completions.create(
        model= "llama-3.3-70b-versatile", # TODO add to constants
        messages= chat
    )

    title = response.choices[0].message.content.strip()
    print("🐍 File: services/generate_title.py | Line: 23 | get_chat_title ~ title",title)
    if len(title.split()) > 8:
        title = "-- LONG TITLE ERROR --"
        
    return str(title)
