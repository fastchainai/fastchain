"""Data models for Auth0 integration."""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """Model representing the decoded JWT payload."""
    sub: str = Field(..., description="Subject identifier")
    iss: str = Field(..., description="Token issuer")
    aud: list[str] | str = Field(..., description="Token audience")
    exp: int = Field(..., description="Expiration time")
    iat: int = Field(..., description="Issued at time")
    scope: str | None = Field(default=None, description="Token scopes")
    permissions: list[str] | None = Field(default=None, description="User permissions")


class Auth0User(BaseModel):
    """Model representing an authenticated Auth0 user."""
    sub: str = Field(..., description="User identifier")
    permissions: list[str] = Field(default_factory=list, description="User permissions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional user metadata")
    token: Optional[str] = Field(default=None, description="Raw JWT token")
