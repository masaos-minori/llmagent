# Implementation: Workflow mode startup validation — Preflight check + enriched error messages

## Goal

Improve startup validation clarity and operator guidance for `workflow_mode="required"` so that a missing or invalid workflow definition produces an actionable error message and is detectable before the agent fully initialises.

## Scope

- **In-Scope**:
  - Add a preflight workflow-definition check inside `StartupOrchestrator._initialize()` (before `_init_orchestrator()`)
  - Enrich error messages in `Orchestrator.__init__()` and `Orchestrator._log_fallback()` with: mode, expected file path, and remediation hint
  - Add a `check_workflow_definition()` helper in `repl_health.py` (consistent with existing `check_readiness`, `check_routing_drift` patterns)
  - Update `docs/05_agent_08_configuration.md` — clarify production deployment contract under the `workflow_mode` section
  - Update `docs/05_agent_10_operations-and-observability.md` — add a "Workflow startup validation" sub-section with troubleshooting steps
  - Expand tests in `tests/test_orchestrator.py` and `tests/test_repl_health.py` to assert the new error messages and preflight path

- **Out-of-Scope**:
  - Changing `workflow_mode="required"` semantics or weakening the hard-error behaviour
  - Changing the production default in `common.toml`
  - Auto-fallback to `"auto"` on missing definition (requires explicit design decision)
  - Redesigning `WorkflowLoader` file-discovery logic

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Ordering of `_initialize()` vs `_check_services()` — the preflight check must run before `Orchestrator.__init__()` triggers the actual load | Resolved: Preflight check goes in `_initialize()`, BEFORE `_init_orchestrator()`. The run() sequence is: `_initialize()` (which calls `_init_orchestrator()` at line 68) → `_start_servers()` → `_check_services()`. The preflight must go between lines 67 and 68 in `_initialize()`. |
| UNK-02 | Whether `check_workflow_definition()` should use `production_mode` flag (raise vs warn) to match `check_readiness()` contract | Resolved: Pass `workflow_mode: str` string parameter to the preflight helper so it can enforce raise-vs-warn based on the mode value, consistent with `check_readiness()` pattern. |
| UNK-03 | Whether doc updates should also cover `/reload` behaviour when `workflow_mode` changes at runtime | Resolved: `workflow_mode` is NOT listed in the hot-reload eligibility table (lines 60-73 of `docs/05_agent_08_configuration.md`) and is NOT handled in `config_reload.py`. It is a startup-only field. The doc update should note this explicitly. |

## Code Verification: Current State

### 1. `_WORKFLOWS_DIR` is private — needs to be exposed as public constant

**File**: `scripts/agent/workflow/workflow_loader.py:42`

```python
_WORKFLOWS_DIR = (
    Path(__file__).parent.parent.parent / "config" / "workflows"
)  # project-level workflows directory
```

The preflight helper needs access to this path. Options:
- Option A: Expose as `WORKFLOWS_DIR` public constant (recommended — minimal change)
- Option B: Add a `preflight_check()` classmethod on WorkflowLoader

### 2. Current error messages lack actionable detail

**File**: `scripts/agent/orchestrator.py:132-136`

```python
if self._workflow_mode == "required":
    raise RuntimeError(
        f"[workflow] mode=required but WorkflowLoader failed: {exc}. "
        "Check workflow definition file or set workflow_mode=auto in config."
    ) from exc
```

Missing: expected file path, current mode, specific remediation.

**File**: `scripts/agent/orchestrator.py:143-151`

```python
def _log_fallback(self, reason: str) -> None:
    if self._workflow_mode == "required":
        raise RuntimeError(
            f"Workflow mode=required but workflow unavailable: {reason}"
        )
    raise WorkflowCreationError(
        f"Workflow unavailable ({reason}). "
        "Direct-execution fallback is disabled. "
        "Fix the workflow definition or set workflow_mode=disabled."
    )
```

Missing: expected file path, current mode.

### 3. Preflight check location — must go in `_initialize()` before `_init_orchestrator()`

**File**: `scripts/agent/startup.py:61-68`

```python
def _initialize(self) -> None:
    """Setup readline, wire DI, init CommandRegistry and Orchestrator."""
    ctx = self._ctx
    self._view.setup_readline()
    build_agent_context(ctx, self._view)
    ctx.conv.llm_url = ctx.cfg.llm.llm_url
    self._init_command_registry()
    # ← PREFLIGHT CHECK GOES HERE (before line 68)
    self._init_orchestrator()
```

### 4. Existing `check_readiness()` pattern for reference

**File**: `scripts/agent/repl_health.py:76-94`

