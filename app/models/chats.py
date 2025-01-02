from uuid import UUID
from pydantic import BaseModel
from typing import List
from datetime import datetime
from typing import Optional

class Message(BaseModel):
    user_prompt: str


class ChatCreateRequest(BaseModel):
    user_id: UUID
    bot_name: str
    message: Message 



class MessageCreateRequest(BaseModel):
    chat_id: UUID  # Required for adding a message to an existing chat
    bot_name: str
    message: Message



class MessageResponse(BaseModel):
    user_prompt: str
    bot_response: str


class ChatCreateResponse(BaseModel):
    user_id: UUID
    chat_id: UUID
    message: MessageResponse  # The first message with bot response


class MessageAddResponse(BaseModel):
    chat_id: UUID
    message: MessageResponse  # The newly added message with bot response