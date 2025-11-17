import logging
from xai_sdk import Client
from xai_sdk.chat import system, user, assistant
from typing import List, Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict
from grpc import RpcError

from src.services.validator import Message


class AIResponse(BaseModel):
    message_to_user: str
    user_status: Literal["follow-up", "ignore"] = Field(default="follow-up")


class AIClient(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    cl: Client | None = None
    xai_key: str
    instructions: str

    @model_validator(mode='after')
    def init_client(self):
        self.cl = Client(api_key=self.xai_key)  
        return self
    
    def call_api(self, conversation: List[Message]) -> AIResponse | dict:
        try:
            chat = self.cl.chat.create(model="grok-4-fast-reasoning")

            chat.append(system(self.instructions))
            for message in conversation:
                if message.sender == "user":
                    chat.append(user(message.text))
                elif message.sender == "ai":
                    chat.append(assistant(message.text))

            _, answer = chat.parse(AIResponse)
            assert isinstance(answer, AIResponse)
            logging.debug(f"AI answer: {answer}")
            return answer
        except (RpcError, AssertionError) as e:
            raise RuntimeError(f"AI service error: {e}") 

