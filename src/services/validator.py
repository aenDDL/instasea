import logging
from pydantic import BaseModel, Field, ValidationError, ConfigDict, field_validator
from typing import Literal, List
from instagrapi.types import DirectMessage


class Notification(BaseModel):
    model_config = ConfigDict(
        extra='ignore',
        populate_by_name=True  
    )
    text: str = Field(..., alias="message")
    type: Literal["direct_v2_pending", "direct_v2_text"] = Field(..., alias="pushCategory")
    ids: dict = Field(..., alias="actionParams")


class Message(BaseModel):
    model_config = ConfigDict(
        extra='ignore',
        populate_by_name=True  
    )
    
    username: str | None = None
    thread_id: int
    text: str
    sender: Literal["AI", "user"] | bool = Field(..., alias="is_sent_by_viewer")

    @field_validator("thread_id", mode="before")
    @classmethod
    def coerce_thread_id(cls, v):
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            return int(v)
        
    @field_validator("sender")
    @classmethod
    def set_sender(cls, v: bool | str) -> Literal["AI", "user"]:
        if isinstance(v, bool):
            return "AI" if v else "user"
        if isinstance(v, str) and v in ("AI", "user"):
            return v
        v_str = str(v).lower()
        return "AI" if v_str in ("1", "true", "yes", "ai") else "user"


def safe_validate(msg):
        try:
            return Message.model_validate(msg.model_dump())
        except ValidationError as e:
            logging.warning(f"Message validation error: {e}")
            return None


def simplify_conversation(thread: List[DirectMessage]) -> List[Message]:
    validated_messages = [safe_validate(message) for message in thread]
    conversation = [msg for msg in validated_messages if msg is not None]
    if len(conversation) == 0:
        raise RuntimeError("No valid messages in the conversation.")
    logging.debug(f"Conversation after simplifying: {conversation}")
    return conversation


def validate_notification(raw_notification: dict) -> Notification | dict:
    try:
        notification_model = Notification(**raw_notification)
        return notification_model
    except ValidationError as e:
        logging.warning(f"Unsupported type of notification. More info: {e}")
        raise RuntimeError(f"Notification validation failed: {e}") from e


def extract_message(notification_model: Notification) -> dict:
    username, *text = notification_model.text.split(":")
    cleaned_text = ":".join(t.lstrip() for t in text)
    raw_message = {
        "username": username,
        "thread_id": notification_model.ids.get("id"),
        "text": cleaned_text,
        "is_sent_by_viewer": False
    }
    logging.info(f"New message from {username}: {cleaned_text}")
    logging.debug(f"Full info: {raw_message}")
    return raw_message


def validate_message(raw_message: dict) -> Message | dict:
    try:
        message_model = Message(**raw_message)
        return message_model
    except ValidationError as e:
        logging.error(f"Message validation error: {e}")
        raise RuntimeError(f"Message validation failed: {e}") from e
    

def create_message_model(raw_notification: dict) -> Message | bool:
    try:
        notification_model = Notification(**raw_notification)
        raw_message = extract_message(notification_model)
        message_model = validate_message(raw_message)
        return message_model
    except RuntimeError:
        return False

