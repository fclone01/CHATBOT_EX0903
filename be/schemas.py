from pydantic import BaseModel
from typing import List, Optional

class MessageCreate(BaseModel):
    chat_id: str
    content: str
    role: Optional[str] = "user"

class ChatCreate    (BaseModel):
    name: str

class FileDelete(BaseModel):
    id: str
