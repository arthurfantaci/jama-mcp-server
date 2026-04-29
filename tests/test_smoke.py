"""Smoke tests verifying the Phase 0 skeleton imports cleanly.

These tests exist solely to give pytest something to collect during
Phase 0 (so the test job in CI exits 0 rather than 5 for "no tests
collected") and to verify the package import surface is wired
correctly. They are replaced by real tests in Phase 1.
"""

import importlib


def test_jama_client_package_imports() -> None:
    """The :mod:`jama_client` package imports without error."""
    importlib.import_module("jama_client")


def test_jama_client_modules_import() -> None:
    """All :mod:`jama_client` submodules import without error."""
    for module in ("auth", "client", "exceptions", "models"):
        importlib.import_module(f"jama_client.{module}")


def test_jama_mcp_server_package_imports() -> None:
    """The :mod:`jama_mcp_server` package imports without error."""
    importlib.import_module("jama_mcp_server")


def test_jama_mcp_server_modules_import() -> None:
    """All :mod:`jama_mcp_server` submodules import without error."""
    for module in ("config", "logging_config", "server", "tools"):
        importlib.import_module(f"jama_mcp_server.{module}")
