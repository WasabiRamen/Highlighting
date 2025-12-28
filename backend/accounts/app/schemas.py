from pydantic import BaseModel, model_validator, EmailStr
from typing import Optional

PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,16}$"

class CreateAccount(BaseModel):
    token: str
    user_id: str
    user_name: str
    password: str
    email: EmailStr
    phone_number: Optional[str] = None

    @model_validator(mode="before")
    def validate_password(cls, values):
        import re
        password = values.get('password')
        if password and not re.fullmatch(PASSWORD_REGEX, password):
            raise ValueError("Password must be 8-16 characters long, include at least one uppercase letter, one digit, and one special character.")
        return values

    @model_validator(mode="after")
    def validate_user_id(cls):
        if ' ' in cls.user_id:
            raise ValueError("user_id must not contain spaces.")
        if len(cls.user_id) < 4 or len(cls.user_id) > 20:
            raise ValueError("user_id must be between 4 and 20 characters long.")
        return cls


class LinkProviderRequest(BaseModel):
    code: str
    provider: str

    @model_validator(mode="after")
    def validate_provider(cls):
        allowed_providers = ["google"]
        if cls.provider not in allowed_providers:
            raise ValueError(f"Provider must be one of {allowed_providers}.")
        return cls