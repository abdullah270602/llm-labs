import os
from openai import OpenAI

from app.services.constants import OPENAI_MODEL
from app.services.prompts import SYSTEM_PROMPT


def get_reply(chat: list[str] ) -> str:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    chat.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=chat
    )

    return response.choices[0].message.content