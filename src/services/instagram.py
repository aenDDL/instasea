import logging
from functools import wraps
from instagrapi import Client
from instagrapi.types import DirectMessage
from instagrapi.exceptions import UnknownError, BadPassword, ChallengeRequired, LoginRequired, ClientNotFoundError, RateLimitError, TwoFactorRequired
from typing import Callable, Any, List

from src.services.authenticator import Credentials


def create_client(username: str) -> Client:
    cl = Client()
    cl.delay_range = [3, 5]
    cl.username = username
    return cl
    

services: dict[str, Callable] = {}

def register_service(name: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        services[name] = wrapper
        return wrapper

    return decorator


@register_service("get_conversation")
def get_conversation(cl: Client, thread_id: int) -> List[DirectMessage]:
    thread = cl.direct_messages(thread_id=thread_id)
    logging.debug(f"Thread's content: {thread}")    
    return thread[::-1]


@register_service("send_message")
def send_message(cl: Client, thread_id: int, text: str) -> None:
    cl.direct_send(text=text, thread_ids=[thread_id])
    logging.info(f"A message to thread with ID: {thread_id} was sent with the following content: {text} ")


@register_service("authenticate")
def authenticate(cl: Client, credentials: Credentials) -> None:
    logging.info(f"Attempt to authenticate for {credentials.username}")
    credentials.auth_method(cl, credentials)
    credentials.save_credentials()
    logging.info(f"Authentication success for {credentials.username}")


class IgClient():
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.cl = create_client(self.credentials.username)
    
    def call_api(self, service: str, *args: Any, **kwargs: Any) -> Any:
        func = services[service]
        logging.debug(f"Attempt to call a function: {func.__name__} with {args} {kwargs} arguments")
        try:
            return func(self.cl, *args, **kwargs)
        except (UnknownError, BadPassword, ChallengeRequired, LoginRequired, ClientNotFoundError, RateLimitError, TwoFactorRequired, TimeoutError) as e:
            raise RuntimeError(f"API error: {type(e).__name__}. More info: {e}")






