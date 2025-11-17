import pyotp
import json
from functools import wraps
from instagrapi import Client
from typing import Callable, Optional, Any
from pydantic import BaseModel, model_validator

from src.core.paths import credentials_file


class Credentials(BaseModel):
    username: str
    password: str
    twofa: Optional[str] = None
    session: Optional[dict] = None
    auth_method: Optional[Callable] = None

    @model_validator(mode='after')
    def create_auth_method(self) -> Callable:  
        if self.session:
            self.auth_method = auth_methods["session"]
        elif self.twofa:
            self.auth_method = auth_methods["twofa"]
        else:
            self.auth_method = auth_methods["standard"]
        return self

    def save_credentials(self) -> None:
        data = self.model_dump(exclude={'auth_method'})
        with credentials_file.open(mode="w") as f:
            f.write(json.dumps(data, indent=4))


def create_session(cl: Client, credentials: Credentials) -> Credentials:
    credentials.session = cl.get_settings()
    return credentials


auth_methods: dict[str, Callable] = {}


def register_auth_method(name: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        auth_methods[name] = wrapper
        return wrapper

    return decorator


@register_auth_method("session")
def auth_with_session(cl: Client, credentials: Credentials) -> Credentials:
    cl.set_settings(credentials.session)
    cl.get_timeline_feed()
    return credentials


@register_auth_method("twofa")
def auth_with_twofa(cl: Client, credentials: Credentials) -> Credentials:
    code = pyotp.TOTP(credentials.twofa).now()
    cl.login(credentials.username, credentials.password, verification_code=code)
    return create_session(cl, credentials)


@register_auth_method("standard")
def auth_without_twofa(cl: Client, credentials: Credentials) -> Credentials:
    cl.login(credentials.username, credentials.password)
    return create_session(cl, credentials)


