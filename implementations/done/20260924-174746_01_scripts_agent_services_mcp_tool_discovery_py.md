# Implementation Procedure: Extract classes and refactor mcp_tool_discovery.py

## Goal

Decompose `McpToolDiscoveryService` into bounded-context classes to reduce method complexity, improve testability, and consolidate severity classification logic — without changing external behavior. REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007, REQ-008.

## Scope

- Extract `McpToolsHttpClient` class (REQ-001)
- Extract `ToolEntryValidator` class (REQ-002)
- Separate duplicate detection from RuntimeTool construction in `_dedupe_and_build()` (REQ-003)
- Consolidate severity classification into `SeverityClassifier` (REQ-004)
- Extract `/v1/tools` path to module-level constant (REQ-006)
- Preserve all public APIs and behavior (REQ-007, REQ-008)

## Assumptions

- `RuntimeToolRegistry.__init__()`'s `_is_excluded_server()` behavior is correct and sufficient for excluding unreachable server tools — no additional filtering needed beyond passing `unavailable_servers`
- The "always FATAL for duplicates" exception to the `is_fatal = strict` scheme is intentional and should be preserved as a documented exception in the SeverityClassifier
- `httpx.AsyncClient` can be injected into `McpToolsHttpClient` for testability without breaking existing usage patterns
- All existing tests pass before refactoring (behavior-lock baseline)

## Design decisions

**Decision 1**: Keep extracted classes nested inside `mcp_tool_discovery.py` initially. Rationale: The issue's unresolved question (UNK-01) has no clear answer yet. Keeping them nested preserves visibility of coupling between the service and its helpers. If reuse emerges later, extraction to a standalone module is straightforward.

**Decision 2**: Inject `httpx.AsyncClient` into `McpToolsHttpClient`. Rationale: Testability requires controlling HTTP transport. The existing code creates clients internally via `self._ctx.services_required.http`, which is mockable but less explicit. Injection makes the dependency boundary clear.

**Decision 3**: Preserve the "always FATAL for duplicates" exception in SeverityClassifier. Rationale: The module docstring (lines 32-34) explicitly documents this as intentional — a duplicated tool is unusable, so there is no WARNING-only case. Aligning with `is_fatal = strict` would change behavior and break REQ-008.

## Alternatives considered

- **Standalone modules for extracted classes**: Would improve reusability but adds import complexity and couples the new module to `shared/` layer constraints. Deferred to Phase X if reuse emerges.
- **Keep `_fetch_server_tools()` as-is and only extract validation**: Would leave the HTTP fetch logic coupled to the service, reducing testability gains. Not aligned with REQ-001.
- **Align duplicate findings with `is_fatal = strict` scheme**: Would simplify severity logic but changes behavior — breaks REQ-008. The module docstring confirms the current exception is intentional.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

#### Phase 1: Preparation — Extract `/v1/tools` constant (REQ-006)

1. Add `TOOLS_ENDPOINT = "/v1/tools"` at module level, after `_REQUIRED_SCHEMA_V2_FIELDS` definition (around line 81).
2. Replace all hardcoded `"/v1/tools"` references with `TOOLS_ENDPOINT`:
   - Line 202: `f"{cfg.url}/v1/tools"` → `f"{cfg.url}{TOOLS_ENDPOINT}"`
   - Line 207: `f"{key} unreachable at {cfg.url}/v1/tools: {e}"` → `f"{key} unreachable at {cfg.url}{TOOLS_ENDPOINT}: {e}"`
   - Line 212: `f"{key} /v1/tools returned HTTP {resp.status_code}"` → `f"{key}{TOOLS_ENDPOINT} returned HTTP {resp.status_code}"`
   - Line 219: `f"{key}: /v1/tools response is not valid JSON: {e}"` → `f"{key}: {TOOLS_ENDPOINT} response is not valid JSON: {e}"`
   - Line 224: `f"{key}: /v1/tools response is not a JSON object..."` → `f"{key}: {TOOLS_ENDPOINT} response is not a JSON object..."`
   - Line 234: `f"{key}: /v1/tools response is missing schema_version..."` → `f"{key}: {TOOLS_ENDPOINT} response is missing schema_version..."`
   - Line 244: `f"{key}: /v1/tools response has unsupported schema_version..."` → `f"{key}: {TOOLS_ENDPOINT} response has unsupported schema_version..."`
   - Line 256: `f"{key}: /v1/tools 'tools' field must be a list..."` → `f"{key}: {TOOLS_ENDPOINT} 'tools' field must be a list..."`
   - Line 296: `f"{server_key}: /v1/tools tool entry is not an object..."` → `f"{server_key}: {TOOLS_ENDPOINT} tool entry is not an object..."`
   - Line 302: `f"{server_key}: /v1/tools entry has invalid name..."` → `f"{server_key}: {TOOLS_ENDPOINT} entry has invalid name..."`
   - Line 308: `f"{server_key}: tool {name!r} has invalid description..."` — no `/v1/tools` reference, skip
   - Line 314: `f"{server_key}: tool {name!r} has invalid inputSchema..."` — no `/v1/tools` reference, skip

