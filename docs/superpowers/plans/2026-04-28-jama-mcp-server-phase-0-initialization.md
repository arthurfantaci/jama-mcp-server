# Phase 0 — Initialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the Jama MCP Server repository so a clean clone passes `uv sync`, `uv run ruff check`, `uv run mypy src/`, and `uv run pytest` against a skeleton-only codebase, then publish the inception commit to a public GitHub repository at `github.com/arthurfantaci/jama-mcp-server`.

**Architecture:** Two top-level Python packages (`jama_client` and `jama_mcp_server`) under `src/`, governed by a single `pyproject.toml`. Phase 0 creates importable skeletons with no implementation; Phase 1 fills them in. Memory-hygiene apparatus, GitHub configuration, editor configuration, and CI are wired in this phase so subsequent phases inherit the rigor.

**Tech Stack:** Python 3.12, `uv` for dependency management, `hatchling` build backend, `ruff` (21 lint rule families, Google docstring convention), `mypy` strict mode, `pytest` with `pytest-asyncio` (auto mode), `pre-commit` with `gitleaks` for secret scanning, GitHub Actions for CI, Apache 2.0 license.

**Reference spec:** `docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`

---

## File Structure

This plan creates the following files. Paths are relative to the repository root (`/Users/arthurfantaci/jama-mcp-server`).

### Build, lint, and runtime configuration

- `pyproject.toml`
- `.python-version`
- `.gitignore`
- `.env.example`
- `.editorconfig`
- `.markdownlint.jsonc`
- `.pre-commit-config.yaml`
- `.gitleaks.toml`

### Editor configuration

- `.vscode/settings.json`
- `.vscode/extensions.json`
- `.vscode/launch.json`

### GitHub configuration

- `.github/workflows/ci.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/CODEOWNERS`
- `.github/dependabot.yml`

### Source skeletons

- `src/jama_client/__init__.py`
- `src/jama_client/auth.py`
- `src/jama_client/client.py`
- `src/jama_client/exceptions.py`
- `src/jama_client/models.py`
- `src/jama_mcp_server/__init__.py`
- `src/jama_mcp_server/__main__.py`
- `src/jama_mcp_server/server.py`
- `src/jama_mcp_server/tools.py`
- `src/jama_mcp_server/config.py`
- `src/jama_mcp_server/logging_config.py`

### Test skeletons

- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_smoke.py`
- `tests/unit/__init__.py`
- `tests/unit/jama_client/__init__.py`
- `tests/unit/jama_mcp_server/__init__.py`
- `tests/integration/__init__.py`
- `tests/integration/conftest.py`
- `tests/fixtures/jama_responses/.gitkeep`

### User-facing documentation

- `LICENSE`
- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `docs/setup.md`

### Memory hygiene apparatus

- `CLAUDE.md`
- `MEMORY.md`
- `.claude/settings.json`
- `.claude/hooks/validate-docs-placement.sh`
- `.claude/skills/memory-hygiene/SKILL.md`
- `.claude/commands/plan.md`
- `.claude/commands/implement.md`
- `.claude/commands/review.md`
- `.claude/commands/test.md`
- `.claude/commands/memory-audit.md`
- `.claude/commands/pre-compact.md`
- `.claude/commands/phase-handoff.md`

### Already present (created during brainstorming)

- `docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`
- `docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md` (this file)

**Total new files in this plan:** 49.

---

## Prerequisites

Before starting Task 1, verify the local environment has the required tooling.

- [ ] **Verify `uv` is installed**

Run: `uv --version`

Expected: a version string such as `uv 0.5.0` or newer.

If absent: install via `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `winget install --id=astral-sh.uv` (Windows).

- [ ] **Verify Python 3.12 is available via `uv`**

Run: `uv python list | grep "3.12"`

Expected: at least one `cpython-3.12.x` entry. If absent, run `uv python install 3.12` to install it.

- [ ] **Verify `git` is installed and configured**

Run: `git --version && git config --get user.name && git config --get user.email`

Expected: a git version string plus the configured user name and email. If `user.email` is unset, set it via `git config --global user.email "arthur.fantaci@mac.com"`.

- [ ] **Verify `gh` (GitHub CLI) is installed and authenticated**

Run: `gh auth status`

Expected: `Logged in to github.com as arthurfantaci`. If not authenticated, run `gh auth login` and complete the flow.

If `gh` is not installed, install via `brew install gh` (macOS) or follow the platform instructions at <https://cli.github.com/>.

- [ ] **Verify the working directory exists and is empty (except for the design and plan documents)**

Run: `ls -A /Users/arthurfantaci/jama-mcp-server`

Expected: only `docs/` is listed.

If the directory contains other files, halt and reconcile before proceeding.

---

## Task 1: Project metadata and build configuration

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/pyproject.toml`
- Create: `/Users/arthurfantaci/jama-mcp-server/.python-version`
- Create: `/Users/arthurfantaci/jama-mcp-server/LICENSE`

- [ ] **Step 1: Create `pyproject.toml`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/pyproject.toml`:

```toml
[project]
name = "jama-mcp-server"
version = "0.0.1"
description = "Model Context Protocol server providing access to Jamacloud (Jama Connect SaaS) via its REST API."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "Apache-2.0" }
keywords = [
    "mcp",
    "model-context-protocol",
    "jama",
    "jama-connect",
    "jamacloud",
    "agentic-ai",
    "fastmcp",
    "requirements-traceability",
]
authors = [{ name = "Arthur Fantaci" }]
classifiers = [
    "Development Status :: 1 - Planning",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Typing :: Typed",
]

dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "structlog>=24.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "respx>=0.21.0",
    "ruff>=0.6.0",
    "mypy>=1.10.0",
    "pre-commit>=4.0.0",
]

[project.scripts]
jama-mcp-stdio = "jama_mcp_server.server:main_stdio"
jama-mcp-http = "jama_mcp_server.server:main_http"

[project.urls]
Homepage = "https://github.com/arthurfantaci/jama-mcp-server"
Repository = "https://github.com/arthurfantaci/jama-mcp-server"
Issues = "https://github.com/arthurfantaci/jama-mcp-server/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/jama_client", "src/jama_mcp_server"]

# =============================================================================
# Ruff Configuration
# =============================================================================
[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "D",      # pydocstyle
    "UP",     # pyupgrade
    "ANN",    # flake8-annotations
    "S",      # flake8-bandit (security)
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "RUF",    # Ruff-specific rules
    "TRY",    # tryceratops (exception handling)
    "EM",     # flake8-errmsg (exception messages)
    "PIE",    # flake8-pie
    "PT",     # flake8-pytest-style
    "RET",    # flake8-return
    "ARG",    # flake8-unused-arguments
    "PL",     # Pylint
]

ignore = [
    "D100",   # Missing docstring in public module
    "D104",   # Missing docstring in public package
    "D107",   # Missing docstring in __init__
    "ANN401", # Dynamically typed expressions (Any)
    "TRY003", # Long exception messages
    "EM101",  # String literal in exception
    "EM102",  # f-string in exception
    "RET504", # Unnecessary variable before return
    "PLR0913",# Too many function arguments
    "PLR2004",# Magic value in comparison
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S101",
    "S105",
    "S311",
    "ANN",
    "D",
    "PLR2004",
    "ARG",
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# =============================================================================
# Pytest Configuration
# =============================================================================
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = ["-ra", "-q", "--strict-markers"]
markers = [
    "integration: opt-in tests that hit the real Jamacloud sandbox (requires JAMA_OAUTH_CLIENT_ID and JAMA_OAUTH_CLIENT_SECRET)",
]

# =============================================================================
# Coverage Configuration
# =============================================================================
[tool.coverage.run]
source = ["src/jama_client", "src/jama_mcp_server"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 0

# =============================================================================
# Mypy Configuration
# =============================================================================
[tool.mypy]
python_version = "3.12"
strict = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_unreachable = true
disallow_untyped_defs = true
check_untyped_defs = true
no_implicit_reexport = true
plugins = ["pydantic.mypy"]
files = ["src"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
check_untyped_defs = false
```

- [ ] **Step 2: Create `.python-version`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.python-version`:

```text
3.12
```

- [ ] **Step 3: Create `LICENSE` (Apache 2.0)**

Write the canonical Apache License 2.0 text to `/Users/arthurfantaci/jama-mcp-server/LICENSE`. The exact text is published at <https://www.apache.org/licenses/LICENSE-2.0.txt>. Append a copyright line at the top:

```text
Copyright 2026 Arthur Fantaci

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      [... continues with the full Apache 2.0 text ...]

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      [... full appendix ...]

   Copyright 2026 Arthur Fantaci

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```

The full canonical text is approximately 200 lines. Fetch it via:

```bash
curl -sSL https://www.apache.org/licenses/LICENSE-2.0.txt -o /Users/arthurfantaci/jama-mcp-server/LICENSE
```

Then prepend the copyright line by editing the file.

- [ ] **Step 4: Verify pyproject.toml is parseable**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv lock`

Expected: `Resolved N packages in <time>`. A `uv.lock` file is created in the repository root. No errors.

If the command fails with a parse error, inspect `pyproject.toml` for syntax issues (likely an unbalanced bracket or quote).

---

