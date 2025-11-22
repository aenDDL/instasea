import logging
from dataclasses import dataclass
from instagrapi.types import DirectMessage
from pydantic import ValidationError, TypeAdapter
from src.core.config import Config
from src.services.ai import AIResponse
from src.core.types import FastAPIMessage, Message


def transform_conversation(conversation: list[DirectMessage]) -> list[Message]:
    adapter = TypeAdapter(Message)  
    transformed = []
    
    for message in conversation:
        try:
            transformed.append(adapter.validate_python(message.model_dump()))
        except ValidationError as e:
            logging.warning(f"Skipping unsupported message format: {e}")
        logging.info(transformed)
    
    if not transformed:
        raise RuntimeError("No valid messages in thread.")
    
    return transformed

        
@dataclass
class TicketsManager:
    config: Config

    def answer_message(self, message: FastAPIMessage) -> None:
        try:
            raw_thread: list[DirectMessage] = self.config.ig_client.call_api("get_conversation", message.thread_id)
            thread: list[Message] = transform_conversation(raw_thread)
            ai_response: AIResponse = self.config.ai_client.call_api(thread)
            self.config.ig_client.call_api("send_message", message.thread_id, ai_response.message_to_user)
        except RuntimeError as e:
            logging.error(f"Error: {type(e).__name__}. More info: {e}")

    def create_ticket(self, message: FastAPIMessage) -> None:
        self.answer_message(message)