#### Phase 2: Extract `McpToolsHttpClient` class (REQ-001)

1. Create `McpToolsHttpClient` class below `_warning_entry` function (after line 112):

```python
class McpToolsHttpClient:
    """Fetch and validate one MCP server's /v1/tools response.

    Handles connection errors, non-200 responses, invalid JSON,
    schema_version checks, and malformed top-level shapes. Returns
    raw entries plus per-server findings.
    """

    def __init__(
        self, async_client: httpx.AsyncClient, logger: logging.Logger
    ) -> None:
        self._async_client = async_client
        self._logger = logger

    async def fetch_tools(
        self, server_key: str, cfg: McpServerConfig
    ) -> tuple[list[_RawEntry], list[StartupCheckOutcome], bool]:
        """Fetch and validate one server's /v1/tools response.

        Returns (entries, findings, is_unreachable). `is_unreachable` is True
        only for whole-server failures (connection error, non-200, invalid
        JSON, or malformed top-level shape) — not for individual malformed
        tool entries.
        """
        try:
            resp = await self._async_client.get(
                f"{cfg.url}{TOOLS_ENDPOINT}",
                timeout=httpx.Timeout(timeout=get_effective_health_timeout(cfg)),
            )
        except (httpx.HTTPError, OSError) as e:
            return _warning_fetch_result(
                f"{server_key} unreachable at {cfg.url}{TOOLS_ENDPOINT}: {e}"
            )

        if resp.status_code != HTTPStatus.OK:
            return _warning_fetch_result(
                f"{server_key} {TOOLS_ENDPOINT} returned HTTP {resp.status_code}"
            )

        try:
            body: object = resp.json()
        except ValueError as e:
            return _warning_fetch_result(
                f"{server_key}: {TOOLS_ENDPOINT} response is not valid JSON: {e}"
            )

        if not isinstance(body, dict):
            return _warning_fetch_result(
                f"{server_key}: {TOOLS_ENDPOINT} response is not a JSON object (got {type(body).__name__})"
            )

        schema_version = body.get("schema_version")
        if schema_version is None:
            self._logger.warning(
                "mcp_tool_discovery: server_key=%s missing schema_version in %s response",
                server_key,
                TOOLS_ENDPOINT,
            )
            return _warning_fetch_result(
                f"{server_key}: {TOOLS_ENDPOINT} response is missing schema_version "
                f"(expected {MCP_TOOL_SCHEMA_VERSION!r})"
            )
        if schema_version != MCP_TOOL_SCHEMA_VERSION:
            self._logger.warning(
                "mcp_tool_discovery: server_key=%s unsupported schema_version=%s",
                server_key,
                schema_version,
            )
            return _warning_fetch_result(
                f"{server_key}: {TOOLS_ENDPOINT} response has unsupported schema_version "
                f"{schema_version!r} (expected {MCP_TOOL_SCHEMA_VERSION!r})"
            )
        self._logger.debug(
            "mcp_tool_discovery: server_key=%s schema_version=%s",
            server_key,
            schema_version,
        )

        tools = body.get("tools")
        if not isinstance(tools, list):
            return _warning_fetch_result(
                f"{server_key}: {TOOLS_ENDPOINT} 'tools' field must be a list (got {type(tools).__name__})"
            )

        # Note: per-tool entry validation is delegated to ToolEntryValidator;
        # this method only validates the top-level response shape.
        return [], [], False
```

