"""Integration-test pytest configuration.

Skips the entire integration suite when the required Jamacloud OAuth
environment variables are absent. Phase 0 declares the skip mechanism;
Phase 1 will add live-sandbox fixtures.
"""

from __future__ import annotations

import os

import pytest

_REQUIRED_ENV_VARS = ("JAMA_BASE_URL", "JAMA_OAUTH_CLIENT_ID", "JAMA_OAUTH_CLIENT_SECRET")


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip integration tests when Jamacloud credentials are not configured."""
    missing = [name for name in _REQUIRED_ENV_VARS if not os.environ.get(name)]
    if not missing:
        return

    skip_reason = (
        "integration suite skipped: missing environment variables "
        f"{', '.join(missing)}. Set them in .env to enable."
    )
    skip_marker = pytest.mark.skip(reason=skip_reason)
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)
