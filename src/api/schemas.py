from typing import Annotated
import bleach
from pydantic import BaseModel, BeforeValidator

def sanitize_string(value: str) -> str:
    """
    Strips all HTML tags from a string, preventing XSS attacks.
    """
    if isinstance(value, str):
        return bleach.clean(value, tags=[], strip=True)
    return value

# Define a reusable Pydantic type for sanitized strings
SanitizedString = Annotated[str, BeforeValidator(sanitize_string)]

# Base model that can be inherited from for common configuration
class AppBaseModel(BaseModel):
    class Config:
        from_attributes = True
