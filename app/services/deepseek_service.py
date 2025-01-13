import os
from openai import OpenAI

from app.services.constants import DEEPSEEK_MODEL
from app.services.prompts import SYSTEM_PROMPT


def get_reply(chat: list[str] ) -> str:

    client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

    chat.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=chat
    )

    return response.choices[0].message.content