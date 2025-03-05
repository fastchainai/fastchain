"""Configuration module for Auth0 integration."""
from pydantic import BaseModel, Field


class Auth0Config(BaseModel):
    """Auth0 configuration settings."""
    domain: str = Field(..., description="Auth0 domain (e.g., 'your-tenant.auth0.com')")
    api_audience: str = Field(..., description="API audience identifier")
    algorithms: list[str] = Field(default=["RS256"], description="Token signing algorithms")
    issuer: str | None = Field(default=None, description="Token issuer")
    
    def get_jwks_url(self) -> str:
        """Get the JWKS URL for the Auth0 domain."""
        return f"https://{self.domain}/.well-known/jwks.json"
    
    def get_issuer(self) -> str:
        """Get the token issuer URL."""
        return self.issuer or f"https://{self.domain}/"