## Task 2: Source code skeletons — `jama_client`

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_client/__init__.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_client/auth.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_client/client.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_client/exceptions.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_client/models.py`

- [ ] **Step 1: Create `src/jama_client/__init__.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_client/__init__.py`:

```python
"""Asynchronous Python client for the Jamacloud REST API.

This package will export the public surface (``JamaClient``, the exception
hierarchy, and the entity models) once Phase 1 implementation lands. The
Phase 0 skeleton intentionally contains no implementation; importing this
package succeeds but exposes nothing yet.
"""
```

- [ ] **Step 2: Create `src/jama_client/exceptions.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_client/exceptions.py`:

```python
"""Exception hierarchy for the Jamacloud REST API client.

The exception hierarchy maps Jamacloud HTTP error semantics to typed Python
exceptions. The full hierarchy is defined in
``docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`` Section 6
and is implemented in Phase 1.
"""
```

- [ ] **Step 3: Create `src/jama_client/models.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_client/models.py`:

```python
"""Pydantic v2 entity models for Jamacloud API responses.

Models are configured with ``ConfigDict(extra="allow")`` to remain
forward-compatible with Jamacloud schema additions. Phase 0 contains only
this module-level placeholder; entity definitions land in Phase 1.
"""
```

- [ ] **Step 4: Create `src/jama_client/auth.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_client/auth.py`:

```python
"""OAuth 2.0 client_credentials authentication for Jamacloud.

This module will implement the OAuth credential grant flow against
``/rest/oauth/token``, an in-memory token cache with proactive refresh at
or above 90 percent of the token's TTL, and the wire-call helper used by
``JamaClient``. Phase 0 contains only this placeholder.
"""
```

- [ ] **Step 5: Create `src/jama_client/client.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_client/client.py`:

```python
"""Asynchronous HTTP client for the Jamacloud REST API.

This module will define the ``JamaClient`` async context manager wrapping
``httpx.AsyncClient``. It owns the OAuth token cache, performs response
envelope unwrapping, maps HTTP status codes to typed exceptions, and
implements the narrow retry policy defined in the design specification.
Phase 0 contains only this placeholder.
"""
```

- [ ] **Step 6: Verify the package imports cleanly**

Run: `cd /Users/arthurfantaci/jama-mcp-server && PYTHONPATH=src uv run --frozen python -c "import jama_client; import jama_client.auth; import jama_client.client; import jama_client.exceptions; import jama_client.models; print('OK')"`

Expected output: `OK` on stdout, exit code 0.

If imports fail with `ModuleNotFoundError`, verify the file paths and that all five files were created.

---

## Task 3: Source code skeletons — `jama_mcp_server`

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/__init__.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/__main__.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/config.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/logging_config.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/server.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/tools.py`

- [ ] **Step 1: Create `src/jama_mcp_server/__init__.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/__init__.py`:

```python
"""FastMCP server exposing Jamacloud REST operations as MCP tools.

The package defines the FastMCP application instance, transport-specific
entry points (stdio and streamable HTTP), the lifespan context that owns
the shared ``JamaClient``, and six MCP tool functions implementing the
Phase 1 traceability slice.
"""
```

- [ ] **Step 2: Create `src/jama_mcp_server/config.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/config.py`:

```python
"""Settings management for the Jama MCP Server.

This module will define a ``Settings`` class extending
``pydantic_settings.BaseSettings`` to load required configuration from
environment variables (``JAMA_BASE_URL``, ``JAMA_OAUTH_CLIENT_ID``,
``JAMA_OAUTH_CLIENT_SECRET``, ``MCP_TRANSPORT``, ``MCP_HTTP_HOST``,
``MCP_HTTP_PORT``). Settings instantiation occurs at server startup and
fails loud if required values are missing. Phase 0 contains only this
placeholder.
"""
```

- [ ] **Step 3: Create `src/jama_mcp_server/logging_config.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/logging_config.py`:

```python
"""Transport-aware structlog configuration.

The MCP stdio transport reserves stdout for JSON-RPC framing; logs must
therefore go to stderr. The streamable HTTP transport runs in containers
that expect logs on stdout. The ``configure_logging(transport)`` function
selects the correct sink based on the transport name. Phase 0 contains
only this placeholder.
"""
```

- [ ] **Step 4: Create `src/jama_mcp_server/server.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/server.py`:

```python
"""FastMCP application instance and transport entry points.

The Phase 0 skeleton declares ``main_stdio`` and ``main_http`` as
no-op entry points so the console scripts declared in ``pyproject.toml``
install successfully and produce a clear error if invoked before Phase 1
implementation lands.
"""

from typing import NoReturn


def main_stdio() -> NoReturn:
    """Run the MCP server using the stdio transport.

    Raises:
        NotImplementedError: Always. Implementation lands in Phase 1.
    """
    msg = "main_stdio is implemented in Phase 1; see docs/superpowers/specs/."
    raise NotImplementedError(msg)


def main_http() -> NoReturn:
    """Run the MCP server using the streamable HTTP transport.

    Raises:
        NotImplementedError: Always. Implementation lands in Phase 1.
    """
    msg = "main_http is implemented in Phase 1; see docs/superpowers/specs/."
    raise NotImplementedError(msg)
```

- [ ] **Step 5: Create `src/jama_mcp_server/tools.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/tools.py`:

```python
"""MCP tool definitions for the Jama traceability slice.

This module will define six ``@mcp.tool()``-decorated async functions
mirroring the Phase 1 client operations: ``whoami``, ``list_projects``,
``get_item``, ``search_items``, ``get_downstream_relationships``, and
``get_test_runs_for_item``. Each tool retrieves the shared ``JamaClient``
from the lifespan context and returns AI-shaped dictionaries. Phase 0
contains only this placeholder.
"""
```

- [ ] **Step 6: Create `src/jama_mcp_server/__main__.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/src/jama_mcp_server/__main__.py`:

```python
"""Command-line entry point for ``python -m jama_mcp_server``.

The Phase 0 skeleton dispatches to the placeholder entry points in
``server.py`` based on the ``MCP_TRANSPORT`` environment variable.
"""

from __future__ import annotations

import os
import sys

from jama_mcp_server.server import main_http, main_stdio


def _dispatch() -> None:
    """Dispatch to the transport entry point named by ``MCP_TRANSPORT``."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "stdio":
        main_stdio()
    elif transport in {"streamable-http", "http"}:
        main_http()
    else:
        msg = (
            f"Unknown MCP_TRANSPORT value: {transport!r}. "
            "Expected 'stdio' or 'streamable-http'."
        )
        print(msg, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _dispatch()
```

- [ ] **Step 7: Verify the package imports cleanly**

Run: `cd /Users/arthurfantaci/jama-mcp-server && PYTHONPATH=src uv run --frozen python -c "import jama_mcp_server; import jama_mcp_server.config; import jama_mcp_server.logging_config; import jama_mcp_server.server; import jama_mcp_server.tools; print('OK')"`

Expected output: `OK` on stdout, exit code 0.

- [ ] **Step 8: Verify console scripts dispatch correctly when imported**

Run: `cd /Users/arthurfantaci/jama-mcp-server && PYTHONPATH=src uv run --frozen python -c "from jama_mcp_server.server import main_stdio, main_http; print(main_stdio, main_http)"`

Expected output: two function objects printed, no errors.

The functions are not invoked here; invoking them will raise `NotImplementedError`, which is the intended Phase 0 behavior.

---

## Task 4: Test skeletons and smoke test

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/tests/__init__.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/tests/conftest.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/tests/test_smoke.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/tests/unit/__init__.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/tests/unit/jama_client/__init__.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/tests/unit/jama_mcp_server/__init__.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/tests/integration/__init__.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/tests/integration/conftest.py`
- Create: `/Users/arthurfantaci/jama-mcp-server/tests/fixtures/jama_responses/.gitkeep`

- [ ] **Step 1: Create `tests/__init__.py`**

Write the following content (empty module marker, single-line docstring) to `/Users/arthurfantaci/jama-mcp-server/tests/__init__.py`:

```python
"""Test suite for the Jama MCP Server."""
```

- [ ] **Step 2: Create `tests/conftest.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/tests/conftest.py`:

```python
"""Shared pytest fixtures for the Jama MCP Server test suite.

Phase 0 declares only the structural scaffolding. Phase 1 will add
fixtures for token samples, envelope responses, mock client factories,
and respx routers.
"""
```

- [ ] **Step 3: Create `tests/test_smoke.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/tests/test_smoke.py`:

```python
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
```

- [ ] **Step 4: Create `tests/unit/__init__.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/tests/unit/__init__.py`:

```python
"""Unit tests for the Jama MCP Server."""
```

- [ ] **Step 5: Create `tests/unit/jama_client/__init__.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/tests/unit/jama_client/__init__.py`:

```python
"""Unit tests for the :mod:`jama_client` package."""
```

- [ ] **Step 6: Create `tests/unit/jama_mcp_server/__init__.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/tests/unit/jama_mcp_server/__init__.py`:

```python
"""Unit tests for the :mod:`jama_mcp_server` package."""
```

- [ ] **Step 7: Create `tests/integration/__init__.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/tests/integration/__init__.py`:

```python
"""Integration tests against the live Jamacloud sandbox."""
```

- [ ] **Step 8: Create `tests/integration/conftest.py`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/tests/integration/conftest.py`:

```python
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
    config: pytest.Config,  # noqa: ARG001
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
```

- [ ] **Step 9: Create `tests/fixtures/jama_responses/.gitkeep`**

Create the empty fixtures directory and a `.gitkeep` placeholder so it can be committed.

Run: `mkdir -p /Users/arthurfantaci/jama-mcp-server/tests/fixtures/jama_responses && touch /Users/arthurfantaci/jama-mcp-server/tests/fixtures/jama_responses/.gitkeep`

Expected: the directory exists with a single zero-byte `.gitkeep` file.

- [ ] **Step 10: Verify pytest collects the smoke tests**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run --frozen pytest --collect-only -q`

Expected: pytest reports 4 tests collected from `tests/test_smoke.py`. The integration suite reports zero collected items because no integration tests exist yet.

---

## Task 5: Environment, git, and editor configuration files

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/.gitignore`
- Create: `/Users/arthurfantaci/jama-mcp-server/.env.example`
- Create: `/Users/arthurfantaci/jama-mcp-server/.editorconfig`
- Create: `/Users/arthurfantaci/jama-mcp-server/.markdownlint.jsonc`

- [ ] **Step 1: Create `.gitignore`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.gitignore`:

```text
# Repository hygiene philosophy
# ============================
# This .gitignore curates the public surface of the repository. The repo
# is public on GitHub from inception and is reviewed by potential
# employers, including but not limited to Jama Software engineers and
# their hiring managers. Files listed here are deliberately excluded
# because they would either leak secrets, leak per-user state, or
# portray the project as anything other than serious, professional
# Agentic AI Application Engineering work.
#
# Working notes and exploratory writing belong in docs/internal/ (also
# ignored), not in the public repository.

# Environment and secrets
.env
.env.local
.env.*.local
*.pem
*.key
credentials.json

# Python build/cache artifacts
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
*.whl

# Virtual environments
.venv/
venv/
ENV/

# Testing
.pytest_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml
.tox/
.nox/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json

# Linting
.ruff_cache/

# IDE — personal/user-specific (project-shared settings live in .vscode/)
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Internal documentation — working notes never enter the public repository.
# Public documentation lives in docs/ root and docs/superpowers/{specs,plans}/.
docs/internal/
docs/plans/