```python
async def check_readiness(
    ctx: AgentContext, *, production_mode: bool = False
) -> HealthCheckResult:
    """Probe required services at startup; raise in production mode on failure."""
    result = await check_service_health(ctx)
    if production_mode and result.has_issues:
        error_msgs = [f"{w.label}: {w.message}" for w in result.warnings]
        msg = (
            "Startup readiness check failed (required services unavailable): "
            + "; ".join(error_msgs)
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return result
```

The new `check_workflow_definition()` should follow a similar pattern but simpler — just check file existence.

### 5. `workflow_mode` is NOT hot-reloadable

**File**: `docs/05_agent_08_configuration.md:60-73` — not in the hot-reload eligibility table.
**File**: `scripts/agent/services/config_reload.py` — no references to `workflow_mode`.

This means `/reload` cannot change workflow_mode at runtime; it's a startup-only field. The doc update should make this explicit.

## Implementation Steps

### Phase 1: Preparation / Refactoring

#### 1.1 Expose `_WORKFLOWS_DIR` as public constant in `workflow_loader.py`

**File**: `scripts/agent/workflow/workflow_loader.py:42`

```python
# Before (private):
_WORKFLOWS_DIR = (
    Path(__file__).parent.parent.parent / "config" / "workflows"
)

# After (public + private alias):
WORKFLOWS_DIR = (
    Path(__file__).parent.parent.parent / "config" / "workflows"
)
_WORKFLOWS_DIR = WORKFLOWS_DIR  # backward compat for internal usage
```

#### 1.2 Confirm `workflow_mode` hot-reload eligibility in docs

**File**: `docs/05_agent_08_configuration.md:60-73` — add note under the table:

```markdown
**Startup-only settings** (not hot-reloadable):
- `workflow_mode` — read once at agent start; never touched by `/reload`. Changes require a full restart.
```

### Phase 2: Core Logic Implementation

#### 2.1 Add `check_workflow_definition()` helper in `repl_health.py`

**File**: `scripts/agent/repl_health.py`

Append after existing health check functions:

```python
def check_workflow_definition(
    workflow_mode: str,
    workflows_dir: Path | None = None,
) -> list[str]:
    """Check whether the workflow definition file exists for the given mode.

    Returns a warning list when the file is missing and the mode requires it.
    Raises RuntimeError in production_mode when the file is missing and mode=required.

    Args:
        workflow_mode: The current workflow_mode setting ("auto", "required", or "disabled").
        workflows_dir: Override for the default WORKFLOWS_DIR path.

    Returns:
        A list of warning strings (empty if no issues).

    Raises:
        RuntimeError: When workflow_mode="required" and the definition file is missing.
    """
    if workflow_mode == "disabled":
        return []  # No workflow needed when disabled

    target_dir = workflows_dir or WORKFLOWS_DIR
    workflow_file = target_dir / "default.json"

    if not workflow_file.exists():
        msg = (
            f"Workflow definition file not found: {workflow_file}. "
            f"Current mode={workflow_mode!r}. "
            f"Deploy config/workflows/default.json or set workflow_mode=disabled in config."
        )
        if workflow_mode == "required":
            logger.error(msg)
            raise RuntimeError(msg)
        return [msg]  # Warning only for auto mode

    return []
```

#### 2.2 Add `_check_workflow_definition()` method in `startup.py`

**File**: `scripts/agent/startup.py`

Add import at top of file:
```python
from agent.repl_health import check_workflow_definition
```

Add method after `_check_embedding_dimensions()`:
```python
def _check_workflow_definition(self) -> None:
    """Preflight check for workflow definition file before Orchestrator.__init__()."""
    ctx = self._ctx
    try:
        warnings = check_workflow_definition(ctx.cfg.workflow_mode)
        for msg in warnings:
            self._view.write_warning(msg)
    except RuntimeError as e:
        # Preflight already logged the error; propagate to abort startup.
        logger.error("Workflow preflight check failed: %s", e)
        raise
```

Insert call in `_initialize()` before `_init_orchestrator()`:
```python
def _initialize(self) -> None:
    """Setup readline, wire DI, init CommandRegistry and Orchestrator."""
    ctx = self._ctx
    self._view.setup_readline()
    build_agent_context(ctx, self._view)
    ctx.conv.llm_url = ctx.cfg.llm.llm_url
    self._init_command_registry()
    self._check_workflow_definition()  # ← ADD THIS LINE
    self._init_orchestrator()
```

#### 2.3 Enrich error messages in `orchestrator.py`

**File**: `scripts/agent/orchestrator.py:132-136`

```python
if self._workflow_mode == "required":
    raise RuntimeError(
        f"[workflow] mode={self._workflow_mode!r} but WorkflowLoader failed: {exc}. "
        f"Expected workflow definition at: {WORKFLOWS_DIR / 'default.json'}. "
        "Fix the workflow definition file or set workflow_mode=disabled in config."
    ) from exc
```