2. Update `McpToolDiscoveryService._fetch_server_tools()` to delegate to `McpToolsHttpClient`:

```python
async def _fetch_server_tools(
    self, key: str, cfg: McpServerConfig
) -> tuple[list[_RawEntry], list[StartupCheckOutcome], bool]:
    """Fetch and validate one server's /v1/tools response.

    Delegates HTTP fetching to `McpToolsHttpClient`; delegates per-tool
    entry validation to `ToolEntryValidator`.
    """
    client = McpToolsHttpClient(
        self._ctx.services_required.http, logger
    )
    raw_entries, top_level_findings, is_unreachable = await client.fetch_tools(key, cfg)
    if is_unreachable:
        return raw_entries, top_level_findings, True

    # Per-tool entry validation
    entries: list[_RawEntry] = []
    entry_findings: list[StartupCheckOutcome] = []
    validator = ToolEntryValidator(server_key=key, required=cfg.required)
    for raw_entry in raw_entries:
        normalized, finding = validator.validate_entry(key, cfg.url, raw_entry)
        if finding is not None and cfg.required:
            finding = StartupCheckOutcome(
                source=finding.source,
                status=StartupCheckStatus.FATAL,
                message=finding.message,
                remediation=finding.remediation,
            )
        if finding is not None:
            entry_findings.append(finding)
        if normalized is not None:
            entries.append((key, cfg.url, normalized))

    return entries, entry_findings, False
```

3. Verify tests pass after Phase 2: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`

#### Phase 3: Extract `ToolEntryValidator` class (REQ-002)

1. Create `ToolEntryValidator` class below `McpToolsHttpClient` (after Phase 2):

```python
class ToolEntryValidator:
    """Validate one raw /v1/tools entry.

    Individual validation methods for each concern: dict type, name,
    description, inputSchema, schema-2.0 fields, schema-2.0 contracts,
    optional field types, capabilities. A rejected entry returns
    (None, finding); a valid entry returns (entry, None).
    """

    def __init__(self, server_key: str, required: bool) -> None:
        self._server_key = server_key
        self._required = required

    def validate_entry(
        self, server_key: str, server_url: str, entry: object
    ) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        """Run all validation checks on a single entry."""
        result = self.validate_dict_type(entry)
        if result[0] is None:
            return result
        result = self.validate_name(result[0])
        if result[0] is None:
            return result
        result = self.validate_description(result[0])
        if result[0] is None:
            return result
        result = self.validate_input_schema(result[0])
        if result[0] is None:
            return result
        result = self.validate_schema_v2_fields(result[0])
        if result[0] is None:
            return result
        result = self.validate_schema_v2_contracts(result[0])
        if result[0] is None:
            return result
        result = self.validate_optional_fields(result[0])
        if result[0] is None:
            return result
        result = self.validate_capabilities(result[0])
        if result[0] is None:
            return result
        return result

    def validate_dict_type(self, entry: object) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        if not isinstance(entry, dict):
            return _warning_entry(
                f"{self._server_key}: {TOOLS_ENDPOINT} tool entry is not an object (got {type(entry).__name__})"
            )
        return entry, None

    def validate_name(self, entry: dict[str, object]) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            return _warning_entry(
                f"{self._server_key}: {TOOLS_ENDPOINT} entry has invalid name {name!r}"
            )
        return entry, None

    def validate_description(self, entry: dict[str, object]) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        description = entry.get("description")
        if not isinstance(description, str):
            return _warning_entry(
                f"{self._server_key}: tool {entry['name']!r} has invalid description {description!r}"
            )
        return entry, None

    def validate_input_schema(self, entry: dict[str, object]) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        input_schema = entry.get("inputSchema")
        if not isinstance(input_schema, dict):
            return _warning_entry(
                f"{self._server_key}: tool {entry['name']!r} has invalid inputSchema {input_schema!r}"
            )
        return entry, None

    def validate_schema_v2_fields(self, entry: dict[str, object]) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        missing_fields = [f for f in _REQUIRED_SCHEMA_V2_FIELDS if f not in entry]
        if missing_fields:
            return _warning_entry(
                f"{self._server_key}: tool {entry['name']!r} missing required schema-2.0 field(s): "
                f"{', '.join(missing_fields)}"
            )
        return entry, None

    def validate_schema_v2_contracts(self, entry: dict[str, object]) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        schema_errors = validate_tool_schema_v2(entry)
        if schema_errors:
            return _warning_entry(
                f"{self._server_key}: tool {entry['name']!r} failed schema-2.0 validation: "
                f"{'; '.join(schema_errors)}"
            )
        return entry, None

    def validate_optional_fields(self, entry: dict[str, object]) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        for field_name, expected_type in (
            ("status", str),
            ("enabled", bool),
        ):
            if field_name in entry and not isinstance(entry[field_name], expected_type):
                return _warning_entry(
                    f"{self._server_key}: tool {entry['name']!r} has invalid {field_name} "
                    f"{entry[field_name]!r} (expected {expected_type.__name__})"
                )
        return entry, None

    def validate_capabilities(self, entry: dict[str, object]) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
        capabilities = entry.get("capabilities")
        if capabilities is not None and not isinstance(capabilities, list):
            return _warning_entry(
                f"{self._server_key}: tool {entry['name']!r} on server {self._server_key!r}: "
                "capabilities must be a list"
            )
        return entry, None
