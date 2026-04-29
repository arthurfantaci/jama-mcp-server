"""Settings management for the Jama MCP Server.

This module will define a ``Settings`` class extending
``pydantic_settings.BaseSettings`` to load required configuration from
environment variables (``JAMA_BASE_URL``, ``JAMA_OAUTH_CLIENT_ID``,
``JAMA_OAUTH_CLIENT_SECRET``, ``MCP_TRANSPORT``, ``MCP_HTTP_HOST``,
``MCP_HTTP_PORT``). Settings instantiation occurs at server startup and
fails loud if required values are missing. Phase 0 contains only this
placeholder.
"""
