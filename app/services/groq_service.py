import os
from groq import Groq

from app.services.constants import GROQ_MODEL
from app.services.prompts import SYSTEM_PROMPT



def get_reply(chat: list[str] ) -> str:
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"),)

   
    chat.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=chat
    )

    return response["choices"][0]["message"]["content"]