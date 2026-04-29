"""Top-level importability checks for the public surfaces."""

from __future__ import annotations

import importlib


def test_jama_client_public_surface_imports():
    from jama_client import (
        Item,
        ItemFields,
        JamaAuthError,
        JamaClient,
        JamaError,
        JamaForbiddenError,
        JamaNetworkError,
        JamaNotFoundError,
        JamaRateLimitError,
        JamaServerError,
        JamaValidationError,
        OAuthCredentials,
        Project,
        Relationship,
        RelationshipType,
        TestRun,
        Token,
        TokenCache,
        User,
    )

    assert JamaClient is not None
    assert issubclass(JamaAuthError, JamaError)
    for cls in (
        User,
        Project,
        Item,
        ItemFields,
        Relationship,
        RelationshipType,
        TestRun,
        Token,
        TokenCache,
        OAuthCredentials,
    ):
        assert cls is not None


def test_jama_client_submodules_import():
    """Every jama_client submodule imports without error."""
    for module in ("auth", "client", "exceptions", "models"):
        importlib.import_module(f"jama_client.{module}")


def test_jama_mcp_server_package_imports():
    import jama_mcp_server


def test_jama_mcp_server_submodules_import():
    """Every jama_mcp_server submodule imports without error."""
    for module in ("config", "logging_config", "server", "tools"):
        importlib.import_module(f"jama_mcp_server.{module}")