# Claude Code per-user state
.claude/settings.local.json
.claude/worktrees/
```

- [ ] **Step 2: Create `.env.example`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.env.example`:

```text
# Jamacloud REST API endpoint (no trailing slash).
JAMA_BASE_URL=https://pm2.jamacloud.com

# OAuth 2.0 client credentials provisioned via Jama Connect's
# "Set API Credentials using OAuth 2.0" panel. Create a dedicated
# credential named "jama-mcp-server-dev" rather than reusing existing
# credentials so it can be revoked independently if needed.
JAMA_OAUTH_CLIENT_ID=
JAMA_OAUTH_CLIENT_SECRET=

# MCP server transport. Use "stdio" for local development with Claude
# Desktop or Claude Code. Use "streamable-http" for the Phase 2 Docker
# build and Phase 3 Kubernetes deployment.
MCP_TRANSPORT=stdio

# HTTP transport binding (only used when MCP_TRANSPORT=streamable-http).
MCP_HTTP_HOST=127.0.0.1
MCP_HTTP_PORT=8765
```

- [ ] **Step 3: Create `.editorconfig`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.editorconfig`:

```text
# https://editorconfig.org/

root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{yml,yaml,json,jsonc,toml,md}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

- [ ] **Step 4: Create `.markdownlint.jsonc`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.markdownlint.jsonc`:

```jsonc
{
  // markdownlint configuration
  // Rules reference: https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md

  // --- Disabled rules ---

  // MD013: Line length — too noisy for documentation prose.
  "MD013": false,

  // MD024: No duplicate headings — conflicts with structured docs that repeat
  // section names (for example, "Reasons for the split" appears multiple times).
  "MD024": false,

  // MD033: No inline HTML — sometimes needed for tables and details/summary blocks.
  "MD033": false,

  // MD041: First line should be a top-level heading — CLAUDE.md and similar
  // files may begin with a comment block.
  "MD041": false,

  // --- Customized rules ---

  // MD007: Unordered list indentation — match 2-space indent.
  "MD007": { "indent": 2 },

  // MD010: No hard tabs — spaces only.
  "MD010": true,

  // MD012: No multiple consecutive blank lines.
  "MD012": true,

  // MD047: Files end with a single trailing newline.
  "MD047": true
}
```

- [ ] **Step 5: Verify the files render correctly in git**

Run: `cd /Users/arthurfantaci/jama-mcp-server && cat .gitignore | head -20 && echo "---" && cat .env.example`

Expected: the first 20 lines of `.gitignore` (including the philosophy comment block) followed by `---` and the full `.env.example` content.

---

## Task 6: Pre-commit and secret-scanning configuration

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/.pre-commit-config.yaml`
- Create: `/Users/arthurfantaci/jama-mcp-server/.gitleaks.toml`

- [ ] **Step 1: Create `.pre-commit-config.yaml`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.pre-commit-config.yaml`:

```yaml
# Pre-commit hooks for the Jama MCP Server project.
# Install:    pre-commit install
# Run all:    pre-commit run --all-files

repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: uv run ruff check --fix
        language: system
        types: [python]
        pass_filenames: false

      - id: ruff-format
        name: ruff format
        entry: uv run ruff format
        language: system
        types: [python]
        pass_filenames: false

      - id: mypy
        name: mypy
        entry: uv run mypy src/
        language: system
        types: [python]
        pass_filenames: false

      - id: validate-docs-placement
        name: validate docs placement
        entry: .claude/hooks/validate-docs-placement.sh
        language: script
        files: ^docs/.*\.md$
        exclude: ^docs/internal/
        pass_filenames: false

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
```

- [ ] **Step 2: Create `.gitleaks.toml`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.gitleaks.toml`:

```toml
# gitleaks configuration for the Jama MCP Server project.
# Extends the gitleaks default ruleset. Project-specific allow-rules
# below permit secret-shaped strings in documentation files where they
# are illustrative rather than real credentials.

title = "Jama MCP Server gitleaks config"

[extend]
useDefault = true

[allowlist]
description = "Documentation paths permitted to contain illustrative secret-shaped patterns"
paths = [
    '''^\.env\.example$''',
    '''^docs/superpowers/specs/.*\.md$''',
    '''^docs/superpowers/plans/.*\.md$''',
    '''^README\.md$''',
]
```

- [ ] **Step 3: Verify the YAML and TOML are well-formed**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run --frozen python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))" && uv run --frozen python -c "import tomllib; tomllib.loads(open('.gitleaks.toml').read())" && echo OK`

Expected output: `OK`. No exceptions raised.

---

## Task 7: Editor configuration (`.vscode/`)

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/.vscode/settings.json`
- Create: `/Users/arthurfantaci/jama-mcp-server/.vscode/extensions.json`
- Create: `/Users/arthurfantaci/jama-mcp-server/.vscode/launch.json`

- [ ] **Step 1: Create `.vscode/settings.json`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.vscode/settings.json`:

```jsonc
{
  // Python interpreter discovery — use venvPath/venvFolders, NEVER defaultInterpreterPath.
  // The latter causes persistent warnings in VS Code Insiders and is ignored once
  // an interpreter is cached.
  "python.venvPath": "${workspaceFolder}",
  "python.venvFolders": [".venv"],
  "python.terminal.activateEnvironment": true,
  "python.createEnvironment.trigger": "off",

  // Ruff is the primary linter and formatter (replaces Black, isort, Flake8).
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.formatOnPaste": false,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },

  // Ruff extension wiring.
  "ruff.path": ["${workspaceFolder}/.venv/bin/ruff"],
  "ruff.importStrategy": "fromEnvironment",
  "ruff.lint.enable": true,
  "ruff.configuration": "./pyproject.toml",

  // Pytest as the test runner.
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["tests", "-v"],

  // Editor settings for Python.
  "editor.rulers": [100],
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,

  // File associations for env files.
  "files.associations": {
    "*.env": "dotenv",
    "*.env.*": "dotenv",
    ".env.example": "dotenv"
  },

  // Hide cache directories and build artifacts from the explorer/search.
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/.ruff_cache": true,
    "**/.mypy_cache": true,
    "**/htmlcov": true,
    "**/*.egg-info": true
  },
  "search.exclude": {
    "**/.venv": true,
    "**/.git": true,
    "**/uv.lock": true
  },

  // Set PYTHONPATH so `python -m` resolves the src/ packages.
  "terminal.integrated.env.osx": {
    "PYTHONPATH": "${workspaceFolder}/src"
  },
  "terminal.integrated.env.linux": {
    "PYTHONPATH": "${workspaceFolder}/src"
  },

  // Pylance type checking.
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.inlayHints.functionReturnTypes": true,

  // JSON, JSONC, and TOML formatting.
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[toml]": {
    "editor.defaultFormatter": "tamasfe.even-better-toml"
  },

  // Markdown.
  "[markdown]": {
    "editor.wordWrap": "on"
  }
}
```

- [ ] **Step 2: Create `.vscode/extensions.json`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.vscode/extensions.json`:

```jsonc
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-python.debugpy",
    "tamasfe.even-better-toml",
    "mikestead.dotenv",
    "esbenp.prettier-vscode",
    "redhat.vscode-yaml",
    "eamodio.gitlens",
    "mhutchie.git-graph",
    "usernamehw.errorlens",
    "christian-kohler.path-intellisense",
    "ms-azuretools.vscode-docker"
  ],
  "unwantedRecommendations": [
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8"
  ]
}
```

- [ ] **Step 3: Create `.vscode/launch.json`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.vscode/launch.json`:

```jsonc
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "MCP server (stdio)",
      "type": "debugpy",
      "request": "launch",
      "module": "jama_mcp_server",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src",
        "MCP_TRANSPORT": "stdio"
      },
      "envFile": "${workspaceFolder}/.env",
      "justMyCode": true
    },
    {
      "name": "MCP server (streamable-http)",
      "type": "debugpy",
      "request": "launch",
      "module": "jama_mcp_server",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src",
        "MCP_TRANSPORT": "streamable-http"
      },
      "envFile": "${workspaceFolder}/.env",
      "justMyCode": true
    },
    {
      "name": "Test: current file",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v", "-s"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      },
      "envFile": "${workspaceFolder}/.env",
      "justMyCode": true
    },
    {
      "name": "Test: all unit tests",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["tests", "-m", "not integration", "-v"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      },
      "envFile": "${workspaceFolder}/.env",
      "justMyCode": true
    }
  ]
}
```

- [ ] **Step 4: Verify the VS Code JSON files parse**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run --frozen python -c "import json, re; [json.loads(re.sub(r'//.*', '', open(p).read())) for p in ('.vscode/settings.json', '.vscode/extensions.json', '.vscode/launch.json')]; print('OK')"`

Expected output: `OK`. The script strips line comments (JSONC) before parsing as JSON.

---

## Task 8: GitHub configuration

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/.github/workflows/ci.yml`
- Create: `/Users/arthurfantaci/jama-mcp-server/.github/dependabot.yml`
- Create: `/Users/arthurfantaci/jama-mcp-server/.github/CODEOWNERS`
- Create: `/Users/arthurfantaci/jama-mcp-server/.github/PULL_REQUEST_TEMPLATE.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `/Users/arthurfantaci/jama-mcp-server/.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `/Users/arthurfantaci/jama-mcp-server/.github/ISSUE_TEMPLATE/config.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"

jobs:
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --frozen --extra dev

      - name: Run ruff lint
        run: uv run ruff check . --output-format=github

      - name: Run ruff format check
        run: uv run ruff format --check .

  type-check:
    name: Type Check (mypy strict)
    runs-on: ubuntu-latest
    needs: [lint]
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --frozen --extra dev

      - name: Run mypy
        run: uv run mypy src/

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: [lint]
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --frozen --extra dev

      - name: Run unit and protocol tests
        run: uv run pytest -m "not integration" --cov=src --cov-report=xml --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        if: success()
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage.xml
          fail_ci_if_error: false

  dependency-review:
    name: Dependency Review
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
```

- [ ] **Step 2: Create `.github/dependabot.yml`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "chore(deps):"
    open-pull-requests-limit: 10

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "ci"
    commit-message:
      prefix: "ci(deps):"
    open-pull-requests-limit: 5
```

- [ ] **Step 3: Create `.github/CODEOWNERS`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.github/CODEOWNERS`:

```text
# CODEOWNERS for the Jama MCP Server project.
# Reference: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

* @arthurfantaci
```

