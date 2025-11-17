import os
import json
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from src.core.paths import ai_instructions_file, credentials_file
from src.services.instagram import IgClient, Credentials
from src.services.ai import AIClient


load_dotenv()


def load_ai_instructions() -> str:
    with ai_instructions_file.open(mode="r") as f:
        return f.read()


def load_credentials() -> Credentials:
    with credentials_file.open(mode="r") as f:
        return Credentials(**json.loads(f.read()))
    
    
def load_ai_client() -> AIClient:
    return AIClient(
        xai_key=os.getenv("xai_key"),
        instructions=load_ai_instructions(),
    )


def load_ig_client() -> IgClient:
    return IgClient(load_credentials())


class Config(BaseSettings): 
    ai_client: AIClient = load_ai_client()
    ig_client: IgClient = load_ig_client()


def load_config() -> Config:
    return Config()

