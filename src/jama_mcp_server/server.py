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
