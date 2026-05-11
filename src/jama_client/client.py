"""Asynchronous HTTP client for the Jamacloud REST API.

The :class:`JamaClient` class is an async context manager wrapping
``httpx.AsyncClient``, owning the OAuth :class:`TokenCache`, performing
response envelope unwrapping (``meta`` / ``links`` / ``data``), and
mapping HTTP status codes to typed :mod:`jama_client.exceptions`. The
retry policy is the narrow one defined in Section 6 of the design spec.

The client maintains a per-instance ``_type_cache`` dictionary for
discovered type IDs and resource lists (item types, relationship types,
Implementation Code Sets). Cache entries are keyed by project-scoped
strings (e.g. ``item_types_127``) and are never invalidated — instances
are short-lived, typically lasting the duration of one server session.
"""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from types import TracebackType

from jama_client.auth import OAuthCredentials, Token, TokenCache, fetch_token
from jama_client.exceptions import (
    JamaAuthError,
    JamaError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaNotFoundError,
    JamaRateLimitError,
    JamaServerError,
    JamaValidationError,
)
from jama_client.models import (
    Comment,
    Item,
    ItemType,
    Project,
    Relationship,
    RelationshipType,
    TestRun,
    User,
)

_M = TypeVar("_M", bound=BaseModel)

_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_NETWORK_RETRY_LIMIT = 2
_NETWORK_RETRY_BASE_DELAY = 0.5
# Matches a trailing ":N-M" line-range suffix, e.g. ":7-42". Used to strip the
# suffix before deriving a Code item name and to extract start/end lines for URL
# construction. Anchored on "$" so it does not match mid-path colons (ISO
# timestamps, Windows paths, annotated identifiers, etc.).
_LINE_RANGE_RE = re.compile(r":(\d+)-(\d+)$")