- [ ] **Step 4: Create `.github/PULL_REQUEST_TEMPLATE.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.github/PULL_REQUEST_TEMPLATE.md`:

````markdown
## Description

<!-- Brief description of the changes. -->

## Related Issues

<!-- Link related issues. Auto-close keywords: Fixes #123, Closes #456, Resolves #789. -->

Fixes #

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that changes existing behavior)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Test improvements
- [ ] Infrastructure or CI changes

## Changes Made

<!-- List the specific changes. -->

-

## Testing

- [ ] Unit tests pass (`uv run pytest -m "not integration"`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Type check passes (`uv run mypy src/`)
- [ ] Manual testing performed
- [ ] MCP Inspector validation (if applicable)

## Documentation

- [ ] README updated (if needed)
- [ ] CLAUDE.md updated (if needed)
- [ ] Docstrings updated
- [ ] Design specification updated (if architecture changed)

## Memory Hygiene

- [ ] Memory files audited if architecture, conventions, or core paths changed (`/memory-audit`)
- [ ] MEMORY.md updated to reflect current phase, branch, and task

## Professional Portrayal

- [ ] Reviewed staged files for content that does not meet professional standards
- [ ] No debug `print` statements, commented-out code, or AI-collaboration artifacts
- [ ] Internal working notes (if any) moved to `docs/internal/`

## Release Notes

<!-- Brief description for the changelog. Leave empty for internal/infrastructure changes. -->

```release-notes

```

## Checklist

- [ ] Code follows the project's conventions
- [ ] Self-reviewed before requesting review
- [ ] Tests added or updated
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Linked to a related issue
````

- [ ] **Step 5: Create `.github/ISSUE_TEMPLATE/bug_report.yml`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.github/ISSUE_TEMPLATE/bug_report.yml`:

```yaml
name: Bug Report
description: Report a bug or unexpected behavior in the Jama MCP Server.
title: "[Bug]: "
labels: ["bug", "needs-triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for reporting a bug. Please complete the sections below to help us reproduce and fix the issue.

  - type: textarea
    id: description
    attributes:
      label: Bug Description
      description: What is the bug? What did you expect to happen?
      placeholder: A clear and concise description.
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: Numbered steps that reliably reproduce the bug.
      placeholder: |
        1. Run `...`
        2. Invoke tool `...`
        3. Observe `...`
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What should have happened.
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: Python version, OS, MCP client, transport mode.
      placeholder: |
        - Python: 3.12.x
        - OS: macOS 14.x
        - MCP client: Claude Desktop / MCP Inspector / curl
        - Transport: stdio / streamable-http
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant Logs
      description: Paste any relevant log output. Redact secrets.
      render: shell

  - type: checkboxes
    id: confirmation
    attributes:
      label: Pre-submission checks
      options:
        - label: I searched existing issues for duplicates
          required: true
        - label: I redacted all credentials and personally identifying information
          required: true
```

- [ ] **Step 6: Create `.github/ISSUE_TEMPLATE/feature_request.yml`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.github/ISSUE_TEMPLATE/feature_request.yml`:

```yaml
name: Feature Request
description: Propose a new feature or enhancement for the Jama MCP Server.
title: "[Feature]: "
labels: ["enhancement", "needs-triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for proposing a feature. Please complete the sections below.

  - type: textarea
    id: problem
    attributes:
      label: Problem Statement
      description: What problem does this feature solve?
    validations:
      required: true

  - type: textarea
    id: proposed-solution
    attributes:
      label: Proposed Solution
      description: How should this be implemented? Include API or tool surface details if relevant.
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: What other approaches did you consider, and why did you reject them?

  - type: dropdown
    id: scope
    attributes:
      label: Phase Alignment
      description: Which phase does this feature align with?
      options:
        - Phase 1 (functional MVP)
        - Phase 2 (containerization)
        - Phase 3 (Kubernetes deployment)
        - Post-Phase 3 / unscoped
    validations:
      required: true

  - type: checkboxes
    id: confirmation
    attributes:
      label: Pre-submission checks
      options:
        - label: I searched existing issues for duplicates
          required: true
        - label: I read the design specification under `docs/superpowers/specs/`
          required: true
```

- [ ] **Step 7: Create `.github/ISSUE_TEMPLATE/config.yml`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.github/ISSUE_TEMPLATE/config.yml`:

```yaml
blank_issues_enabled: false
contact_links:
  - name: Documentation
    url: https://github.com/arthurfantaci/jama-mcp-server/tree/main/docs
    about: Read the project documentation before opening an issue.
```

- [ ] **Step 8: Verify all GitHub YAML files parse**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run --frozen python -c "import yaml, glob; [yaml.safe_load(open(p)) for p in glob.glob('.github/**/*.y*ml', recursive=True)]; print('OK')"`

Expected output: `OK`. No exceptions raised.

---

## Task 9: User-facing documentation

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/README.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/CONTRIBUTING.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/SECURITY.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/docs/setup.md`

- [ ] **Step 1: Create `README.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/README.md`:

````markdown
# Jama MCP Server

A Model Context Protocol (MCP) server providing programmatic access to a hosted [Jama Connect](https://www.jamasoftware.com/) instance via its REST API. Implemented with rigorous typing, professional tooling, and a phased delivery roadmap.

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0     | Repository scaffolding, CI/CD, memory hygiene apparatus | In progress |
| 1     | Functional MVP — six MCP tools demonstrating end-to-end traceability | Planned |
| 2     | Docker containerization | Planned |
| 3     | Kubernetes deployment (Minikube) | Planned |

The full design is published in [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md).

## Architecture

The project is organized as two top-level Python packages under a single source tree:

- **`jama_client`** — an asynchronous Python library wrapping a curated subset of the Jamacloud REST API. Owns authentication, transport, retry policy, and Pydantic-typed entity models.
- **`jama_mcp_server`** — a [FastMCP](https://github.com/modelcontextprotocol/python-sdk) server that imports `jama_client` and exposes its operations as MCP tools, supporting both `stdio` and `streamable-http` transports.

This split keeps the Jama API integration reusable independently of the MCP server (for a future MCP client agent, a CLI, or a notebook).

## Phase 1 tool surface

The Phase 1 MVP exposes six MCP tools demonstrating Jama Connect's signature requirements-to-test-runs traceability workflow:

1. `whoami` — identifies the authenticated user.
2. `list_projects` — enumerates accessible Jama projects.
3. `get_item(item_id)` — retrieves a single Jama item.
4. `search_items(project_id, query)` — searches items within a project.
5. `get_downstream_relationships(item_id)` — traces relationships from a requirement toward its tests.
6. `get_test_runs_for_item(item_id)` — retrieves test execution history for a covered item.

## Quick start

> **Phase 0 in progress.** The commands below assume the Phase 1 implementation has landed. They will not produce a functional server during Phase 0.

```bash
git clone https://github.com/arthurfantaci/jama-mcp-server.git
cd jama-mcp-server
uv sync --extra dev
cp .env.example .env
# Populate .env with your Jamacloud OAuth credentials.
uv run jama-mcp-stdio
```

## Configuration

The server reads its configuration from environment variables (or a `.env` file). See [`.env.example`](.env.example) for the full list. The required variables are:

| Variable | Purpose |
|----------|---------|
| `JAMA_BASE_URL` | Jamacloud REST API base URL (e.g., `https://pm2.jamacloud.com`) |
| `JAMA_OAUTH_CLIENT_ID` | OAuth 2.0 client ID provisioned in Jama Connect |
| `JAMA_OAUTH_CLIENT_SECRET` | OAuth 2.0 client secret |
| `MCP_TRANSPORT` | `stdio` or `streamable-http` |

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

Pre-commit hooks (ruff, mypy, gitleaks, validate-docs-placement) install via:

```bash
uv run pre-commit install
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full contribution workflow.

## Documentation

- [`docs/superpowers/specs/`](docs/superpowers/specs/) — design specifications.
- [`docs/superpowers/plans/`](docs/superpowers/plans/) — implementation plans.
- [`docs/setup.md`](docs/setup.md) — local setup instructions.
- [`CLAUDE.md`](CLAUDE.md) — Claude Code project conventions.
- [`MEMORY.md`](MEMORY.md) — project working state.

## Security

See [`SECURITY.md`](SECURITY.md) for the security disclosure policy.

## License

Apache License 2.0. See [`LICENSE`](LICENSE) for the full text.
````

- [ ] **Step 2: Create `CONTRIBUTING.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/CONTRIBUTING.md`:

````markdown
# Contributing to the Jama MCP Server

Thanks for considering a contribution. This project is in active development; the contribution surface is intentionally narrow during Phase 0 and Phase 1.

## Quick links

- [Design specification](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- [Project conventions (`CLAUDE.md`)](CLAUDE.md)
- [Working state (`MEMORY.md`)](MEMORY.md)

## Local development setup

```bash
git clone https://github.com/arthurfantaci/jama-mcp-server.git
cd jama-mcp-server
uv sync --extra dev
uv run pre-commit install
cp .env.example .env
# Populate .env with your Jamacloud OAuth credentials.
```

## Branch and PR workflow

- All work after Phase 0 follows an Issue → Branch → PR workflow.
- Branch naming: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`, `refactor/<short-name>`, `test/<short-name>`, `chore/<short-name>`, `ci/<short-name>`.
- Commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification with imperative-mood subjects.
- Documentation-only changes (touching only `CLAUDE.md`, `MEMORY.md`, or per-user memory files) do not get separate issues, branches, or PRs; they are bundled into the next phase's PR.

## Pre-commit checks

The following must pass before a commit lands:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

`pre-commit install` enables these as git hooks. Pre-commit also runs `gitleaks` for secret scanning and `validate-docs-placement` for documentation hygiene.

## Coding conventions

- **Python 3.12.** All code targets Python 3.12 syntax and standard library.
- **Full type annotations.** All public functions, classes, and methods have type annotations on parameters and return values. `mypy --strict` is a blocking CI check.
- **Google-style docstrings.** All public functions, classes, and methods have Google-style docstrings. Ruff's `D` rules enforce this.
- **Async throughout.** New code in `jama_client` and `jama_mcp_server` is async by default.
- **Errors map to typed exceptions.** Follow the two-layer error policy in the design specification.

## Testing

- **Unit tests** (`tests/unit/`) — `respx`-mocked, fast, run on every save and in CI.
- **Integration tests** (`tests/integration/`) — opt-in via `pytest -m integration`, hit the real Jamacloud sandbox, never run in CI.
- **Protocol tests** (`tests/unit/jama_mcp_server/test_protocol.py`) — use FastMCP's in-process test client.

New `jama_client` code targets at least 80 percent line coverage. New `jama_mcp_server` code triggers every error class at least once.

## Documentation

- Public docs live in `docs/` root and `docs/superpowers/{specs,plans}/`.
- Working notes, raw plans, and exploratory writing live in `docs/internal/` (gitignored).
- Architectural changes update both the relevant design spec and `CLAUDE.md`.

## Reporting issues

Use the GitHub issue templates. Redact secrets and personally identifying information.

## Security

See [`SECURITY.md`](SECURITY.md) for the security disclosure policy.
````

- [ ] **Step 3: Create `SECURITY.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/SECURITY.md`:

````markdown
# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately via GitHub's [private vulnerability reporting](https://github.com/arthurfantaci/jama-mcp-server/security/advisories/new) feature, **not** via public issues.

When reporting, include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce.
- The affected version or commit.
- Any suggested mitigations.

You should receive an acknowledgment within 5 business days. We aim to release a fix within 30 days for critical vulnerabilities.

## Scope

In-scope vulnerabilities include:

- Credential leakage from logs, error messages, or persisted state.
- Authorization bypass against the Jamacloud REST API.
- MCP protocol-level injection or sandbox escape.
- Dependency-chain vulnerabilities (verified via `actions/dependency-review-action` on PRs).

Out-of-scope:

- Vulnerabilities in upstream Jamacloud, the MCP specification, or external libraries (please report those to the respective maintainers).
- Issues that require physical access to the user's machine.

## Secret hygiene

This project never commits secrets:

- `.env` files are gitignored; only `.env.example` (with empty placeholder values) is tracked.
- `gitleaks` runs as a pre-commit hook and scans every commit for accidentally staged credentials.
- OAuth client credentials are provisioned per-developer via Jama Connect's REST API credentials panel and rotated after sharing or compromise.

If you accidentally commit a secret, rotate the affected credential immediately and follow up with a private vulnerability report so the repository history can be rewritten if necessary.
````

- [ ] **Step 4: Create `docs/setup.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/docs/setup.md`:

````markdown
# Local Setup Guide

This document supplements the README's quick-start section with detailed setup instructions for new contributors.

## Prerequisites

- **Python 3.12** — installed via your preferred Python version manager. `uv` will install it automatically if missing.
- **`uv`** — the dependency manager. Install via `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `winget install --id=astral-sh.uv` (Windows).
- **`git`** — version 2.30 or newer.
- **A Jamacloud account** — with a NAMED Creator license (required for REST API access) and OAuth 2.0 client credentials.

## Step 1: Clone the repository

```bash
git clone https://github.com/arthurfantaci/jama-mcp-server.git
cd jama-mcp-server
```

## Step 2: Install dependencies

```bash
uv sync --extra dev
```

This creates a `.venv/` directory, installs all runtime and development dependencies, and pins versions per `uv.lock`.

## Step 3: Install pre-commit hooks

```bash
uv run pre-commit install
```

The hooks run on every commit and enforce ruff lint/format, mypy strict, gitleaks secret scanning, and the `validate-docs-placement` documentation hygiene check.

## Step 4: Provision OAuth credentials

Open Jama Connect, navigate to **My Profile → Set API Credentials using OAuth 2.0**, and create a new credential named `jama-mcp-server-dev` (or similar). Copy the client ID and secret.

## Step 5: Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and populate:

```text
JAMA_BASE_URL=https://pm2.jamacloud.com
JAMA_OAUTH_CLIENT_ID=<your-client-id>
JAMA_OAUTH_CLIENT_SECRET=<your-client-secret>
MCP_TRANSPORT=stdio
```

`.env` is gitignored; it never enters the repository.

## Step 6: Verify the install

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

All four commands should exit with status 0.

## Step 7: Run the integration smoke tests (optional)

```bash
uv run pytest -m integration
```

The integration suite hits the real Jamacloud sandbox and is skipped automatically when `JAMA_OAUTH_CLIENT_ID` or `JAMA_OAUTH_CLIENT_SECRET` are unset.

## Phase status

This setup guide is current as of Phase 0 scaffolding. Phase 1 (functional MVP) and beyond will extend this document with transport-specific run instructions, MCP Inspector configuration, and (in Phase 2) Docker quickstart.
````

- [ ] **Step 5: Verify all markdown files render**

Run: `cd /Users/arthurfantaci/jama-mcp-server && for f in README.md CONTRIBUTING.md SECURITY.md docs/setup.md; do echo "=== $f ==="; head -3 "$f"; done`

Expected: each file's first three lines printed under its header banner. The README begins with `# Jama MCP Server`; CONTRIBUTING.md begins with `# Contributing to the Jama MCP Server`; SECURITY.md begins with `# Security Policy`; setup.md begins with `# Local Setup Guide`.

---

## Task 10: Memory hygiene apparatus

**Files:**

- Create: `/Users/arthurfantaci/jama-mcp-server/CLAUDE.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/MEMORY.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/settings.json`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/hooks/validate-docs-placement.sh`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/skills/memory-hygiene/SKILL.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/commands/plan.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/commands/implement.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/commands/review.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/commands/test.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/commands/memory-audit.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/commands/pre-compact.md`
- Create: `/Users/arthurfantaci/jama-mcp-server/.claude/commands/phase-handoff.md`

- [ ] **Step 1: Create `CLAUDE.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/CLAUDE.md`:

````markdown
# Jama MCP Server — Claude Code Instructions

## Project overview

Model Context Protocol server providing access to Jamacloud (Jama Connect SaaS) via its REST API. Two-layer architecture: `jama_client` (async REST client) and `jama_mcp_server` (FastMCP server). Phase 1 MVP exposes six tools demonstrating requirements-to-test-runs traceability.

Full design: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md).

## Repository visibility

This repository is public on GitHub from inception and is reviewed by potential employers, including Jama Software engineers and their hiring managers. Every committed file must portray the project, the author, and the role of AI-assisted development as serious, professional Agentic AI Application Engineering work.

**Mechanical enforcement:**

- `.claude/hooks/validate-docs-placement.sh` warns on staged docs containing internal markers.
- `gitleaks` (pre-commit) scans every commit for staged credentials.
- `docs/internal/` and `docs/plans/` are gitignored escape hatches for working notes.
- The PR template includes a "Professional Portrayal" checklist.

**Excluded from public surface:** debug `print` statements, commented-out code, AI-collaboration artifacts (e.g., narrative comments referencing the assistant by name), scratch files, half-finished thought experiments.

## Project layout

- `src/jama_client/` — async Jamacloud REST client. Owns auth, transport, models, exceptions.
- `src/jama_mcp_server/` — FastMCP server, tool definitions, transport entry points, lifespan management.
- `tests/{unit,integration}/` — three-tier test suite (unit, integration, MCP-protocol).
- `docs/superpowers/specs/` — design specifications.
- `docs/superpowers/plans/` — implementation plans.

## Conventions

- **Python 3.12**, managed with `uv`. `uv.lock` is committed.
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`.
- **Issue → Branch → PR** for all phases after Phase 0.
- **Documentation-only changes do NOT get separate issues, branches, or PRs.** Bundle into the next phase's PR or commit directly to the working branch.
- **Async throughout.** New code in `jama_client` and `jama_mcp_server` is async by default.
- **Type annotations and Google-style docstrings on every public surface.** Enforced by ruff `ANN` and `D` rules.
- **Errors map to typed exceptions** per the two-layer policy in the design spec.

## Tooling rigor

- **Ruff** (21 rule families): E, W, F, I, N, D, UP, ANN, S, B, C4, SIM, TCH, RUF, TRY, EM, PIE, PT, RET, ARG, PL. Google docstring convention. Per-file relaxations for tests.
- **Mypy strict** (blocking CI check): `strict = true`, pydantic plugin, no implicit reexport.
- **Pytest** with `asyncio_mode = "auto"` and `--strict-markers`.
- **Pre-commit**: ruff, mypy, gitleaks, validate-docs-placement, standard hygiene hooks.

## Verification before PR

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

## Memory hygiene

This project maintains two memory tiers:

- **Public** (in repo, version-controlled): `CLAUDE.md` (this file, ~150 lines max), `MEMORY.md` (~100 lines max), `docs/superpowers/{specs,plans}/`.
- **Private** (per-user): `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/{CLAUDE.md, memory/MEMORY.md}`, plus the Knowledge Graph via the `memory` MCP server.

**Slash commands:**

- `/memory-audit` — invoke the memory-hygiene skill.
- `/pre-compact` — Pre-Compaction Protocol (persist findings, update MEMORY.md).
- `/phase-handoff` — Phase Handoff Protocol (merge PR, clean branches, update memory).

**Triggers** for memory updates: phase completion, new convention codified, non-obvious gotcha discovered, architectural change, approach to auto-compaction, post-PR-merge with path/convention changes.

See [`.claude/skills/memory-hygiene/SKILL.md`](.claude/skills/memory-hygiene/SKILL.md) for the audit checklist.

## Pointers to global protocols

The author's `~/.claude/CLAUDE.md` defines:

- Knowledge Graph Memory Protocol (when to write to KG via `memory` MCP server).
- Context Recovery Protocol (re-establishing state after compaction).
- Phase Handoff Protocol (cross-phase memory hygiene).
- Pre-Compaction Protocol (persist findings before auto-compact).

This project follows those protocols; do not duplicate them here.
````

- [ ] **Step 2: Create `MEMORY.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/MEMORY.md`:

````markdown
# Jama MCP Server — Working State

## Current phase

**Phase 0 — Initialization** (in progress / closing)

**Active branch:** `main`

**Next task:** complete the Phase 0 inception commit and push to GitHub. After Phase 0 closes, transition to Phase 1 — Functional MVP per the design spec.

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository scaffolding, CI/CD, memory hygiene apparatus | In progress |
| 1 | Functional MVP — six MCP tools, both transports | Planned |
| 2 | Docker containerization | Planned |
| 3 | Kubernetes deployment (Minikube) | Planned |

## Recent decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-28 | Approach 1 (two-layer split) approved | Clean separation; client lib reusable later |
| 2026-04-28 | Python 3.12 (not 3.13) | Broader compatibility for clone-and-play audience |
| 2026-04-28 | mypy strict (blocking), not ty | Maturity signal — mypy is the widely-recognized lingua franca |
| 2026-04-28 | Apache 2.0 license | Patent grant; contributor-friendly |
| 2026-04-28 | Public GitHub from Day 1 | Public engineering deliverable from inception |
| 2026-04-28 | FastMCP both transports (stdio + streamable-http) | Same module supports both |
| 2026-04-28 | Three-phase deployment plan (P1 code, P2 Docker, P3 K8s) | Clean troubleshooting boundaries |
| 2026-04-28 | Professional portrayal constraint binding via `validate-docs-placement.sh` hook | Mechanical enforcement |

## Known constraints

- **Repository visibility:** public on GitHub; reviewed by potential employers including Jama Software. Every commit must meet professional standards.
- **OAuth credential discipline:** create a dedicated `jama-mcp-server-dev` credential rather than reusing existing ones; revocable independently.
- **Sandbox URL:** `https://pm2.jamacloud.com` (Jama Software-provisioned sandbox).
- **Author identity:** Arthur Fantaci, `arthur.fantaci@mac.com`.

## Open items deferred to Phase 1

- Provision the `jama-mcp-server-dev` OAuth credential in Jama Connect.
- Populate `.env` locally with the new credential.
- Implement `jama_client.auth` and `jama_client.client`.
- Implement the six MCP tools.
- Author hand-crafted JSON fixtures under `tests/fixtures/jama_responses/`.

## References

- Design spec: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- Phase 0 plan: [`docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md`](docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md)
- Conventions: [`CLAUDE.md`](CLAUDE.md)
- Author's global Claude Code protocols: `~/.claude/CLAUDE.md`
````

- [ ] **Step 3: Create `.claude/settings.json`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/validate-docs-placement.sh"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Create `.claude/hooks/validate-docs-placement.sh`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/hooks/validate-docs-placement.sh`:

```bash
#!/usr/bin/env bash
# validate-docs-placement.sh — Warns when staged documentation contains
# internal markers that should not appear in the public repository.
#
# This is an awareness hook, not a blocker. Warnings go to stderr.
#
# Rule: "Would a hiring manager see this as expertise or learning in progress?"
# If not, move the content to docs/internal/ (gitignored).

set -euo pipefail

# Only check staged markdown files in docs/ (excluding docs/internal/, which is
# gitignored and intended for working notes).
STAGED_DOCS=$(git diff --cached --name-only --diff-filter=ACM -- 'docs/*.md' 'docs/**/*.md' 2>/dev/null \
    | grep -v '^docs/internal/' \
    || true)

if [ -z "$STAGED_DOCS" ]; then
    exit 0
fi

WARNINGS=0

for file in $STAGED_DOCS; do
    MARKERS=""

    # Check for internal-marker section headers.
    if grep -qiE '^\s*#+\s*(open questions|todo|practice exercises|training rubric|gap analysis|session notes)' "$file" 2>/dev/null; then
        MARKERS="section headers with internal markers"
    fi

    # Check for inline TODO items.
    if grep -qiE '\bTODO\b.*:' "$file" 2>/dev/null; then
        MARKERS="${MARKERS:+$MARKERS, }TODO items"
    fi

    # Check for competency checkpoint markers.
    if grep -qiE '^\s*#+\s*.*competency checkpoint' "$file" 2>/dev/null; then
        MARKERS="${MARKERS:+$MARKERS, }competency checkpoints"
    fi

    if [ -n "$MARKERS" ]; then
        echo "warning: docs-placement: $file contains $MARKERS" >&2
        echo "  Consider moving to docs/internal/ (see docs/superpowers/specs/ for the public-vs-internal rule)." >&2
        WARNINGS=$((WARNINGS + 1))
    fi
done

if [ "$WARNINGS" -gt 0 ]; then
    echo "" >&2
    echo "$WARNINGS file(s) may belong in docs/internal/ instead of public docs/." >&2
    echo "Rule: 'Would a hiring manager see this as expertise or learning in progress?'" >&2
fi

exit 0
```

After writing, mark the script executable:

```bash
chmod +x /Users/arthurfantaci/jama-mcp-server/.claude/hooks/validate-docs-placement.sh
```

- [ ] **Step 5: Create `.claude/skills/memory-hygiene/SKILL.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/skills/memory-hygiene/SKILL.md`:

````markdown
---
name: memory-hygiene
description: Audit and update Claude memory files after PRs, milestones, or architectural changes. Use after merging PRs, deleting files, or changing architecture.
allowed-tools: Read, Edit, Write, Glob, Grep
---

# Memory Hygiene

Audit and update Claude's memory files to prevent stale context across sessions.

## Memory file locations

```text
~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/
├── CLAUDE.md        # Author's private session instructions (~150 lines max)
└── memory/
    └── MEMORY.md    # Accumulated session learnings (~100 lines max)
```

```text
<repo-root>/
├── CLAUDE.md        # Project conventions and pointers (~150 lines max)
└── MEMORY.md        # Working state: phase, branch, current task (~100 lines max)
```

## Audit checklist

### 1. Check for stale file references

Extract paths mentioned in memory files and verify each still exists:

```bash
grep -oE '[a-zA-Z_/]+\.(py|md|toml|yml|yaml|json|sh)' CLAUDE.md MEMORY.md
```

Remove references to deleted files. Update paths that have moved.

### 2. Verify architecture sections

Compare the architecture description in `CLAUDE.md` against the actual layout:

```bash
ls -la src/jama_client/
ls -la src/jama_mcp_server/
```

Update the architecture section if module structure has changed.

### 3. Update recent decisions

In `MEMORY.md`, keep only the last 5–10 significant decisions or PRs. Remove older entries.

### 4. Check line counts

- `CLAUDE.md` should be at most ~150 lines.
- `MEMORY.md` should be at most ~100 lines.

```bash
wc -l CLAUDE.md MEMORY.md
wc -l ~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/CLAUDE.md
wc -l ~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/memory/MEMORY.md
```

If over limit, consolidate or archive content.

### 5. Verify patterns are still valid

Review any "Patterns" or "Gotchas" sections. Remove patterns that have been refactored away. Update patterns that have evolved.

### 6. Verify the phase pointer

`MEMORY.md` should accurately reflect:

- The currently active phase (0, 1, 2, 3, or post-3).
- The current working branch.
- The next planned task or PR.

If the phase has just transitioned, run the Phase Handoff Protocol from the author's global `~/.claude/CLAUDE.md`.

## When to run this skill

- After merging a PR that changes architecture, conventions, or core file paths.
- After completing a development phase.
- After deleting modules.
- When session context feels stale or Claude makes outdated suggestions.
- Before approaching memory auto-compaction.
- Monthly hygiene check.

## Output

After running, report:

1. Files audited.
2. Stale references removed.
3. Sections updated.
4. Current line counts versus caps.
5. Any flagged content that may belong in `docs/internal/`.
````

- [ ] **Step 6: Create `.claude/commands/plan.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/commands/plan.md`:

````markdown
# Plan Command

Create a comprehensive implementation plan for: $ARGUMENTS

## Instructions

1. **Do not write any code yet** — this is planning only.
2. Explore the codebase to understand current structure and conventions.
3. Read the relevant design specification under `docs/superpowers/specs/`.
4. Identify all files that need to be created or modified, with exact paths.
5. List implementation steps in logical order.
6. Define success criteria and verification commands.
7. Identify potential risks or blockers.
8. **Wait for approval before implementing.**

## Output format

```markdown
## Implementation Plan: [Feature Name]

### Overview
[Brief description.]

### Files to Create
- `exact/path/to/new_file.py` — purpose

### Files to Modify
- `exact/path/to/existing.py:line-range` — what changes

### Implementation Steps
1. [Step with details and verification.]

### Dependencies
- [Any new packages needed.]

### Success Criteria
- [ ] [Testable criterion.]

### Risks
- [Potential issue and mitigation.]
```

## Important

- Be thorough; do not gloss over file paths or content.
- Consider edge cases.
- Specify the testing strategy.
- Do not start implementing until the plan is approved.
- For non-trivial plans, prefer the `superpowers:writing-plans` skill.
````

- [ ] **Step 7: Create `.claude/commands/implement.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/commands/implement.md`:

````markdown
# Implement Command

Implement the feature: $ARGUMENTS

## Instructions

1. Follow Test-Driven Development (TDD):
   - Write failing test first.
   - Implement minimum code to pass.
   - Refactor while keeping tests green.

2. Follow project conventions documented in `CLAUDE.md` and the relevant spec under `docs/superpowers/specs/`.

3. Apply relevant skills:
   - `fastmcp-patterns` for MCP tool definitions.
   - `claude-api` if Anthropic SDK code is involved.

4. After each file, verify:

   ```bash
   uv run ruff check [file]
   uv run mypy [file]
   uv run pytest [test_file]
   ```

## Workflow

```text
write test → run test (fails) → implement → run test (passes) → refactor → commit
```

## Verification checklist

Before marking complete:

- [ ] All new code has type hints (enforced by ruff `ANN` rules).
- [ ] All public functions, classes, and methods have Google-style docstrings (enforced by ruff `D` rules).
- [ ] Tests cover happy path and edge cases.
- [ ] `uv run ruff check src/` passes.
- [ ] `uv run mypy src/` passes.
- [ ] `uv run pytest -m "not integration"` passes.
- [ ] No credentials or secrets committed.
- [ ] No debug `print` statements or commented-out code.

## Output

After implementation, provide:

1. Summary of changes.
2. Test results.
3. Follow-up items, if any.
````

- [ ] **Step 8: Create `.claude/commands/review.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/commands/review.md`:

````markdown
# Review Command

Review the code: $ARGUMENTS

## Instructions

If a `code-reviewer` agent is available, delegate to it. Otherwise, perform the review inline.

If no specific files are mentioned, review recently modified files:

```bash
git diff --name-only HEAD~1
```

## Review scope

1. **Code Quality**
   - Type hints (ruff `ANN` rules).
   - Google-style docstrings (ruff `D` rules).
   - Error handling matches the project's two-layer policy.
   - Code organization aligns with module responsibilities in `CLAUDE.md`.

2. **MCP patterns**
   - Tool definitions use `@mcp.tool()` decorators with full type annotations.
   - Tools retrieve dependencies via `lifespan_context`, not module-level globals.
   - Tools shape responses for AI consumption (trimmed fields, structured "not found").

3. **Jama client patterns**
   - Operations are async methods on `JamaClient`.
   - Errors mapped to typed `Jama*Error` exceptions.
   - Retry policy applied only where specified.
   - Pydantic models with `extra="allow"` for forward compatibility.

4. **Security**
   - No credentials in code.
   - No injection vulnerabilities.
   - Logging redacts secrets.
   - Token cache values never logged.

5. **Testing**
   - Unit tests use `respx` for HTTP mocking.
   - Integration tests are gated by `pytest -m integration`.
   - Test names describe behavior, not implementation.

## Output format

```markdown
## Code Review: [file/feature]

### Assessment: [APPROVED / NEEDS CHANGES]

### Issues Found

| Severity | Location | Issue | Fix |
|----------|----------|-------|-----|
| Critical | file:line | description | fix |

### Recommendations

- [Optional improvements.]
```
````

- [ ] **Step 9: Create `.claude/commands/test.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/commands/test.md`:

````markdown
# Test Command

Write tests for: $ARGUMENTS

## Instructions

1. Create pytest tests following the AAA pattern:
   - **Arrange:** set up test data and mocks.
   - **Act:** call the function under test.
   - **Assert:** verify expected outcomes.

2. Test file location:
   - Unit tests: `tests/unit/<package>/test_<module>.py`.
   - Integration tests: `tests/integration/test_<feature>.py` with `@pytest.mark.integration`.
   - Protocol tests: `tests/unit/jama_mcp_server/test_protocol.py`.

3. Use shared fixtures from `tests/conftest.py`.

4. Mock external dependencies:
   - HTTP calls: `respx` (mocks `httpx.AsyncClient`).
   - `JamaClient` (in MCP tool tests): inject via `lifespan` context.

## Test categories

### Unit tests

```python
async def test_function_happy_path(respx_mock):
    respx_mock.get("https://example.com/api/x").respond(200, json={...})
    result = await function(input)
    assert result == expected


async def test_function_handles_404(respx_mock):
    respx_mock.get("https://example.com/api/x").respond(404)
    with pytest.raises(JamaNotFoundError):
        await function(input)
```

### Integration tests

```python
@pytest.mark.integration
async def test_real_jama_whoami(jama_client):
    user = await jama_client.get_current_user()
    assert user.id > 0
```

## Coverage targets

- `jama_client`: at least 80 percent line coverage.
- `jama_mcp_server`: every error class triggered at least once.

Run with:

```bash
uv run pytest -m "not integration" --cov=src --cov-report=term-missing
```

## Output

After writing tests:

1. List test functions created.
2. Run tests; show results.
3. Show coverage delta if applicable.
````

- [ ] **Step 10: Create `.claude/commands/memory-audit.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/commands/memory-audit.md`:

````markdown
# Memory Audit Command

Run the memory-hygiene skill against the project's memory files.

## Instructions

1. Invoke the `memory-hygiene` skill defined at `.claude/skills/memory-hygiene/SKILL.md`.

2. Apply the audit checklist:
   - Check for stale file references in `CLAUDE.md` and `MEMORY.md`.
   - Verify architecture sections match the actual codebase.
   - Update recent decisions/PRs (keep last 5–10).
   - Check line counts against caps (CLAUDE.md ~150, MEMORY.md ~100).
   - Verify patterns are still valid.
   - Verify phase pointer accuracy.

3. Audit BOTH memory tiers:
   - Public (in repo): `CLAUDE.md`, `MEMORY.md`.
   - Private (per-user): `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/CLAUDE.md` and `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/memory/MEMORY.md`.

4. Report findings per the skill's "Output" section.

## When to use

Trigger this command after:

- Merging a PR that changes architecture, conventions, or core file paths.
- Completing a development phase.
- Deleting modules or significant code.
- Detecting stale Claude suggestions.
- Approaching memory auto-compaction.

## Related

- `.claude/skills/memory-hygiene/SKILL.md` — the underlying audit checklist.
- `~/.claude/CLAUDE.md` — the author's global Knowledge Graph Memory Protocol and Phase Handoff Protocol.
````

- [ ] **Step 11: Create `.claude/commands/pre-compact.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/commands/pre-compact.md`:

````markdown
# Pre-Compaction Command

Prepare for memory auto-compaction by persisting any unwritten findings.

## Instructions

Execute the Pre-Compaction Protocol from the author's global `~/.claude/CLAUDE.md`:

1. **Persist unwritten findings to the Knowledge Graph.** Review the current session for:
   - Debugging insights that took significant effort.
   - Architectural decisions with rationale.
   - Cross-project patterns or gotchas.
   - User corrections (prefix observation with `Corrected YYYY-MM-DD:`).
   - Dependency relationships.

   For each, call the `memory` MCP server's `create_entities`, `add_observations`, or `create_relations` tools to write the finding into the Neo4j-backed Knowledge Graph.

2. **Update `MEMORY.md`** with the current task state:
   - Active phase.
   - Active branch.
   - Current task or in-progress work.
   - Open questions or decisions awaiting input.

3. **Verify CLAUDE.md and MEMORY.md line counts** are within caps (CLAUDE.md ~150, MEMORY.md ~100). Consolidate if over.

4. **Run `/memory-audit`** to perform the full hygiene checklist.

## Output

Report:

1. Knowledge Graph entities created or updated.
2. MEMORY.md sections updated.
3. CLAUDE.md and MEMORY.md current line counts.
4. Any pending work that should be resumed in the next session.

## Related

- `~/.claude/CLAUDE.md` — Pre-Compaction Protocol section.
- `.claude/commands/memory-audit.md` — full hygiene audit.
````

- [ ] **Step 12: Create `.claude/commands/phase-handoff.md`**

Write the following content to `/Users/arthurfantaci/jama-mcp-server/.claude/commands/phase-handoff.md`:

````markdown
# Phase Handoff Command

Execute the Phase Handoff Protocol when transitioning between development phases.

## Instructions

Execute the Phase Handoff Protocol from the author's global `~/.claude/CLAUDE.md`:

1. **Merge the phase's PR** to `main`.

2. **Clean up branches** for the completed phase:

   ```bash
   git branch --merged main | grep -v 'main' | xargs -n 1 git branch -d
   git remote prune origin
   ```

3. **Verify tests pass** on `main`:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/
   uv run pytest -m "not integration"
   ```

4. **Update `MEMORY.md`** to reflect:
   - The newly completed phase status.
   - The newly active phase.
   - The current working branch (likely `main` after handoff).
   - Recent decisions worth remembering.

5. **Update `CLAUDE.md`** if the completed phase introduced:
   - New conventions worth codifying.
   - New module paths worth referencing.
   - Resolved gotchas no longer needing mention.

6. **Run `/memory-audit`** to audit for stale references introduced by the phase change.

7. **Persist phase-completion observations to the Knowledge Graph** via the `memory` MCP server.

## Output

Report:

1. PR merged.
2. Branches deleted.
3. Test results.
4. MEMORY.md and CLAUDE.md updates summary.
5. Memory audit findings.
6. Knowledge Graph updates.

## Related

- `~/.claude/CLAUDE.md` — Phase Handoff Protocol section.
- `.claude/commands/memory-audit.md` — full hygiene audit.
- `.claude/commands/pre-compact.md` — sibling command for auto-compaction prep.
````

- [ ] **Step 13: Verify the validate-docs-placement hook is executable and well-formed**

Run: `cd /Users/arthurfantaci/jama-mcp-server && bash -n .claude/hooks/validate-docs-placement.sh && test -x .claude/hooks/validate-docs-placement.sh && echo OK`

Expected output: `OK`. The first command checks bash syntax; the second verifies the executable bit is set.

- [ ] **Step 14: Verify `.claude/settings.json` parses**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run --frozen python -c "import json; json.load(open('.claude/settings.json')); print('OK')"`

Expected output: `OK`.

---

## Task 11: Synchronize dependencies and run full verification suite

This task confirms the entire scaffolding works as a coherent whole before committing.

- [ ] **Step 1: Run `uv sync` to materialize the dev environment**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv sync --extra dev`

Expected: a `.venv/` directory is created, dependencies are installed, `uv.lock` is updated. Final line resembles `Installed N packages in <time>`.

- [ ] **Step 2: Run ruff lint**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run ruff check .`

Expected output: `All checks passed!` and exit code 0.

If failures appear, inspect each one. Common issues during scaffolding:

- Missing `from __future__ import annotations` — add to any file using string-form forward references.
- Missing trailing newline — re-save the file.
- Unused imports — remove or add `# noqa: F401` if intentional.

- [ ] **Step 3: Run ruff format check**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run ruff format --check .`

Expected output: `N files already formatted` and exit code 0.

If files need formatting, run `uv run ruff format .` to auto-format and re-run the check.

- [ ] **Step 4: Run mypy strict on `src/`**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run mypy src/`

Expected output: `Success: no issues found in N source files` and exit code 0.

If failures appear, inspect each one. Common issues during scaffolding:

- Functions without return-type annotations — add `-> None` or the appropriate return type.
- Untyped function arguments — add type hints.

- [ ] **Step 5: Run pytest (unit and protocol tests; integration suite excluded)**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run pytest -m "not integration"`

Expected output: `4 passed in <time>` and exit code 0. The four passing tests are the smoke tests defined in `tests/test_smoke.py`.

If pytest reports `5 passed` or another count, verify no extra test files were created accidentally.

- [ ] **Step 6: Install pre-commit hooks**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run pre-commit install`

Expected output: `pre-commit installed at .git/hooks/pre-commit`. Note: pre-commit requires a git repository, so this step also implicitly verifies that `git init` (from Task 12) has run. If it has not yet, defer this step until after Task 12 Step 1.

- [ ] **Step 7: Run all pre-commit hooks against all files**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run pre-commit run --all-files`

Expected: every hook reports `Passed`. If any hook reports `Failed`, inspect the output, fix the issue, and re-run.

The `validate-docs-placement` hook will run only if there are staged docs/*.md files matching its filter; during `--all-files`, it sees all docs files and validates them. Expected: no warnings.

The `gitleaks` hook scans for secret patterns. Expected: no findings.

If pre-commit reports failures during the first run that are auto-fixable (whitespace, ruff fixes), pre-commit modifies the files and exits non-zero. Run the hooks a second time; they should now pass.

---

## Task 12: Initialize git repository and create the inception commit

**Pre-requisite:** Tasks 1–11 are complete and all verification steps pass.

- [ ] **Step 1: Initialize the git repository on the `main` branch**

Run: `cd /Users/arthurfantaci/jama-mcp-server && git init -b main`

Expected output: `Initialized empty Git repository in /Users/arthurfantaci/jama-mcp-server/.git/` and the default branch is `main`.

- [ ] **Step 2: Re-run pre-commit install (if not already run in Task 11)**

Run: `cd /Users/arthurfantaci/jama-mcp-server && uv run pre-commit install`

Expected output: `pre-commit installed at .git/hooks/pre-commit`.

- [ ] **Step 3: Stage all scaffolding files**

Run: `cd /Users/arthurfantaci/jama-mcp-server && git add .`

Expected: no error output. The staging area now contains every tracked file in the repository.

- [ ] **Step 4: Verify the staged file list does not include unintended files**

Run: `cd /Users/arthurfantaci/jama-mcp-server && git status --short`

Expected: a list of `A` (added) entries for every file created in Tasks 1–10, plus this plan file and the design spec. The list should NOT include `.env`, `uv.lock` (wait, `uv.lock` IS tracked — see below), `.venv/`, `.mypy_cache/`, `.ruff_cache/`, or `.pytest_cache/`.

Note: `uv.lock` IS tracked by design (it pins reproducible dependency versions). Verify it appears in the staged list.

If unintended files appear, halt and inspect `.gitignore` for missing entries.

- [ ] **Step 5: Create the inception commit**

Run:

```bash
cd /Users/arthurfantaci/jama-mcp-server && git commit -m "$(cat <<'EOF'
chore: phase 0 — initialize repository scaffolding

Scaffold the Jama MCP Server repository per the Phase 0 plan:

- Two-layer Python package structure under src/ (jama_client and jama_mcp_server)
  with importable skeletons; no implementation yet (Phase 1 lands the logic).
- Build configuration: pyproject.toml with hatchling, uv lockfile, Python 3.12
  target, console scripts (jama-mcp-stdio, jama-mcp-http).
- Tooling rigor: ruff (21 rule families, Google docstring convention), mypy
  strict mode (blocking CI check), pytest with asyncio_mode=auto.
- Test scaffolding: unit/integration/protocol tier directories, smoke tests
  verifying skeleton imports, integration-suite skip-when-no-creds fixture.
- Pre-commit: ruff, mypy, gitleaks, validate-docs-placement, standard hygiene.
- CI: GitHub Actions with lint, test, type-check, dependency-review jobs.
- Memory hygiene apparatus: CLAUDE.md, MEMORY.md, .claude/ skill + hook +
  slash commands (memory-audit, pre-compact, phase-handoff).
- Editor configuration: .vscode/ settings, recommended extensions, debug
  launch configurations.
- GitHub configuration: PR template, issue templates, CODEOWNERS, dependabot.
- User documentation: README, CONTRIBUTING, SECURITY, setup guide.
- Design spec and implementation plan committed under
  docs/superpowers/{specs,plans}/.

Phase 0 verifiable end state:
  uv sync && uv run ruff check . && uv run mypy src/ && uv run pytest
  all succeed against the skeleton-only codebase.

Refs: docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md
EOF
)"
```

Expected output: a commit summary line such as `[main (root-commit) <hash>] chore: phase 0 — initialize repository scaffolding` followed by file-count and insertion stats.

If pre-commit hooks fail, inspect the output, fix the issue, re-stage with `git add .`, and re-run the commit (do NOT use `--amend` on a hook failure; create a new commit if the first one was rejected).

- [ ] **Step 6: Verify the commit landed cleanly**

Run: `cd /Users/arthurfantaci/jama-mcp-server && git log --oneline -1 && git status`

Expected:

- `git log` shows one commit with the chore: prefix.
- `git status` reports `nothing to commit, working tree clean`.

---

## Task 13: Create the public GitHub repository and push the inception commit

- [ ] **Step 1: Verify the GitHub repository does not already exist**

Run: `gh repo view arthurfantaci/jama-mcp-server 2>&1 | head -5`

Expected: an error message such as `GraphQL: Could not resolve to a Repository...` indicating the repo does not yet exist.

If the repo already exists, halt and reconcile with the user before proceeding.

- [ ] **Step 2: Create the public GitHub repository**

Run:

```bash
gh repo create arthurfantaci/jama-mcp-server \
    --public \
    --description "Model Context Protocol server providing access to Jamacloud (Jama Connect SaaS) via its REST API." \
    --homepage "https://github.com/arthurfantaci/jama-mcp-server" \
    --source /Users/arthurfantaci/jama-mcp-server \
    --remote origin \
    --push
