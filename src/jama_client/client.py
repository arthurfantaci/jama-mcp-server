"""Asynchronous HTTP client for the Jamacloud REST API.

This module will define the ``JamaClient`` async context manager wrapping
``httpx.AsyncClient``. It owns the OAuth token cache, performs response
envelope unwrapping, maps HTTP status codes to typed exceptions, and
implements the narrow retry policy defined in the design specification.
Phase 0 contains only this placeholder.
"""
