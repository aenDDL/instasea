from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from typing import Literal



class Message(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    text: str
    sender: Literal["AI", "user"] | bool = Field(..., alias='is_sent_by_viewer')

    @field_validator('sender', mode='before')
    def set_sender(cls, v: bool | str) -> str:
        if isinstance(v, bool):
            return "AI" if v else "user"
        return v


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    username: str
    user_id: int
    thread_id: int
    conversation: list[Message] = Field(..., alias='text', default_factory=[])

    @model_validator(mode='before')
    @classmethod
    def set_conversation(cls, v: dict) -> dict:
        if all([v["sender"], v["text"]]):
            v["text"] = [Message(**v)]
        return v


class FastAPIMessage(BaseModel):
    type: Literal["direct_v2_pending", "direct_v2_text"] = Field(..., alias="pushCategory")
    text: str = Field(..., alias="message")
    username: str = Field(..., min_length=3, max_length=30)
    thread_id: int
    user_id: int = Field(..., alias="sourceUserId")
    sender: str = "user"
    
    @model_validator(mode='before')
    @classmethod
    def extract_values(cls, v: dict) -> dict:
        content: str = v.get("message")
        username, message = content.split(":", 1)  
        v["username"] = username.strip()         
        v["message"] = message.lstrip()     
        if not all([v["username"], v["message"]]):
            raise ValueError("Username or message is missing.")
        
        params: dict = v.get("actionParams")
        v["thread_id"] = params.get("id")
        if not v["thread_id"]:
            raise ValueError("Thread ID value is missing.")

        return v