```

2. Remove `_validate_and_normalize_entry()` from `McpToolDiscoveryService` (lines 279-348).

3. Verify tests pass after Phase 3: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`

#### Phase 4: Separate duplicate detection from RuntimeTool construction (REQ-003)

1. Split `_dedupe_and_build()` into two methods:

```python
def _detect_duplicates(
    self, entries: list[_RawEntry]
) -> tuple[dict[str, _RawEntry], list[StartupCheckOutcome]]:
    """Group entries by tool name, detect duplicates across servers.

    Returns (unique_entries_by_name, duplicate_findings). Names reported
    by exactly one server become a unique entry; names reported by more
    than one distinct server produce a FATAL finding.
    """
    by_name: dict[str, list[_RawEntry]] = {}
    for server_key, server_url, entry in entries:
        name = str(entry["name"])
        by_name.setdefault(name, []).append((server_key, server_url, entry))

    findings: list[StartupCheckOutcome] = []
    unique: dict[str, _RawEntry] = {}
    for name, group in by_name.items():
        server_keys = sorted({server_key for server_key, _, _ in group})
        if len(server_keys) > 1:
            status = StartupCheckStatus.FATAL
            msg = (
                f"duplicate tool name {name!r} reported by multiple servers: "
                f"{', '.join(server_keys)} — excluded from registry"
            )
            findings.append(
                StartupCheckOutcome(source=_SOURCE, status=status, message=msg)
            )
            continue
        server_key, server_url, entry = group[0]
        unique[name] = (server_key, server_url, entry)
    return unique, findings
```

2. Create `_build_runtime_tools()`:

```python
def _build_runtime_tools(
    self, unique_entries: dict[str, _RawEntry]
) -> dict[str, RuntimeTool]:
    """Build RuntimeTool instances from unique-name entries.

    Every entry reaching this method has already passed
    `_validate_and_normalize_entry()`'s hard schema-2.0 requirement, so
    `is_write`/`requires_serial`/`resource_scope_kind`/`resource_scope_keys`
    are guaranteed present — they are indexed directly (`entry[...]`), not
    defaulted via `.get()`.
    """
    built: dict[str, RuntimeTool] = {}
    for name, (server_key, server_url, entry) in unique_entries.items():
        built[name] = build_runtime_tool(
            name=name,
            server_key=server_key,
            server_url=server_url,
            description=str(entry.get("description", "")),
            input_schema=entry.get("inputSchema"),  # type: ignore[arg-type]
            raw_definition=entry,
            status=str(entry.get("status", "active")),
            is_write=entry["is_write"],  # type: ignore[arg-type]
            requires_serial=entry["requires_serial"],  # type: ignore[arg-type]
            resource_scope_kind=str(entry["resource_scope_kind"]),
            resource_scope_keys=tuple(entry["resource_scope_keys"]),  # type: ignore[arg-type]
            enabled_for_llm=bool(entry.get("enabled", True)),
            capabilities=tuple(entry.get("capabilities", []) or []),  # type: ignore[arg-type]
        )
    return built
```

