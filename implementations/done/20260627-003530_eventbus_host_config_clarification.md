# EventBus Host Configuration Clarification

## Goal

Remove dead `host` configuration from TOML config example in deployment documentation, clarify that host binding is controlled via uvicorn CLI arguments (not TOML config), and add a startup log for the effective bind address.

## Scope

**In-Scope**:
- Remove `host = "127.0.0.1"` from TOML config example in `06_eventbus_05_configuration_deploy_and_operations.md`
- Document host binding as uvicorn CLI configuration in deployment docs
- Add startup log for effective bind address in app.py
- Add config validation tests for EventBusConfig

**Out-of-Scope**:
- Adding authentication to EventBus HTTP endpoints
- Replacing uvicorn deployment mechanism
- Configuring host via TOML (by design, not supported)

## Assumptions

1. The `host` field is NOT loaded by `EventBusConfig` — confirmed: no `host` field defined in `scripts/eventbus/config.py` (lines 21-33)
2. The TOML example with `host = "127.0.0.1"` is dead config and should be removed — confirmed: actual `config/eventbus.toml` has no `host` field
3. Host binding is controlled via uvicorn CLI arguments (`--host 127.0.0.1`) — confirmed by existing start command in deployment docs (line 46)
4. uvicorn already logs the bind address at startup by default (e.g., "INFO: Uvicorn running on http://127.0.0.1:8015")

## Implementation

### Phase 1: Remove dead `host` from TOML config example

**Target file**: `docs/06_eventbus_05_configuration_deploy_and_operations.md`

**Procedure**:
1. Remove line 37 (`host = "127.0.0.1"`) from the TOML config example block (lines 35-39)
2. Update the TOML example to only include fields that are actually loaded by EventBusConfig (port, db_path, storage_dir, offsets_dir, deadletter_dir, max_retry, poll_interval_ms)

**Method**: Direct edit — remove the single line from the code block.

**Details**:
- Current lines 35-39:
```toml
# config/eventbus.toml
host = "127.0.0.1"
port = 8765
```
- After removal, only include fields that EventBusConfig actually loads:
```toml
# config/eventbus.toml
port = 8765
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
poll_interval_ms = 500
```

### Phase 2: Document host binding as deployment configuration

**Target file**: `docs/06_eventbus_05_configuration_deploy_and_operations.md`

**Procedure**:
1. Replace the TOML config example block under "Bind Address" section with a uvicorn CLI example showing host binding via `--host` argument
2. Update the section to clarify that host binding is a deployment/runtime concern, not a TOML config concern

**Method**: Edit the "Bind Address" subsection (lines 29-47) to replace the TOML example with a uvicorn CLI example.

**Details**:
- Current section structure:
```
### Bind Address
[text about 127.0.0.1 vs 0.0.0.0]
[Code block with dead host config]
[text about reverse proxy]

### Start command
[uvicorn CLI example]
```
- After edit, the TOML example is removed from "Bind Address" section; host binding is documented under "Start command" or as a deployment note referencing the uvicorn CLI.

### Phase 3: Add startup log for effective bind address

**Target file**: `scripts/eventbus/app.py`

**Procedure**:
1. In the lifespan function, after app creation, add logging of the effective bind address (host + port)
2. Use existing logger (`logger = logging.getLogger(__name__)`) to emit the startup log

**Method**: Add a log statement in the lifespan context manager after `app.state.config` is loaded.

**Details**:
- Current app.py line 108: `app = FastAPI(lifespan=lifespan)`
- Since uvicorn already logs "INFO: Uvicorn running on http://127.0.0.1:8015" by default, explicit startup logging may be unnecessary. However, if we want to log the effective bind address from within the app (independent of uvicorn's logging), add after lifespan setup:
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    app.state.config = load_config(get_config_path())
    logger.info("eventbus starting on port=%d", app.state.config.port)
    # ... rest of existing code
```

**Note**: If uvicorn's default logging already covers this, Phase 3 may be deferred. The deployment docs should reference uvicorn's `--host` flag as the mechanism for bind address configuration.

### Phase 4: Add config validation tests

**Target file**: `tests/test_eventbus_config.py` (new)

**Procedure**:
1. Create a new test file for EventBusConfig validation
2. Test that invalid port range is rejected
3. Test that invalid max_retry is rejected
4. Test that valid config without `host` field is accepted

**Method**: Use pytest with direct instantiation of EventBusConfig dataclass.

**Details**:
```python
import pytest
from scripts.eventbus.config import EventBusConfig

def test_invalid_port_too_low():
    with pytest.raises(ValueError, match="port must be 1024-65535"):
        EventBusConfig(port=0, db_path="", storage_dir="", offsets_dir="", deadletter_dir="", max_retry=3)

def test_invalid_port_too_high():
    with pytest.raises(ValueError, match="port must be 1024-65535"):
        EventBusConfig(port=70000, db_path="", storage_dir="", offsets_dir="", deadletter_dir="", max_retry=3)

def test_invalid_max_retry_zero():
    with pytest.raises(ValueError, match="max_retry must be >= 1"):
        EventBusConfig(port=8015, db_path="", storage_dir="", offsets_dir="", deadletter_dir="", max_retry=0)

def test_valid_config_without_host_field():
    cfg = EventBusConfig(
        port=8015, db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage", offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter", max_retry=3
    )
    assert cfg.port == 8015
    # host is not a field — this test validates no host attribute exists
    assert not hasattr(cfg, "host")

def test_valid_config_with_deprecated_defaults():
    cfg = EventBusConfig(
        port=8015, db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage", offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter", max_retry=3
    )
    assert cfg.poll_interval_ms == 500
    assert cfg.offset_checkpoint_interval == 10
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/06_eventbus_05_configuration_deploy_and_operations.md | Verify dead `host` removed from TOML example | Check for absence of `host = "127.0.0.1"` in TOML section | No dead config references remain |
| scripts/eventbus/app.py | Verify startup log added (if Phase 3 implemented) | Check for bind address logging at startup | Effective port logged at startup |
| tests/test_eventbus_config.py | Verify config validation tests pass | `uv run pytest tests/test_eventbus_config.py` | All config validation tests pass |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Removing `host` from TOML example may break operators who rely on it for audit purposes | Low | The `host` field is NOT loaded by EventBusConfig — it's dead config. Operators auditing the config would be misled by seeing a field that has no effect. This is a bug fix, not a breaking change. |
| Startup log for bind address may not work if uvicorn doesn't expose host binding info before app startup | Low | uvicorn logs the bind address at startup by default (e.g., "INFO: Uvicorn running on http://127.0.0.1:8015"). No additional logging needed if uvicorn already does this. Phase 3 may be deferred. |
| Tests may fail if test config file doesn't exist | Low | Tests use direct dataclass instantiation, not file loading. No external files required. |
