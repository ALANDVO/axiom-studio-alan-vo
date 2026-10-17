"""Application settings and environment configuration."""
import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Axiom Studio."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core environment
    app_name: str = "Axiom Studio"
    version: str = "1.0.1"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    database_url: str = Field(default="sqlite:///./axiom_studio.sqlite3", alias="DATABASE_URL")

    # Keycloak OIDC Authentication with SAML identity brokering
    keycloak_url: str = Field(default="http://127.0.0.1:8080", alias="KEYCLOAK_URL")
    keycloak_realm: str = Field(default="axiom-realm", alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="axiom-studio", alias="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: Optional[str] = Field(default=None, alias="KEYCLOAK_CLIENT_SECRET")
    jwt_secret_key: str = Field(default="axiom-studio-dev-signature-secret-key-998244", alias="JWT_SECRET_KEY")

    # Advisory LLM settings (opt-in, non-secret parameters + single credential)
    llm_provider: str = Field(default="openai-compatible", alias="LLM_PROVIDER")
    llm_model: Optional[str] = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_request_timeout_seconds: float = Field(default=10.0, alias="LLM_TIMEOUT")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_envs = {"development", "testing", "staging", "production"}
        lowered = v.lower()
        if lowered not in valid_envs:
            return "development"
        return lowered

    def validate_production_safety(self) -> None:
        """Startup check: refuse demo mode in production environments."""
        if self.environment == "production" and self.demo_mode:
            raise ValueError(
                "Security violation: DEMO_MODE=true is strictly forbidden in production environment."
            )


settings = Settings()
settings.validate_production_safety()
