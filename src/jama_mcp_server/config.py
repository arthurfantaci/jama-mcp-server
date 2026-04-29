"""Settings management for the Jama MCP Server.

Reads configuration from environment variables (or a local ``.env`` file).
The class fails loud with ``pydantic.ValidationError`` at startup if any
required value is missing or malformed; this is intentional per the
design spec's Section 6 error-handling policy.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Transport = Literal["stdio", "streamable-http"]


class Settings(BaseSettings):
    """Runtime configuration for the Jama MCP Server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    jama_base_url: str = Field(...)
    jama_oauth_client_id: str = Field(...)
    jama_oauth_client_secret: SecretStr = Field(...)

    mcp_transport: Transport = "stdio"
    mcp_http_host: str = "127.0.0.1"
    mcp_http_port: int = 8765