```

Expected output: a confirmation line such as `Created repository arthurfantaci/jama-mcp-server on GitHub` followed by remote configuration and push progress.

The `--source` flag points to the local repository, `--remote origin` configures the `origin` remote, and `--push` pushes the inception commit immediately.

- [ ] **Step 3: Verify the remote is configured and the commit is pushed**

Run: `cd /Users/arthurfantaci/jama-mcp-server && git remote -v && git log --oneline origin/main`

Expected:

- `git remote -v` shows two `origin` lines (fetch and push) pointing to `https://github.com/arthurfantaci/jama-mcp-server.git` (or `git@github.com:arthurfantaci/jama-mcp-server.git`).
- `git log --oneline origin/main` shows the same inception commit hash that exists locally.

- [ ] **Step 4: Verify the GitHub repository renders correctly**

Run: `gh repo view arthurfantaci/jama-mcp-server --web`

Expected: a browser opens to <https://github.com/arthurfantaci/jama-mcp-server>. Inspect the rendered README, the file tree, the Issues tab (issue templates should be available), and confirm the repository description, homepage, and license are correctly populated.

- [ ] **Step 5: Verify the first CI run succeeds**

Wait approximately 30–60 seconds, then run: `gh run list --limit 1`

Expected: one run with status `completed` and conclusion `success`. If the run is still `in_progress`, wait and re-run the command. If the conclusion is `failure`, run `gh run view --log-failed` to inspect.

