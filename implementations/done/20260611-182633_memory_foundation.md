# Goal

Create four new foundation files in `scripts/agent/memory/` defining shared enums,
exceptions, DTOs, and ports used throughout the memory layer.

# Scope

New files only — no changes to existing code in this step:
- `scripts/agent/memory/enums.py`
- `scripts/agent/memory/exceptions.py`
- `scripts/agent/memory/models.py`
- `scripts/agent/memory/ports.py`

# Assumptions

1. `MemoryType` StrEnum replaces the module-level `MEMORY_TYPES: frozenset[str]` in types.py.
2. `HistoryMessage` is a memory-local DTO that replaces `LLMMessage` from shared.types.
3. `ConsistencyReport` replaces `dict[str, int]` return from `store.check_consistency()`.
4. `EmbeddingResponse` DTO wraps the HTTP response body from the embedding service.
5. `InjectionSnippet` DTO wraps each injected snippet returned by injection.py.
6. `JsonlRecord` DTO represents one deserialized line from the JSONL file.
7. All exception classes inherit from either ValueError or RuntimeError to match project convention.

# Implementation

## Target file

`enums.py`, `exceptions.py`, `models.py`, `ports.py`

## Procedure

1. Create `enums.py` with StrEnum subclasses.
2. Create `exceptions.py` with exception hierarchy.
3. Create `models.py` with frozen dataclasses.
4. Create `ports.py` with Protocol.
5. Run ruff + mypy on each.

## Method

Same pattern as `agent/commands/` foundation files (enums → exceptions → models → ports).

## Details

### enums.py

```python
from enum import StrEnum

class MemoryType(StrEnum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"

class RetrievalMode(StrEnum):
    FTS = "fts"
    KNN = "knn"
    HYBRID = "hybrid"

class ExtractionDecision(StrEnum):
    ACCEPT = "accept"
    REJECT_TOO_SHORT = "reject_too_short"
    REJECT_NO_KEYWORDS = "reject_no_keywords"
    REJECT_DEDUP = "reject_dedup"
```

### exceptions.py

```python
class MemorySchemaError(ValueError): ...
class MemoryStorageError(RuntimeError): ...
class JsonlFormatError(ValueError): ...
class MemoryConsistencyError(RuntimeError): ...
class EmbeddingTransportError(RuntimeError): ...
class EmbeddingProtocolError(ValueError): ...
class ExtractionError(RuntimeError): ...
class UnknownMemoryTypeError(MemorySchemaError): ...
class InjectionValidationError(ValueError): ...
```

### models.py

```python
@dataclass(frozen=True)
class HistoryMessage:
    role: str
    content: str

@dataclass(frozen=True)
class JsonlRecord:
    memory_id: str; memory_type: str; source_type: str
    session_id: int | None; turn_id: str | None
    project: str; repo: str; branch: str
    content: str; summary: str; tags: list[str]
    importance: float; pinned: bool; created_at: str; updated_at: str

@dataclass(frozen=True)
class ConsistencyReport:
    memories: int; fts: int; vec: int

@dataclass(frozen=True)
class EmbeddingRequest:
    text: str; query_prefix: str

@dataclass(frozen=True)
class EmbeddingResponse:
    embedding: list[float]; model: str | None = None

@dataclass(frozen=True)
class InjectionSnippet:
    prefix: str; text: str; memory_id: str; memory_type: str
```

### ports.py

```python
class MemoryOutputPort(Protocol):
    def emit_persist(self, memory_id: str, memory_type: str) -> None: ...
    def emit_skip_dedup(self, memory_id: str) -> None: ...
```

# Validation plan

- `uv run ruff check scripts/agent/memory/enums.py scripts/agent/memory/exceptions.py scripts/agent/memory/models.py scripts/agent/memory/ports.py`
- `uv run mypy scripts/agent/memory/enums.py scripts/agent/memory/exceptions.py scripts/agent/memory/models.py scripts/agent/memory/ports.py`