3. Update `discover_all()` to use the new methods and eliminate redundant registry creation:

```python
async def discover_all(self) -> DiscoveryResult:
    """Fetch tools from every HTTP-transport MCP server and build a registry."""
    entries: list[_RawEntry] = []
    findings: list[StartupCheckOutcome] = []
    unreachable: list[str] = []
    for key, cfg in self._ctx.cfg.mcp.mcp_servers.items():
        if cfg.transport != TransportType.HTTP or not cfg.url or cfg.is_disabled:
            continue
        fetched, server_findings, is_unreachable = await self._fetch_server_tools(
            key, cfg
        )
        if is_unreachable:
            is_required = cfg.required
            new_findings = []
            for o in server_findings:
                new_status = (
                    StartupCheckStatus.FATAL
                    if is_required
                    else StartupCheckStatus.WARNING
                )
                new_findings.append(
                    StartupCheckOutcome(
                        source=o.source,
                        status=new_status,
                        message=o.message,
                        remediation=o.remediation,
                    )
                )
            server_findings = new_findings

        findings.extend(server_findings)
        if is_unreachable:
            unreachable.append(key)
        entries.extend(fetched)

    # Separate duplicate detection from RuntimeTool construction
    unique_entries, dedup_findings = self._detect_duplicates(entries)
    findings.extend(dedup_findings)

    # Build RuntimeTools with unavailable_servers exclusion at construction time
    runtime_tools = self._build_runtime_tools(unique_entries)
    unavailable_keys = frozenset(unreachable)
    registry = RuntimeToolRegistry(
        tools=runtime_tools,
        unavailable_servers=unavailable_keys,
    )

    # Required tool checks against the first (and only) registry
    for srv_key, srv_cfg in self._ctx.cfg.mcp.mcp_servers.items():
        if srv_cfg.required and srv_cfg.tool_names:
            for tool_name in srv_cfg.tool_names:
                if tool_name not in registry._tools:
                    findings.append(
                        StartupCheckOutcome(
                            source=_SOURCE,
                            status=StartupCheckStatus.FATAL,
                            message=(
                                f"{srv_key}: required tool {tool_name!r} not found in discovery results"
                            ),
                            remediation="Verify the server's /v1/tools response includes this tool.",
                        )
                    )
    drift_findings = self._build_drift_findings(entries)
    findings.extend(drift_findings)
    tool_defs_finding = await self._check_tool_definitions_finding()
    if tool_defs_finding is not None:
        findings.append(tool_defs_finding)

    return DiscoveryResult(
        registry=registry,
        findings=findings,
        unreachable=unreachable,
    )
```

4. Remove the second `RuntimeToolRegistry` instantiation (lines 176-180 of original file).

5. Verify tests pass after Phase 4: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`

#### Phase 5: Consolidate severity classification (REQ-004)

1. Create `SeverityClassifier` class below `ToolEntryValidator`:

```python
class SeverityClassifier:
    """Consolidated severity escalation logic.

    The `is_fatal = strict` rule applies uniformly to all findings emitted
    by McpToolDiscoveryService (duplicates, drift, tool-definitions,
    malformed-capabilities). Duplicate findings follow the same scheme
    unless explicitly documented as an exception.

    Exception: duplicate tool names are always FATAL regardless of strict mode.
    A duplicated tool is unusable, so there is no WARNING-only case.
    This is documented in the module docstring (lines 32-34).
    """

    def __init__(self, is_strict: bool) -> None:
        self._is_strict = is_strict

    def classify(
        self, finding: StartupCheckOutcome, is_duplicate: bool = False
    ) -> StartupCheckOutcome:
        """Classify a finding's severity based on strict mode and context.

        Args:
            finding: The finding to classify.
            is_duplicate: Whether this finding relates to a duplicate tool name.

        Returns:
            A new StartupCheckOutcome with the correct severity level.
        """
        if is_duplicate:
            # Always fatal — tool is unusable when duplicated across servers
            return StartupCheckOutcome(
                source=finding.source,
                status=StartupCheckStatus.FATAL,
                message=finding.message,
                remediation=finding.remediation,
            )
        if self._is_strict:
            return StartupCheckOutcome(
                source=finding.source,
                status=StartupCheckStatus.FATAL,
                message=finding.message,
                remediation=finding.remediation,
            )
        return finding
