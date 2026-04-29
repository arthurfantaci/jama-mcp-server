"""MCP tool definitions for the Jama traceability slice.

This module will define six ``@mcp.tool()``-decorated async functions
mirroring the Phase 1 client operations: ``whoami``, ``list_projects``,
``get_item``, ``search_items``, ``get_downstream_relationships``, and
``get_test_runs_for_item``. Each tool retrieves the shared ``JamaClient``
from the lifespan context and returns AI-shaped dictionaries. Phase 0
contains only this placeholder.
"""