**File**: `scripts/agent/orchestrator.py:143-151`

```python
def _log_fallback(self, reason: str) -> None:
    """Raise WorkflowCreationError; direct-execution fallback is removed (fail-closed)."""
    if self._workflow_mode == "required":
        raise RuntimeError(
            f"[workflow] mode={self._workflow_mode!r} but workflow unavailable: {reason}. "
            f"Expected workflow definition at: {WORKFLOWS_DIR / 'default.json'}. "
            "Fix the workflow definition or set workflow_mode=disabled in config."
        )
    raise WorkflowCreationError(
        f"[workflow] mode={self._workflow_mode!r} — workflow unavailable ({reason}). "
        "Direct-execution fallback is disabled. "
        "Fix the workflow definition or set workflow_mode=disabled in config."
    )
```

### Phase 3: Tests

#### 3.1 Add tests in `tests/test_repl_health.py`

**File**: `tests/test_repl_health.py`

```python
class TestCheckWorkflowDefinition:
    """Tests for check_workflow_definition() preflight helper."""

    def test_disabled_mode_returns_empty(self, tmp_path: pathlib.Path) -> None:
        """workflow_mode=disabled returns no warnings regardless of file existence."""
        warnings = check_workflow_definition("disabled", workflows_dir=tmp_path)
        assert warnings == []

    def test_auto_mode_missing_file_returns_warning(
        self, tmp_path: pathlib.Path
    ) -> None:
        """workflow_mode=auto with missing file returns warning (does not raise)."""
        warnings = check_workflow_definition("auto", workflows_dir=tmp_path)
        assert len(warnings) == 1
        assert "not found" in warnings[0]
        assert tmp_path.name in warnings[0]

    def test_required_mode_missing_file_raises(
        self, tmp_path: pathlib.Path
    ) -> None:
        """workflow_mode=required with missing file raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition("required", workflows_dir=tmp_path)
        assert "not found" in str(exc_info.value)
        assert tmp_path.name in str(exc_info.value)

    def test_required_mode_file_present_returns_empty(
        self, tmp_path: pathlib.Path
    ) -> None:
        """workflow_mode=required with present file returns no warnings."""
        (tmp_path / "default.json").write_text("{}")
        warnings = check_workflow_definition("required", workflows_dir=tmp_path)
        assert warnings == []

    def test_error_message_includes_mode_and_path(
        self, tmp_path: pathlib.Path
    ) -> None:
        """RuntimeError message includes current mode and expected path."""
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition("required", workflows_dir=tmp_path)
        msg = str(exc_info.value)
        assert "mode='required'" in msg or "mode=required" in msg
        assert tmp_path.name in msg

    def test_auto_mode_warning_includes_remediation(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Warning includes remediation hint for operator action."""
        warnings = check_workflow_definition("auto", workflows_dir=tmp_path)
        assert "workflow_mode=disabled" in warnings[0]
```

#### 3.2 Add tests in `tests/test_orchestrator.py`

**File**: `tests/test_orchestrator.py`

Extend existing required_mode test to assert enriched message content:
```python
def test_required_mode_enriched_error_message(
    mocker: pytest.MockFixture, tmp_path: pathlib.Path
) -> None:
    """Orchestrator.__init__ with workflow_mode=required includes file path in error."""
    # Mock WorkflowLoader to raise an error
    mock_loader = mocker.patch("agent.orchestrator.WorkflowLoader")
    mock_loader.return_value.load.side_effect = RuntimeError("file not found")

    # Create a valid common.toml so Orchestrator can parse config
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "common.toml").write_text(
        "[workflow]\nworkflow_mode = \"required\"\n"
    )
    mocker.patch("agent.orchestrator.Path", return_value=config_dir)

    ctx = mocker.MagicMock()
    ctx.cfg.workflow_mode = "required"
    ctx.cfg.mcp.security_profile = SecurityProfile.DEVELOPMENT
    ctx.services = None
    ctx.llm_client = mocker.MagicMock()

    with pytest.raises(RuntimeError) as exc_info:
        Orchestrator(
            ctx,
            on_turn_start=mocker.MagicMock(),
            on_turn_end=mocker.MagicMock(),
            on_error=mocker.MagicMock(),
            on_first_turn=mocker.MagicMock(),
        )

    msg = str(exc_info.value)
    assert "mode='required'" in msg or "mode=required" in msg
    assert "default.json" in msg
```

### Phase 4: Documentation

#### 4.1 Update `docs/05_agent_08_configuration.md`