```

2. Replace scattered `_is_strict()` / `_is_fatal_severity()` logic:

In `_build_drift_findings()`, replace:
```python
status = (
    StartupCheckStatus.FATAL
    if self._is_fatal_severity()
    else StartupCheckStatus.WARNING
)
```
with:
```python
classifier = SeverityClassifier(is_strict=self._is_strict())
for sk, msgs in drift.items():
    base_finding = StartupCheckOutcome(
        source=_SOURCE,
        status=StartupCheckStatus.WARNING,
        message=f"Live routing drift [{sk}]: {msgs}",
    )
    findings.append(classifier.classify(base_finding, is_duplicate=False))
```

In `_check_tool_definitions_finding()`, replace:
```python
status = (
    StartupCheckStatus.FATAL
    if self._is_fatal_severity()
    else StartupCheckStatus.WARNING
)
return StartupCheckOutcome(
    source=_SOURCE,
    status=status,
    message="; ".join(result.warning_messages()),
)
```
with:
```python
classifier = SeverityClassifier(is_strict=self._is_strict())
base_finding = StartupCheckOutcome(
    source=_SOURCE,
    status=StartupCheckStatus.WARNING,
    message="; ".join(result.warning_messages()),
)
return classifier.classify(base_finding, is_duplicate=False)
```

Also replace the RuntimeError handler in `_check_tool_definitions_finding()`:
```python
except RuntimeError as exc:
    classifier = SeverityClassifier(is_strict=self._is_strict())
    base_finding = StartupCheckOutcome(
        source=_SOURCE,
        status=StartupCheckStatus.WARNING,
        message=str(exc),
    )
    return classifier.classify(base_finding, is_duplicate=False)
