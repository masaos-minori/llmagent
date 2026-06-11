# Implementation: agent/services/{enums,exceptions,models,io_ports}.py — Foundation files

## Goal

Create 4 new foundation files for the `agent/services/` subsystem.
These introduce Enum types, exception classes, DTO models, and I/O port Protocols
that all other service files will reference in subsequent refactoring steps.

## Scope

**Target files (all new)**:
- `scripts/agent/services/enums.py`
- `scripts/agent/services/exceptions.py`
- `scripts/agent/services/models.py`
- `scripts/agent/services/io_ports.py`

No existing files are modified in this step.

## Assumptions

1. `from __future__ import annotations` is used throughout.
2. `agent/services/models.py` imports only from `agent/services/enums.py` — no other agent/* imports to avoid cycles.
3. `agent/services/io_ports.py` has no agent/* imports; uses `typing.Protocol` only.
4. `ContextStateView.breakdown` is `dict[str, int]` (presentation data, dict is acceptable here).
5. `AuditUnavailableError` is defined but never raised in current code (placeholder for future use).
6. `SessionTitleResult` holds the generated title string.
7. `DbHealth`, `DbCheckpointResult`, `DbPurgeResult`, `DbRecoverResult` are added to `models.py` for `db_maintenance_service.py` Step 9.

## Implementation

### Target files

1. `scripts/agent/services/enums.py`
2. `scripts/agent/services/exceptions.py`
3. `scripts/agent/services/models.py`
4. `scripts/agent/services/io_ports.py`

### Procedure

**enums.py**:
```python
from __future__ import annotations
from enum import Enum

class IngestStage(str, Enum):
    OK = "ok"
    CRAWL = "crawl"
    SPLIT = "split"
    INGEST = "ingest"

class McpTier(str, Enum):
    READ_ONLY = "READ_ONLY"
    WRITE_SAFE = "WRITE_SAFE"
    WRITE_DANGEROUS = "WRITE_DANGEROUS"
    ADMIN = "ADMIN"

class McpAvailability(str, Enum):
    OK = "OK"
    STOPPED = "STOPPED"
    NOT_STARTED = "NOT_STARTED"
    DEAD = "DEAD"
    NO_URL = "no-url"
    HTTP_ERROR = "http_error"
    FAIL = "fail"

class ConversationActionType(str, Enum):
    CLEAR = "clear"
    SWITCH_PROMPT = "switch_prompt"

class ExportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
```

**exceptions.py**:
```python
from __future__ import annotations
from agent.services.enums import IngestStage

class IngestStageError(RuntimeError):
    def __init__(self, stage: IngestStage, detail: str) -> None:
        super().__init__(f"[{stage.value}] {detail}")
        self.stage = stage
        self.detail = detail

class McpProbeError(RuntimeError): ...
class SessionTitleGenerationError(RuntimeError): ...
class ConfigReloadValidationError(ValueError): ...
class ContextStateBuildError(RuntimeError): ...
class ExportWriteError(OSError): ...
class ConversationStateError(RuntimeError): ...
class DbMaintenanceError(RuntimeError): ...
```

**models.py**:
```python
from __future__ import annotations
from dataclasses import dataclass, field
from agent.services.enums import (
    ConversationActionType, ExportFormat, IngestStage, McpAvailability, McpTier,
)

@dataclass(frozen=True)
class IngestOutcome:
    stage: IngestStage
    n_chunks: int = 0
    messages: tuple[str, ...] = ()

@dataclass(frozen=True)
class SessionTitleResult:
    title: str

@dataclass(frozen=True)
class McpProbeResult:
    key: str
    transport: str
    startup_mode: str
    auth: bool
    tier: McpTier
    role: str
    availability: McpAvailability
    health: str
    endpoint: str

@dataclass(frozen=True)
class SessionRestoreResult:
    session_id: int
    n_messages: int

@dataclass(frozen=True)
class UndoResult:
    n_removed: int

@dataclass(frozen=True)
class ConversationActionResult:
    action: ConversationActionType
    message: str

@dataclass(frozen=True)
class ContextStateView:
    total_chars: int
    compress_limit: int
    n_msgs: int
    sys_preview: str
    compress_count: int
    token_is_exact: bool
    token_estimate: int | None
    token_limit: int
    tokenize_configured: bool
    mem_status: str
    git_branch: str | None
    git_commit: str | None
    breakdown: dict[str, int]

@dataclass(frozen=True)
class DbStats:
    docs: int
    chunks: int
    sessions: int
    messages: int

@dataclass(frozen=True)
class DbHealth:
    integrity_ok: bool
    wal_pages: int
    size_bytes: int

@dataclass(frozen=True)
class DbCheckpointResult:
    mode: str
    pages_written: int

@dataclass(frozen=True)
class DbPurgeResult:
    sessions_removed: int

@dataclass(frozen=True)
class DbRecoverResult:
    integrity_ok: bool
    recovered: bool
    detail: str

@dataclass(frozen=True)
class ExportResult:
    n_messages: int
    content: str
    format: ExportFormat

@dataclass
class ConfigReloadRequest:
    """Typed request object for apply_config. All fields optional; missing fields are skipped."""
    mcp_servers: dict | None = None
    approval: dict | None = None
    llm: dict | None = None
    masked_fields: list[str] | None = None
    rag_tool: dict | None = None
    sse: dict | None = None
```

**io_ports.py**:
```python
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol
if TYPE_CHECKING:
    from agent.services.models import ScaffoldResult  # forward ref only

class InstallIOPort(Protocol):
    async def ask_port(self, default: int) -> int: ...
    async def ask_role(self) -> str: ...
    async def ask_confd(self) -> bool: ...

class ExportOutputPort(Protocol):
    def write(self, content: str) -> None: ...
    def write_file(self, content: str, path: str, n_messages: int) -> None: ...

class StatusRenderPort(Protocol):
    def render_next_steps(self, result: object) -> str: ...
```

### Method

`Write` tool for each new file. Use the exact class/field names from the plan.

### Details

- `exceptions.py` imports `IngestStage` from `enums.py` for `IngestStageError` constructor.
- `models.py` imports from `enums.py` only — no circular imports.
- `io_ports.py` uses `Protocol` from `typing`; `ScaffoldResult` is a forward reference guarded by `TYPE_CHECKING` to avoid importing from `mcp_install.py`.
- `ConfigReloadRequest` uses `dict` / `list` without generic params at runtime due to `from __future__ import annotations`.

## Validation plan

```bash
PYTHONPATH=scripts uv run python -c "
from agent.services.enums import IngestStage, McpTier, McpAvailability, ConversationActionType, ExportFormat
from agent.services.exceptions import IngestStageError, SessionTitleGenerationError, ConfigReloadValidationError
from agent.services.models import IngestOutcome, McpProbeResult, SessionRestoreResult, ContextStateView
from agent.services.io_ports import InstallIOPort, ExportOutputPort
print('import OK')
"
uv run ruff check scripts/agent/services/enums.py scripts/agent/services/exceptions.py scripts/agent/services/models.py scripts/agent/services/io_ports.py
uv run mypy scripts/agent/services/enums.py scripts/agent/services/exceptions.py scripts/agent/services/models.py scripts/agent/services/io_ports.py
```