The first CI run executes lint, test, and type-check jobs (the dependency-review job runs only on PRs).

- [ ] **Step 6: Update `MEMORY.md` to reflect Phase 0 completion**

Edit `/Users/arthurfantaci/jama-mcp-server/MEMORY.md` to change the Current phase block from "Phase 0 — Initialization (in progress / closing)" to "Phase 0 — Initialization (complete)" and add a new entry to the Recent decisions table:

```markdown
| 2026-04-28 | Phase 0 inception commit pushed to public GitHub | Repository scaffolded; CI green; ready for Phase 1 |
```

Update the Phase status table to mark Phase 0 as `Complete` and Phase 1 as `Active (planned)`.

- [ ] **Step 7: Commit the MEMORY.md update directly to main**

Per the project's repository hygiene rule, documentation-only changes (touching only `MEMORY.md` or `CLAUDE.md`) do not require a separate issue, branch, or PR.

Run:

```bash
cd /Users/arthurfantaci/jama-mcp-server && git add MEMORY.md && git commit -m "docs: mark Phase 0 complete in MEMORY.md" && git push
```

Expected: a second commit lands on `main` and is pushed to GitHub. CI runs again and succeeds.

---

## Self-Review Notes

This section records the plan author's self-review pass against the design specification.

### Spec coverage check