class JamaClient:
    """Async client wrapping a curated subset of the Jamacloud REST API."""

    def __init__(
        self,
        creds: OAuthCredentials,
        *,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        """Initialize the client; the underlying HTTP transport opens on ``__aenter__``.

        Args:
            creds: Immutable OAuth credentials (including the ``base_url``).
            timeout: Optional ``httpx.Timeout`` override; defaults to a sensible value.
        """
        self._creds = creds
        self._timeout = timeout or _DEFAULT_TIMEOUT
        self._http: httpx.AsyncClient | None = None
        self._tokens = TokenCache()
        self._type_cache: dict[str, Any] = {}

    @property
    def is_open(self) -> bool:
        """Return ``True`` when the underlying HTTP client is open."""
        return self._http is not None

    async def __aenter__(self) -> JamaClient:
        """Open the underlying ``httpx.AsyncClient``."""
        self._http = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the underlying ``httpx.AsyncClient`` and clear the token cache."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        self._tokens.clear()

    async def _ensure_token(self) -> Token:
        """Return a valid token, refreshing proactively at or above 90 percent of TTL."""
        now = datetime.now(tz=UTC)
        cached = self._tokens.get(now=now)
        if cached is not None:
            return cached
        if self._http is None:
            msg = "JamaClient must be used as an async context manager."
            raise RuntimeError(msg)
        token = await fetch_token(self._creds, self._http)
        self._tokens.set(token)
        return token

    async def get_current_user(self) -> User:
        """Return the user identified by the current OAuth credentials.

        Returns:
            A :class:`~jama_client.models.User` populated from the API response.

        Raises:
            JamaValidationError: When the response cannot be validated as a :class:`User`.
        """
        data = await self._request("GET", "/rest/latest/users/current")
        return self._validate(User, data)

    async def list_projects(self) -> list[Project]:
        """Return the first page of accessible Jama projects.

        Pagination metadata (``meta.pageInfo``) is discarded by the default
        envelope-unwrapping behaviour. Phase 2 may revisit pagination by
        passing ``return_envelope=True`` and surfacing ``pageInfo`` to
        callers; for Phase 1 the first page is sufficient for the
        traceability slice.
        """
        data = await self._request("GET", "/rest/latest/projects")
        return [self._validate(Project, item) for item in data]

    async def get_item(self, item_id: int) -> Item:
        """Return a single Jama item by ID.

        Args:
            item_id: The Jama internal item ID.

        Raises:
            JamaNotFoundError: When the item does not exist.
        """
        data = await self._request("GET", f"/rest/latest/items/{item_id}")
        return self._validate(Item, data)

    async def search_items(self, project_id: int, query: str) -> list[Item]:
        """Search Jama items within a project for ``query``.

        Pagination metadata (``meta.pageInfo``) is discarded by the default
        envelope-unwrapping behaviour. Phase 2 may revisit pagination by
        passing ``return_envelope=True`` and surfacing ``pageInfo`` to
        callers; for Phase 1 the first page is sufficient for the
        traceability slice.

        Args:
            project_id: The Jama project ID to scope the search.
            query: Free-text search query (matched against item content).
        """
        data = await self._request(
            "GET",
            "/rest/latest/abstractitems",
            params={"project": project_id, "contains": query},
        )
        return [self._validate(Item, item) for item in data]

    async def get_downstream_relationships(self, item_id: int) -> list[Relationship]:
        """Return downstream relationships originating from ``item_id``.

        Pagination metadata (``meta.pageInfo``) is discarded by the default
        envelope-unwrapping behaviour. Phase 2 may revisit pagination by
        passing ``return_envelope=True`` and surfacing ``pageInfo`` to
        callers; for Phase 1 the first page is sufficient for the
        traceability slice.

        Args:
            item_id: The Jama internal item ID.

        Raises:
            JamaNotFoundError: When the item does not exist.
        """
        data = await self._request(
            "GET",
            f"/rest/latest/items/{item_id}/downstreamrelationships",
        )
        return [self._validate(Relationship, rel) for rel in data]

    async def get_test_runs_for_item(self, item_id: int) -> list[TestRun]:
        """Return test runs for the test case identified by ``item_id``.

        Test runs are records of executing a test case; ``item_id`` should
        therefore be the ID of an item whose item type is a test case. For
        non-test-case items the call returns an empty list.

        Pagination metadata (``meta.pageInfo``) is discarded by the default
        envelope-unwrapping behaviour. Phase 2 may revisit pagination by
        passing ``return_envelope=True`` and surfacing ``pageInfo`` to
        callers; for Phase 1 the first page is sufficient for the
        traceability slice.

        Args:
            item_id: The Jama internal item ID for a test case.
        """
        data = await self._request(
            "GET",
            "/rest/latest/testruns",
            params={"testCase": item_id},
        )
        return [self._validate(TestRun, run) for run in data]

    async def create_comment(
        self,
        item_id: int,
        project_id: int,
        body: str,
        *,
        in_reply_to: int | None = None,
        comment_type: str = "GENERAL",
    ) -> Comment:
        """Create a comment on a Jamacloud item.

        Posts to ``POST /rest/latest/comments`` with the Jama-canonical request
        shape: ``body`` nested under ``{"text": ...}``, ``location`` nested
        under ``{"item": ..., "project": ...}``, and ``commentType`` defaulting
        to ``"GENERAL"``. For top-level comments, ``inReplyTo`` is **omitted
        entirely** (passing ``in_reply_to=0`` triggers a server-side
        ``NullPointerException`` in Jamacloud's parent-comment lookup; verified
        against ``pm2.jamacloud.com`` 2026-05-02).

        Jamacloud's POST response is a ``meta``-only envelope with the new
        comment's ``id`` and ``location`` URL — there is no ``data`` field
        carrying the full comment representation. The returned :class:`Comment`
        is therefore synthesised from the new ID plus the inputs the caller
        already provided; timestamp and author fields are left ``None``. Callers
        that need a fully-populated comment can issue a follow-up GET against
        ``/rest/latest/comments/{id}``.

        Args:
            item_id: The Jama internal ID of the item being commented on.
            project_id: The Jama internal ID of the item's parent project.
                Required by Jama's request schema; obtain from a prior
                ``get_item`` call's ``project`` field or from ``list_projects``.
            body: Plain-text comment body.
            in_reply_to: Parent comment ID for threaded replies; ``None``
                (default) creates a top-level comment by omitting the field.
            comment_type: Jama comment-type enumeration; defaults to ``"GENERAL"``.

        Returns:
            A :class:`Comment` synthesised from the assigned ID plus the request
            inputs. Timestamp and author fields are ``None`` — see method
            docstring for rationale.

        Raises:
            JamaAuthError: HTTP 401 — the OAuth token was rejected.
            JamaForbiddenError: HTTP 403 — the credential lacks comment-create
                permission on the item or project.
            JamaNotFoundError: HTTP 404 — the target item does not exist.
            JamaValidationError: HTTP 400 (request payload rejected by Jama),
                any other unexpected status, or absence of the new comment ID
                from the response envelope.
        """
        payload: dict[str, Any] = {
            "body": {"text": body},
            "commentType": comment_type,
            "location": {"item": item_id, "project": project_id},
        }
        if in_reply_to is not None:
            payload["inReplyTo"] = in_reply_to

        envelope = await self._request(
            "POST",
            "/rest/latest/comments",
            json_body=payload,
            return_envelope=True,
        )
        meta = envelope.get("meta") if isinstance(envelope, dict) else None
        new_id = meta.get("id") if isinstance(meta, dict) else None
        if not isinstance(new_id, int):
            msg = "Jamacloud POST /comments response did not include a new comment ID."
            raise JamaValidationError(msg, payload=envelope)

        return Comment(
            id=new_id,
            in_reply_to=in_reply_to,
            body={"text": body},
            comment_type=comment_type,
            location={"item": item_id, "project": project_id},
        )

    async def list_item_types(self, project_id: int) -> list[ItemType]:
        """Return all item types configured for ``project_id``.

        Anticipates ``GET /rest/latest/projects/{id}/itemtypes`` from
        Jama Connect MCP™. Results are cached per project ID for the
        client instance's lifetime.

        Args:
            project_id: The Jama project ID.

        Returns:
            A list of :class:`~jama_client.models.ItemType` objects.

        Raises:
            JamaNotFoundError: When the project does not exist.
        """
        cache_key = f"item_types_{project_id}"
        cached: list[ItemType] | None = self._type_cache.get(cache_key)
        if cached is not None:
            return cached
        data = await self._request(
            "GET",
            f"/rest/latest/projects/{project_id}/itemtypes",
        )
        result = [self._validate(ItemType, item) for item in data]
        self._type_cache[cache_key] = result
        return result

    async def list_relationship_types(self, project_id: int) -> list[RelationshipType]:
        """Return relationship types available within ``project_id``.

        Anticipates ``GET /rest/latest/relationshiptypes`` scoped by project
        from Jama Connect MCP™. Results are cached per project ID for the
        client instance's lifetime.

        Args:
            project_id: The Jama project ID used for scoping and caching.

        Returns:
            A list of :class:`~jama_client.models.RelationshipType` objects.
        """
        cache_key = f"relationship_types_{project_id}"
        cached: list[RelationshipType] | None = self._type_cache.get(cache_key)
        if cached is not None:
            return cached
        data = await self._request(
            "GET",
            "/rest/latest/relationshiptypes",
            params={"project": project_id},
        )
        result = [self._validate(RelationshipType, rt) for rt in data]
        self._type_cache[cache_key] = result
        return result

    async def list_items_by_type(
        self,
        project_id: int,
        item_type: int,
        *,
        max_items: int = 200,
    ) -> tuple[list[Item], bool]:
        """Return items of ``item_type`` within ``project_id``, up to ``max_items``.

        Anticipates ``GET /rest/latest/abstractitems`` filtered by project and
        item type from Jama Connect MCP™. Paginates internally using Jama's
        ``startIndex`` / ``maxResults`` query parameters; stops when all items
        have been fetched or the ``max_items`` cap is reached.

        Args:
            project_id: The Jama project ID to query.
            item_type: The numeric item type ID to filter on.
            max_items: Maximum number of items to return; defaults to 200.

        Returns:
            A ``(items, max_items_reached)`` tuple where ``max_items_reached``
            is ``True`` when the cap was hit before all results were collected.
        """
        _page_size = 50
        items: list[Item] = []
        start_index = 0
        total_results = 0

        while len(items) < max_items:
            remaining = max_items - len(items)
            envelope = await self._request(
                "GET",
                "/rest/latest/abstractitems",
                params={
                    "project": project_id,
                    "itemType": item_type,
                    "startIndex": start_index,
                    "maxResults": min(_page_size, remaining),
                },
                return_envelope=True,
            )
            page_data: list[Any] = envelope.get("data") or []
            if not page_data:
                break
            items.extend(self._validate(Item, item) for item in page_data)
            page_info: dict[str, Any] = (envelope.get("meta") or {}).get("pageInfo") or {}
            total_results = int(page_info.get("totalResults") or 0)
            if len(items) >= total_results:
                break
            start_index += len(page_data)
        else:
            return items, True

        return items, len(items) < total_results

    async def create_item(
        self,
        project_id: int,
        item_type: int,
        parent: int,
        name: str,
        fields: dict[str, Any] | None = None,
    ) -> Item:
        """Create a new Jama item of ``item_type`` inside ``parent``.

        Anticipates ``POST /rest/latest/items`` from Jama Connect MCP™.
        Follows the Phase 4.5 meta-only response envelope pattern: Jamacloud
        returns a ``meta``-only envelope with the new item's ``id`` and
        ``location``; the returned :class:`~jama_client.models.Item` is
        synthesised from the assigned ID plus the request inputs.

        Args:
            project_id: The Jama project ID.
            item_type: The numeric item type ID for the new item.
            parent: The Jama item ID of the parent Set or container item.
            name: The ``name`` field value for the new item.
            fields: Optional additional field key/value pairs to set on the
                item (merged with ``{"name": name}`` before submission).

        Returns:
            A :class:`~jama_client.models.Item` synthesised from the assigned
            ID plus the request inputs. Timestamp and relational fields are
            ``None`` — issue a follow-up ``get_item`` call for a fully-populated
            representation.

        Raises:
            JamaAuthError: HTTP 401.
            JamaForbiddenError: HTTP 403 — credential lacks item-create
                permission on the project.
            JamaNotFoundError: HTTP 404 — ``parent`` or ``project_id`` does
                not exist.
            JamaValidationError: HTTP 400 (request payload rejected by Jama),
                any other unexpected status, or absence of the new item ID
                from the response envelope.
        """
        item_fields: dict[str, Any] = {"name": name}
        if fields:
            item_fields.update(fields)

        payload: dict[str, Any] = {
            "project": project_id,
            "itemType": item_type,
            "location": {"parent": {"item": parent}},
            "fields": item_fields,
        }
        envelope = await self._request(
            "POST",
            "/rest/latest/items",
            json_body=payload,
            return_envelope=True,
        )
        meta = envelope.get("meta") if isinstance(envelope, dict) else None
        new_id = meta.get("id") if isinstance(meta, dict) else None
        if not isinstance(new_id, int):
            msg = "Jamacloud POST /items response did not include a new item ID."
            raise JamaValidationError(msg, payload=envelope)

        return Item(
            id=new_id,
            item_type=item_type,
            project=project_id,
            fields=item_fields,
        )

    async def create_relationship(
        self,
        from_item: int,
        to_item: int,
        relationship_type: int,
    ) -> Relationship:
        """Create a directed relationship between two existing Jama items.

        Anticipates ``POST /rest/latest/relationships`` from Jama Connect MCP™.
        Follows the Phase 4.5 meta-only response envelope pattern. The returned
        :class:`~jama_client.models.Relationship` is synthesised from the
        assigned ID plus the request inputs.

        Args:
            from_item: The Jama item ID of the source (upstream) endpoint.
            to_item: The Jama item ID of the target (downstream) endpoint.
            relationship_type: The numeric relationship type ID.

        Returns:
            A :class:`~jama_client.models.Relationship` synthesised from the
            assigned ID plus the request inputs.

        Raises:
            JamaAuthError: HTTP 401.
            JamaForbiddenError: HTTP 403.
            JamaNotFoundError: HTTP 404 — either item does not exist.
            JamaValidationError: HTTP 400, or absence of new relationship ID.
        """
        payload: dict[str, Any] = {
            "fromItem": from_item,
            "toItem": to_item,
            "relationshipType": relationship_type,
        }
        envelope = await self._request(
            "POST",
            "/rest/latest/relationships",
            json_body=payload,
            return_envelope=True,
        )
        meta = envelope.get("meta") if isinstance(envelope, dict) else None
        new_id = meta.get("id") if isinstance(meta, dict) else None
        if not isinstance(new_id, int):
            msg = "Jamacloud POST /relationships response did not include a new relationship ID."
            raise JamaValidationError(msg, payload=envelope)

        return Relationship(
            id=new_id,
            from_item=from_item,
            to_item=to_item,
            relationship_type=relationship_type,
        )

    async def create_path_a_trace(
        self,
        project_id: int,
        source_requirement_key: str,
        code_path: str,
        code_version: str,
        *,
        repo_origin: str | None = None,
        name: str | None = None,
        code_set_id: int | None = None,
        code_item_type: int | None = None,
        relationship_type: int | None = None,
    ) -> dict[str, Any]:
        """Create a Path A trace link from a source requirement to a new Code item.

        Workflow tool — composes core primitives; NOT expected in Jama Connect
        MCP™. High-level workflow that, given a source requirement document key,
        a code file path, and a code version string:

        1. Validates the source requirement exists (raises
           :class:`~jama_client.exceptions.JamaNotFoundError` before any write
           if the key cannot be resolved).
        2. Resolves the Code item type by ``typeKey == "CODE"`` when
           ``code_item_type`` is omitted; caches the result.
        3. Resolves the "Implemented by" relationship type by name when
           ``relationship_type`` is omitted; caches the result.
        4. Resolves the Implementation Code Set by case-insensitive substring
           match on ``"Implementation Code"`` when ``code_set_id`` is omitted;
           caches the result. Raises :class:`~jama_client.exceptions.JamaNotFoundError`
           when no match or multiple matches are found without an explicit ID.
        5. Creates the Code item. The ``name`` defaults to the basename of
           ``code_path`` with any trailing ``:N-M`` line-range suffix stripped
           (e.g. ``"src/client.py:7-42"`` → ``"client.py"``); mid-path colons
           (ISO timestamps, Windows-style paths, annotated identifiers) are
           preserved. When ``repo_origin`` is supplied, populates the item's
           ``description`` field with an HTML-formatted deep link to the
           tagged code (see ``repo_origin`` parameter description below). The
           HTML wrapping is required because Jama's Type 114 ``description``
           field is RICHTEXT-typed and silently drops plain-text content.
        6. Creates the "Implemented by" relationship from the source requirement
           to the new Code item.

        ``source_requirement_key`` accepts a Jama document key (e.g.
        ``"AF-SUBSS-25"``), which this method resolves to a numeric ID
        internally. By contrast, ``create_item`` and ``create_relationship``
        accept numeric IDs only; callers composing those primitives directly
        must resolve keys themselves.

        Args:
            project_id: The Jama project ID containing the source requirement
                and the target Implementation Code Set.
            source_requirement_key: The document key (e.g. ``"AF-SUBSS-25"``)
                of the source requirement. Resolved to a numeric ID internally
                — callers do not need a prior ``search_items`` call.
            code_path: File path string stored in the Code item's
                ``path$<typeId>`` field (e.g.
                ``"src/detection/detector.py:7-42"``). A trailing ``:N-M``
                suffix is recognised as a line range; any other colon is
                treated as part of the path.
            code_version: Version string stored in the Code item's
                ``code_version$<typeId>`` field (e.g. ``"v1.0.0-rc1"``).
            repo_origin: Optional ``<host>/<owner>/<repo>`` string identifying
                the source repository, e.g.
                ``"github.com/arthurfantaci/jama-mcp-server"``. No leading
                scheme; ``https://`` is prepended when constructing the deep
                link. When supplied, the Code item's ``description`` field is
                populated with an HTML payload of the form:

                .. code-block:: html

                    <p>Repository: <repo_origin><br>
                    Version: <code_version><br>
                    Path: <path-without-line-range> (lines N-M)<br>
                    Link: <a href="<url>"><url></a></p>

                where ``<url>`` is
                ``https://<repo_origin>/blob/<code_version>/<path>#LN-LM``.
                The ``Path:`` line omits the ``(lines N-M)`` annotation and
                the URL omits the ``#LN-LM`` fragment when no line range is
                present in ``code_path``. The link is wrapped in an explicit
                ``<a href>`` so it is clickable in Jama's UI regardless of
                tenant link-detection settings. When ``None`` (default), no
                ``description`` field is set on the Code item.
            name: Optional override for the Code item's ``name`` field.
                Defaults to the basename of ``code_path`` with any trailing
                ``:N-M`` line-range suffix stripped.
            code_set_id: Optional explicit parent Set ID for the new Code item.
                When omitted, the Set is resolved by name.
            code_item_type: Optional explicit item type ID for Code items.
                When omitted, resolved by ``typeKey == "CODE"``.
            relationship_type: Optional explicit relationship type ID.
                When omitted, resolved by name ``"Implemented by"``.

        Returns:
            A dict with ``source_item_id``, ``code_item_id``, and
            ``relationship_id`` keys.

        Raises:
            JamaNotFoundError: When the source requirement, Code item type,
                "Implemented by" relationship type, or Implementation Code Set
                cannot be resolved.
            JamaValidationError: When item or relationship creation fails.
        """
        source = await self._find_item_by_key(project_id, source_requirement_key)

        resolved_code_item_type = (
            code_item_type
            if code_item_type is not None
            else await self._resolve_code_item_type(project_id)
        )
        resolved_rel_type = (
            relationship_type
            if relationship_type is not None
            else await self._resolve_implemented_by_rel_type(project_id)
        )
        resolved_code_set_id = (
            code_set_id
            if code_set_id is not None
            else await self._resolve_implementation_code_set(project_id)
        )

        stripped_path = _LINE_RANGE_RE.sub("", code_path)
        derived_name = name if name is not None else Path(stripped_path).name

        code_fields: dict[str, Any] = {
            f"path${resolved_code_item_type}": code_path,
            f"code_version${resolved_code_item_type}": code_version,
        }
        if repo_origin is not None:
            range_match = _LINE_RANGE_RE.search(code_path)
            if range_match:
                start_line, end_line = range_match.group(1), range_match.group(2)
                path_line = f"Path: {stripped_path} (lines {start_line}-{end_line})"
                link = (
                    f"https://{repo_origin}/blob/{code_version}"
                    f"/{stripped_path}#L{start_line}-L{end_line}"
                )
            else:
                path_line = f"Path: {stripped_path}"
                link = f"https://{repo_origin}/blob/{code_version}/{stripped_path}"
            code_fields["description"] = (
                f"<p>Repository: {repo_origin}<br>"
                f"Version: {code_version}<br>"
                f"{path_line}<br>"
                f'Link: <a href="{link}">{link}</a></p>'
            )

        code_item = await self.create_item(
            project_id=project_id,
            item_type=resolved_code_item_type,
            parent=resolved_code_set_id,
            name=derived_name,
            fields=code_fields,
        )

        relationship = await self.create_relationship(
            from_item=source.id,
            to_item=code_item.id,
            relationship_type=resolved_rel_type,
        )

        return {
            "source_item_id": source.id,
            "code_item_id": code_item.id,
            "relationship_id": relationship.id,
        }

    async def _find_item_by_key(self, project_id: int, key: str) -> Item:
        """Locate a single item by its document key within ``project_id``.

        Args:
            project_id: The Jama project ID to scope the lookup.
            key: The exact document key (e.g. ``"AF-SUBSS-25"``).

        Returns:
            The matching :class:`~jama_client.models.Item`.

        Raises:
            JamaNotFoundError: When no item with the given key exists in the
                project.
        """
        data = await self._request(
            "GET",
            "/rest/latest/abstractitems",
            params={"project": project_id, "documentKey": key},
        )
        items: list[Any] = data if isinstance(data, list) else []
        if not items:
            msg = f"No Jama item found with document key '{key}' in project {project_id}."
            raise JamaNotFoundError(msg)
        return self._validate(Item, items[0])

    async def _resolve_code_item_type(self, project_id: int) -> int:
        """Return the numeric ID of the ``CODE`` item type in ``project_id``.

        Caches the result under ``code_item_type_{project_id}``.

        Raises:
            JamaNotFoundError: When no item type with ``typeKey == "CODE"``
                exists in the project.
        """
        cache_key = f"code_item_type_{project_id}"
        cached: int | None = self._type_cache.get(cache_key)
        if cached is not None:
            return cached
        item_types = await self.list_item_types(project_id)
        for it in item_types:
            if it.type_key == "CODE":
                self._type_cache[cache_key] = it.id
                return it.id
        msg = f"No item type with typeKey 'CODE' found in project {project_id}."
        raise JamaNotFoundError(msg)

    async def _resolve_implemented_by_rel_type(self, project_id: int) -> int:
        """Return the numeric ID of the ``"Implemented by"`` relationship type.

        Caches the result under ``rel_type_implemented_by_{project_id}``.

        Raises:
            JamaNotFoundError: When no relationship type named ``"Implemented by"``
                exists.
        """
        cache_key = f"rel_type_implemented_by_{project_id}"
        cached: int | None = self._type_cache.get(cache_key)
        if cached is not None:
            return cached
        rel_types = await self.list_relationship_types(project_id)
        for rt in rel_types:
            if rt.name == "Implemented by":
                self._type_cache[cache_key] = rt.id
                return rt.id
        msg = f"No relationship type named 'Implemented by' found in project {project_id}."
        raise JamaNotFoundError(msg)

    async def _resolve_implementation_code_set(self, project_id: int) -> int:
        """Return the item ID of the Implementation Code Set in ``project_id``.

        Queries Sets (item type 31) and picks the one whose ``name`` field
        contains ``"implementation code"`` (case-insensitive substring match).
        Caches the result under ``code_set_{project_id}``.

        Raises:
            JamaNotFoundError: When no matching Set exists, or when multiple
                Sets match without an explicit ``code_set_id`` override.
        """
        cache_key = f"code_set_{project_id}"
        cached: int | None = self._type_cache.get(cache_key)
        if cached is not None:
            return cached
        sets, _ = await self.list_items_by_type(project_id, item_type=31, max_items=200)
        matches = [
            s for s in sets if "implementation code" in str(s.fields.get("name") or "").lower()
        ]
        if not matches:
            msg = (
                f"No Set named 'Implementation Code' (case-insensitive substring) "
                f"found in project {project_id}. Pass code_set_id explicitly."
            )
            raise JamaNotFoundError(msg)
        if len(matches) > 1:
            ids = [s.id for s in matches]
            msg = (
                f"Multiple Sets matching 'Implementation Code' found in project "
                f"{project_id} (IDs: {ids}). Pass code_set_id explicitly."
            )
            raise JamaNotFoundError(msg)
        self._type_cache[cache_key] = matches[0].id
        return matches[0].id

    @staticmethod
    def _validate(model_cls: type[_M], payload: Any) -> _M:
        """Validate an API payload as ``model_cls``, translating failures to JamaValidationError.

        Args:
            model_cls: The Pydantic model class to validate against.
            payload: The raw API payload (typically a ``dict``).

        Returns:
            A validated instance of ``model_cls``.

        Raises:
            JamaValidationError: When the payload fails Pydantic validation.
        """
        try:
            return model_cls.model_validate(payload)
        except (ValidationError, TypeError, ValueError) as exc:
            msg = f"Failed to validate {model_cls.__name__} response."
            raise JamaValidationError(msg, payload=payload) from exc

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        return_envelope: bool = False,
    ) -> Any:
        """Issue an authenticated request against the Jamacloud API.

        Args:
            method: HTTP verb.
            path: Path under the configured ``base_url`` (must start with ``/``).
            params: Optional query parameters.
            json_body: Optional JSON request body (serialised by ``httpx``;
                ``Content-Type: application/json`` is set automatically).
            return_envelope: When ``True`` returns the full ``{meta,links,data}`` envelope;
                otherwise returns just the unwrapped ``data`` field.

        Returns:
            Parsed JSON ``data`` field by default, or the full envelope when requested.

        Raises:
            JamaAuthError: The API returned HTTP 401.
            JamaForbiddenError: The API returned HTTP 403.
            JamaNotFoundError: The API returned HTTP 404.
            JamaRateLimitError: The API rate-limited the request and retry was exhausted.
            JamaServerError: The API returned a 5xx status and retry was exhausted.
            JamaNetworkError: A transport-level failure occurred after retries.
            JamaValidationError: The response body failed envelope validation.
            RuntimeError: When invoked outside the async context manager.
        """
        if self._http is None:
            msg = "JamaClient must be used as an async context manager."
            raise RuntimeError(msg)

        url = f"{self._creds.base_url.rstrip('/')}{path}"

        rate_retried = False
        server_retried = False
        network_attempt = 0

        while True:
            token = await self._ensure_token()
            headers = {"Authorization": f"Bearer {token.access_token}"}
            try:
                response = await self._http.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=headers,
                )
            except httpx.HTTPError as exc:
                if network_attempt < _NETWORK_RETRY_LIMIT:
                    network_attempt += 1
                    await asyncio.sleep(_NETWORK_RETRY_BASE_DELAY * (2 ** (network_attempt - 1)))
                    continue
                msg = f"Network failure contacting Jamacloud: {exc!r}"
                raise JamaNetworkError(msg) from exc

            status = response.status_code

            if status in (200, 201):
                return self._parse_envelope(response, return_envelope=return_envelope)

            if status == 429:
                if not rate_retried:
                    rate_retried = True
                    retry_after = self._parse_retry_after(response)
                    await asyncio.sleep(retry_after)
                    continue
                msg = "Jamacloud rate limit exceeded after retry."
                raise JamaRateLimitError(msg, retry_after=self._parse_retry_after(response))

            if 500 <= status < 600:
                if not server_retried:
                    server_retried = True
                    continue
                msg = f"Jamacloud returned HTTP {status}."
                raise JamaServerError(msg)

            self._raise_for_status(status)

    @staticmethod
    def _parse_envelope(response: httpx.Response, *, return_envelope: bool) -> Any:
        """Parse and unwrap a Jamacloud response envelope.

        Args:
            response: The raw ``httpx.Response`` to parse.
            return_envelope: When ``True`` return the full payload dict; otherwise
                return only the ``data`` field.

        Returns:
            The unwrapped ``data`` value or the full envelope dict.

        Raises:
            JamaValidationError: When the body is not a JSON object, or when the
                caller asked for unwrapped ``data`` and the envelope does not
                include a ``data`` key. Some write endpoints (notably
                ``POST /rest/latest/comments``) return a ``meta``-only envelope
                with the new resource's ``id`` and ``location`` but no ``data``;
                callers of those endpoints must pass ``return_envelope=True``.
        """
        try:
            payload = response.json()
        except ValueError as exc:
            msg = "Jamacloud response was not valid JSON."
            raise JamaValidationError(msg, payload=response.text) from exc
        if not isinstance(payload, dict):
            msg = "Jamacloud response was not a JSON object."
            raise JamaValidationError(msg, payload=payload)
        if return_envelope:
            return payload
        if "data" not in payload:
            msg = "Jamacloud response missing expected meta/links/data envelope."
            raise JamaValidationError(msg, payload=payload)
        return payload["data"]

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> int:
        """Extract the ``Retry-After`` header value in seconds.

        Args:
            response: The ``httpx.Response`` carrying the header.

        Returns:
            Integer seconds to wait; defaults to 1 if the header is absent or invalid.
        """
        raw = response.headers.get("Retry-After", "1")
        try:
            return max(0, int(raw))
        except ValueError:
            return 1

    @staticmethod
    def _raise_for_status(status: int) -> NoReturn:
        """Raise a typed exception for a non-success, non-retried HTTP status code.

        Args:
            status: The HTTP status code to map.

        Raises:
            JamaAuthError: For HTTP 401.
            JamaForbiddenError: For HTTP 403.
            JamaNotFoundError: For HTTP 404.
            JamaValidationError: For any other unexpected status code.
        """
        mapping: dict[int, type[JamaError]] = {
            401: JamaAuthError,
            403: JamaForbiddenError,
            404: JamaNotFoundError,
        }
        exc_cls = mapping.get(status)
        if exc_cls is not None:
            raise exc_cls(f"Jamacloud returned HTTP {status}.")
        msg = f"Jamacloud returned unexpected HTTP {status}."
        raise JamaValidationError(msg)
