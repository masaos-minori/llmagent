## 1. Goal
- Add `enable_grep` configuration field to `config/mdq_mcp_server.toml` so that MDQ service controls all operational parameters through the config file.

## 2. Scope
- **In-Scope**:
  - Add `enable_grep` field to `config/mdq_mcp_server.toml` (default: `true`)
  - Read `enable_grep` in `MdqService.__init__`
  - Enforce `enable_grep` flag in `service.grep_docs()` — return rejection response when `false`
- **Out-of-Scope**:
  - Existing field changes (db_path, allowed_dirs already implemented)
  - Adding `index_roots` (already handled by `allowed_dirs`)
  - DB schema changes

## 3. Requirements
### Functional
- `enable_grep = false` causes `grep_docs` to return a rejection response (HTTP 400 via `MdqValidationError`)
- Config read at startup (`__init__`); no runtime reload

### Non-functional
- Safe defaults: config file value takes precedence; code default is fallback when TOML field absent

## 4. Architecture
### Concurrency Model
- Config read once at `MdqService.__init__()`; no runtime reload
- No changes to concurrency model; same as existing `enable_refresh` pattern

### Component Boundaries
```
config/mdq_mcp_server.toml (enable_grep)
  └── MdqService.__init__() → reads enable_grep from config
        └── grep_docs → guard: if not self.enable_grep, raise MdqValidationError
```

## 5. Module Design
No changes to dependency direction. `service.py` reads config in `__init__`; `grep_docs` method checks the flag.

## 6. Interface Design
### New/Modified Methods

```python
# service.py
class MdqService:
    def __init__(self, db_path: str = ..., allowed_dirs: list[str] | None = ...):
        mdq_cfg = ConfigLoader.load_config("mdq_mcp_server.toml")
        # NEW: read enable_grep from config with safe default
        self.enable_grep: bool = mdq_cfg.get("enable_grep", True)

    def grep_docs(self, pattern: str, path_prefix: str | None = None) -> list[dict]:
        # MODIFIED: add enforcement guard at top of method
        if not self.enable_grep:
            raise MdqValidationError("grep_docs is disabled by configuration")
        # ... existing logic
```

### TOML Config

```toml
# config/mdq_mcp_server.toml
enable_grep = true  # When false, grep_docs tool is disabled (returns MdqValidationError)

[server]
host = "127.0.0.1"
port = 8013

[db]
path = "/opt/llm/db/mdq.sqlite"
```

## 7. Data Model & Serialization
No changes to data models. `enable_grep` is a runtime boolean flag read from config.

## 8. Error Handling & Resource Lifecycle
### Failure Modes
- Config default value mismatch between `service.py` and TOML → **Mitigation**: Set `__init__` default to match TOML default (`True`)
- `enable_refresh` also unused (flag read but not enforced) → **Mitigation**: Note during `grep_docs` implementation; consider fixing `enable_refresh` guard as part of this task

### Resource Lifecycle
- Config read once at `MdqService.__init__()`; no runtime reload
- No connection pooling; each operation opens and closes its own connection (unchanged)

## 9. Configuration
- `config/mdq_mcp_server.toml`: add `enable_grep = true` with comment
- Safe default in `service.py`: `mdq_cfg.get("enable_grep", True)`

## 10. Test Strategy
### Unit Tests
- `test_grep_docs_disabled_by_config`: set `enable_grep=False`, assert `MdqValidationError` raised from `grep_docs()`

### Regression Tests
- Full mdq regression: `uv run pytest tests/test_mdq_service.py -x -q`

## 11. Implementation Plan
### Phase 1: Config Addition
- Add `enable_grep = true` to `config/mdq_mcp_server.toml` (after `enable_refresh`)

### Phase 2: Service Implementation
- In `MdqService.__init__`, add `self.enable_grep: bool = mdq_cfg.get("enable_grep", True)`
- In `MdqService.grep_docs()`, add guard at top: `if not self.enable_grep: raise MdqValidationError("grep_docs is disabled by configuration")`

### Phase 3: Test Addition
- Add `test_grep_docs_disabled_by_config` in `tests/test_mdq_service.py`
- Run `uv run pytest tests/test_mdq_service.py -x -q` to confirm

## 12. Risks / Open Questions
- **UNK-01**: Return type when `enable_grep = false` (ValidationError vs custom response) → **Resolution**: Inspect `service.py` and `server.py`; follow existing `enable_refresh` pattern (flag read but not yet enforced — same approach for `enable_grep`)
- **Risk**: `enable_refresh` also remains unused → **Mitigation**: During `grep_docs` implementation, check if `enable_refresh` should also be fixed; consider as part of this task or separate issue.