```

3. In `discover_all()`, replace unreachable server finding escalation:
```python
new_status = (
    StartupCheckStatus.FATAL
    if is_required
    else StartupCheckStatus.WARNING
)
```
with:
```python
classifier = SeverityClassifier(is_strict=is_required)
new_status = classifier.classify(o, is_duplicate=False).status
```

4. Document the "always FATAL for duplicates" exception in SeverityClassifier class docstring (already included above).

5. Verify tests pass after Phase 5: `uv run pytest tests/agent/test_startup_severity_classification.py -v`

#### Phase 6: Reduce `discover_all()` to orchestration only

1. Refactor `discover_all()` to use extracted classes and reduce to under 30 lines (see Phase 4 step 3 above).

2. Update module docstring to reflect new class structure and responsibility boundaries:
   - Add `McpToolsHttpClient` — fetches `/v1/tools`, validates top-level response shape
   - Add `ToolEntryValidator` — validates individual tool entries
   - Add `SeverityClassifier` — consolidates severity escalation logic
   - Note the "always FATAL for duplicates" exception in the severity section

## Compatibility considerations

- **Public API preservation**: All existing public APIs must be preserved: `McpToolDiscoveryService`, `DiscoveryResult`, `_warning_fetch_result`, `_warning_entry`. These are consumed by tests and other modules.
- **Return type compatibility**: `DiscoveryResult` dataclass fields (`registry`, `findings`, `unreachable`) must remain unchanged.
- **Behavioral compatibility**: All existing behavior must be preserved — duplicate tool names always excluded from registry, severity escalation rules, unreachable server handling.
- **Reference files**: `scripts/shared/runtime_tool_registry.py` must handle `unavailable_servers` correctly at construction time (verified via `_is_excluded_server()`).

## Security considerations

- No new security-sensitive code paths introduced.
- The "always FATAL for duplicates" exception preserves the existing security posture — duplicated tools are excluded rather than silently routed.
- Severity escalation logic consolidation does not change which findings are escalated; it only centralizes the decision point.

## Rollback considerations

- Each phase can be rolled back independently by reverting the changes made in that phase.
- Phase 1 constant extraction is safe to rollback — no behavioral impact.
- Phase 2-5 refactoring changes should be tested incrementally; rollback each phase separately if a test failure occurs.
- If Phase 4 breaks unreachable server exclusion, revert the second `RuntimeToolRegistry` instantiation removal and restore the filtered copy pattern.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/services/mcp_tool_discovery.py | Unit + behavioral lock | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | All existing tests pass without modification |
| scripts/agent/services/mcp_tool_discovery.py | Integration | `uv run pytest tests/agent/test_startup.py -v` | All startup integration tests pass |
| scripts/agent/services/mcp_tool_discovery.py | Integration | `uv run pytest tests/agent/test_startup_severity_classification.py -v` | All severity classification tests pass |
| scripts/agent/services/mcp_tool_discovery.py | Integration | `uv run pytest tests/integration/test_production_security_regression.py -v` | All integration regression tests pass |
| scripts/agent/services/mcp_tool_discovery.py | Type check | `uv run mypy scripts/agent/services/mcp_tool_discovery.py` | No new mypy errors |
| scripts/agent/services/mcp_tool_discovery.py | Lint check | `uv run ruff check scripts/agent/services/mcp_tool_discovery.py` | No new ruff lint errors |
| scripts/agent/services/mcp_tool_discovery.py | Behavioral lock | Compare StartupCheckOutcome messages before/after refactoring | Identical outputs |

## Completion criteria

- [ ] `discover_all()` method reduced to under 30 lines (orchestration only, no business logic)
- [ ] `_validate_and_normalize_entry()` removed; replaced by `ToolEntryValidator.validate_entry()` method
- [ ] `_dedupe_and_build()` separated into `_detect_duplicates()` and `_build_runtime_tools()` methods
- [ ] Severity classification logic consolidated in a single location (with documented exception for duplicate findings if retained)
- [ ] No redundant registry creation in `discover_all()` — pass `unavailable_servers` to first `RuntimeToolRegistry` constructor
- [ ] `/v1/tools` path extracted to a module-level constant
- [ ] All existing tests pass without modification
- [ ] No new mypy errors introduced
- [ ] No ruff lint errors introduced
- [ ] Behavioral regression verification: compare StartupCheckOutcome messages before/after refactoring for identical outputs

## Out of scope

- Adding new validation rules for tool entries
- Changing the duplicate-tool-name resolution strategy
- Modifying `RuntimeToolRegistry`'s core functionality beyond removing redundant filtering
- Adding new dependencies
- Changing the public API surface of `McpToolDiscoveryService`
- Addressing the known limitation about two independent HTTP round-trips (mentioned in module docstring)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — Extract `/v1/tools` constant | Completed | — | — | REQ-006 |
| 2 | Phase 2: Extract `McpToolsHttpClient` class | Completed | — | — | REQ-001 |
| 3 | Phase 3: Extract `ToolEntryValidator` class | Completed | — | — | REQ-002 |
| 4 | Phase 4: Separate duplicate detection from RuntimeTool construction | Completed | — | — | REQ-003, REQ-005 |
| 5 | Phase 5: Consolidate severity classification | Completed | — | — | REQ-004 |
| 6 | Phase 6: Reduce `discover_all()` to orchestration only | Completed | — | — | REQ-001, REQ-003, REQ-005 |
| 7 | Final validation | Completed | — | — | REQ-009, REQ-010, REQ-011, REQ-008 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007, REQ-008
- **Source issue**: issues/20260924-105819_refactor_001_refactor-mcp-tool-discovery-service.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-172946_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-174746
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py