Each design-specification section has at least one task implementing it:

| Spec section | Implementing task |
|-------------|-------------------|
| §1 Project overview | Task 9 (README documents goals, audience, status) |
| §2 Repository visibility & professional portrayal | Tasks 5 (.gitignore), 6 (gitleaks), 8 (PR template), 10 (validate-docs-placement hook), 11 (pre-commit run) |
| §3 Architecture (two-layer split) | Tasks 1 (pyproject packages), 2 (jama_client skeleton), 3 (jama_mcp_server skeleton) |
| §4 Component breakdown | Tasks 2, 3 (file-by-file skeletons match spec) |
| §5 Data flow | Phase 1 deliverable; Phase 0 documents only via skeleton docstrings |
| §6 Error handling policy | Phase 1 deliverable; Phase 0 declares `exceptions.py` placeholder |
| §7 Testing strategy | Task 4 (test skeletons + smoke tests + integration skip-fixture) |
| §8 Tooling rigor | Tasks 1 (ruff/mypy/pytest config), 6 (pre-commit), 7 (.vscode), 8 (CI) |
| §9 Memory hygiene apparatus | Task 10 (CLAUDE.md, MEMORY.md, .claude/) |
| §10 Phase roadmap | Task 9 (README phase status), Task 10 (MEMORY.md phase pointer) |
| §11 Repository hygiene rules | Tasks 5, 6, 10, 11, 12 (gitignore, hooks, conventions, inception commit, MEMORY) |
| §12 Open decisions deferred | Tasks 1, 6 (resolved here: ruff ignore list, gitleaks chosen) |