**File**: `docs/05_agent_08_configuration.md:60-73` — add under the hot-reload eligibility table:

```markdown
**Startup-only settings** (not hot-reloadable):
- `workflow_mode` — read once at agent start; never touched by `/reload`. Changes require a full restart.
```

Also update the production default paragraph (line 158-161) to mention the preflight:

```markdown
**Production default:** `config/common.toml` sets `workflow_mode = "required"`. Any environment
that copies `common.toml` (see `deploy.sh:58`) must have a valid workflow definition file
deployed, or the agent will fail at startup with an actionable error message. The preflight
check runs before `Orchestrator.__init__()` and reports the expected path (`config/workflows/default.json`).
For local/dev environments without `common.toml` in the config search path, the dataclass default `"auto"` applies (warns and falls back).
```

#### 4.2 Update `docs/05_agent_10_operations-and-observability.md`

**File**: `docs/05_agent_10_operations-and-observability.md` — add new subsection under the troubleshooting section:

```markdown
### Workflow startup validation

When `workflow_mode = "required"` (production default), the agent validates the workflow
definition file exists before initializing the orchestrator. If the file is missing, a
`RuntimeError` is raised with the following actionable guidance:

- **Expected path:** `config/workflows/default.json`
- **Remediation options:**
  - Deploy the workflow definition to the expected path
  - Set `workflow_mode = "disabled"` in config (not recommended for production)
  - Set `workflow_mode = "auto"` for degraded operation (warns and falls back to direct LLM)

The preflight check runs before `Orchestrator.__init__()` and produces a clear error message
rather than a cryptic `WorkflowLoadError` that may not include the expected file path.

**Note:** `workflow_mode` is a startup-only setting — it cannot be changed via `/reload`.
Any change requires a full agent restart.
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `repl_health.check_workflow_definition` | Unit test: file absent + mode=required raises RuntimeError with path; mode=auto returns warning list; mode=disabled returns [] | `uv run pytest tests/test_repl_health.py -k workflow_definition` | All assertions pass |
| `startup.StartupOrchestrator._check_workflow_definition` | Integration: mock `check_workflow_definition` to return warnings; assert `view.write_warning` called | `uv run pytest tests/test_startup.py` | Warning surfaces to view |
| `orchestrator.Orchestrator.__init__` (required mode) | Existing test extended: assert error message contains file path | `uv run pytest tests/test_orchestrator.py -k required_mode` | Error message includes path and mode |
| Import layer contract | No new cross-layer imports introduced | `uv run lint-imports` | No violations |
| Type correctness | New function signatures are fully typed | `uv run mypy scripts/agent/repl_health.py scripts/agent/startup.py scripts/agent/orchestrator.py` | 0 new errors |
| Doc consistency | `workflow_mode` section in configuration doc names the deployment contract; ops doc has troubleshooting steps | Manual review | Sections present and accurate |

## Risks & Mitigations

- **Risk**: Preflight check runs after `Orchestrator.__init__()` making it redundant → **Mitigation**: UNK-01 resolved — insert check explicitly in `_initialize()` before `_init_orchestrator()` call (between lines 67 and 68).
- **Risk**: Exposing `WORKFLOWS_DIR` as a module-level constant introduces a coupling point that breaks tests relying on filesystem isolation → **Mitigation**: Accept `workflows_dir: Path | None` override in `check_workflow_definition()` parameter, consistent with the existing pattern used by `check_readiness()`.
- **Risk**: Doc-only changes diverge from actual code behaviour → **Mitigation**: Write tests first; update docs only after tests pass to ensure docs reflect verified behaviour.
- **Risk**: Enriched error messages in `orchestrator.py` change the regex patterns in existing tests (`test_orchestrator.py` `match="mode=required"`) → **Mitigation**: Use `re.search` compatible patterns or update test match strings as part of the same PR.

## Files Changed

- `scripts/agent/workflow/workflow_loader.py` — expose `_WORKFLOWS_DIR` as public constant `WORKFLOWS_DIR`
- `scripts/agent/repl_health.py` — add `check_workflow_definition()` helper function
- `scripts/agent/startup.py` — add `_check_workflow_definition()` method; call before `_init_orchestrator()`
- `scripts/agent/orchestrator.py` — enrich error messages with mode, file path, and remediation hint
- `tests/test_repl_health.py` — add `TestCheckWorkflowDefinition` test class
- `tests/test_orchestrator.py` — extend required_mode test to assert enriched message content
- `docs/05_agent_08_configuration.md` — note workflow_mode as startup-only (not hot-reloadable); update production default paragraph
- `docs/05_agent_10_operations-and-observability.md` — add "Workflow startup validation" troubleshooting sub-section
