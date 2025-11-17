import logging
from typing import List
from dataclasses import dataclass
from instagrapi.types import DirectMessage

from src.core.config import Config
from src.services.ai import AIResponse
from src.services.validator import Message, simplify_conversation


@dataclass
class TicketsManager:
    config: Config

    def answer_message(self, thread_id: int) -> None:
        try:
            raw_thread: List[DirectMessage] = self.config.ig_client.call_api("get_conversation", thread_id)
            thread: List[Message] = simplify_conversation(raw_thread)
            ai_response: AIResponse = self.config.ai_client.call_api(thread)
            self.config.ig_client.call_api("send_message", thread_id, ai_response.message_to_user)
        except RuntimeError as e:
            logging.error(f"Error: {type(e).__name__}. More info: {e}")

    def create_ticket(self, thread_id: int) -> None:
        self.answer_message(thread_id)