### Placeholder scan

No `TBD`, `TODO:`, or "implement later" markers in the plan body. Every step contains the literal content the engineer needs.

The `validate-docs-placement` hook would not fire on this plan because:

- No section headers match the forbidden patterns (`open questions`, `todo`, `practice exercises`, `training rubric`, `gap analysis`, `session notes`, `competency checkpoint`).
- The phrase `TODO` appears only inside code blocks (e.g., the hook's grep pattern itself) and in commit-prefix examples, not as a heading or as a `TODO:` line.

### Type and method consistency

The Phase 0 skeletons define only two functions with signatures: `main_stdio() -> NoReturn` and `main_http() -> NoReturn`. Both are referenced consistently in:

- `pyproject.toml` `[project.scripts]` block (Task 1).
- `src/jama_mcp_server/__main__.py` import statement (Task 3).
- `.vscode/launch.json` (which uses `module: jama_mcp_server` and relies on `__main__.py` for dispatch).

The `_dispatch()` helper in `__main__.py` references `MCP_TRANSPORT` consistently with `pyproject.toml`'s console-script declarations and the README's quick-start instructions.

### Scope check

The plan is a single coherent Phase 0 deliverable. It does not bleed into Phase 1 implementation; the only references to Phase 1 are explicit deferral notes in skeleton docstrings and in `MEMORY.md`.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md`.

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. Uses the `superpowers:subagent-driven-development` skill.
2. **Inline Execution** — execute tasks in this session using the `superpowers:executing-plans` skill, batch execution with checkpoints for review.

Which approach?
