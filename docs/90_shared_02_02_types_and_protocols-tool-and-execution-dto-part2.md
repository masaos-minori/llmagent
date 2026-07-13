---
title: "Shared Types and Protocols - Tool and Execution DTOs (Part 2)"
category: shared
tags:
  - shared
  - types
  - tool-dto
  - action-result
  - tool-spec
  - cache
  - events
related:
  - 90_shared_00_document-guide.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_02_03_types_and_protocols-reference.md
source:
  - 90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md
---

# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 7c. `PluginFailure` / `PluginLoadResult` (`shared/plugin_result.py`)

```python
@dataclass(frozen=True)
class PluginFailure:
    path: str          # plugin .py filename
    error: str         # exception message

@dataclass(frozen=True)
class PluginLoadResult:
    loaded_count: int
    failed: tuple[PluginFailure, ...]
    tool_conflicts_shadowed: int
    tool_conflicts_allowed: int
    command_shadows_rejected: int

class PluginLoadError(RuntimeError):
    pass
```

- `PluginFailure` — 個々のプラグイン読み込み失敗の詳細
- `PluginLoadResult` — `load_plugins()` 呼び出しから集約された結果
- `PluginLoadError` — `strict_mode=True` で失敗または MCP 競合がある場合にのみ発生する
- Import: `from shared.plugin_result import PluginFailure, PluginLoadResult, PluginLoadError`

---

## 7d. `ToolDefinition` (`shared/tool_registry.py`)

```python
@dataclass(frozen=True)
class ToolDefinition:
    """Immutable tool definition owned by a single server."""
    name: str
    server_key: str
    description: str = ""
    input_schema: dict[str, object] = field(default_factory=dict)
```

- 不変のツール定義 — 1 つのツールは必ず 1 つの MCP サーバーに属する
- インポート時に `tool_constants.py` の frozenset から `_populate_default_registry()` により値が設定される
- **境界条件 (Boundary and ownership):** `description` と `input_schema` は将来利用のための予約フィールドであり、`_populate_default_registry()` では一切設定されず、現状どの呼び出し元からも読まれない。LLMに見せるツールスキーマは各サーバー自身の `tools.py` の `TOOL_LIST` が情報源であり、この `ToolRegistry` からではない (Explicit in code: `scripts/shared/tool_registry.py` docstring)
- `ToolRegistry` はツールの所有権・ルーティングのみを扱う。ライブ `/v1/tools` の応答は起動時のドリフト検証にのみ使われ、ルーティング判断には使われない (Explicit in code)
- Import: `from shared.tool_registry import ToolDefinition, ToolRegistry, get_registry`

---

## 8. `ArtifactEvent` / `RetryEvent` (`shared/events.py`)

```python
class ArtifactEvent(TypedDict, total=False):
    """Emitted when a repo artifact is created or updated."""
    event_type: str  # "artifact.updated" | "artifact.created" | "artifact.deleted"
    repo: str        # "owner/repo"
    branch: str      # branch name
    commit: str      # commit SHA or empty
    path: str        # file path or empty (for whole-branch events)
    pr_number: int   # PR number or 0
    session_id: int  # agent session that triggered the event
    timestamp: str   # ISO-8601 UTC

class RetryEvent(TypedDict):
    """Emitted when a workflow stage retry is triggered."""
    event_type: str
    workflow_id: str
    task_id: str
    attempt_number: int
    max_attempts: int
    error_type: str
    backoff_sec: float
    session_id: str
    timestamp: str   # ISO-8601 UTC
```

> **Note:** `ArtifactEvent` は純粋なデータ構造(`TypedDict`)である。配信の仕組み・イベントバス・購読者は一切存在しない。将来的にアーティファクトイベントを発行しうるコードのための型注釈としてのみ存在する。`ArtifactEvent` のインスタンス生成が何らかのアクションをトリガーすると仮定してはならない (Explicit in code: `scripts/shared/events.py` モジュールdocstring)。

### 将来のイベントエンベロープ (構想段階 — 未実装)

これらのフィールドは将来のイベントバス層のために予約されている。`shared/events.py` に
設計方針としてのみ記載されている。現在の `ArtifactEvent` インスタンスにこれらが
存在すると仮定してはならない。

| Field | Type | Purpose |
|---|---|---|
| `event_id` | str | UUID v7 — イベントごとの一意識別子 |
| `source` | str | 発行元モジュール (例: `"mcp/github"`) |
| `timestamp` | str | ISO-8601 UTC — 既にフィールドとして存在 |
| `correlation_id` | str | 関連イベントを結びつけるトレース ID |

イベントバスが実装された場合、これらのフィールドは `ArtifactEvent` に追加され、
サブスクライバーへの配信前に発行元によって値が設定される。

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)

```python
@dataclass(frozen=True)
class ShellPolicy:
    allowed_commands: frozenset[str]
    cwd_allowed_dirs: tuple[str, ...]
    default_cwd: str
    timeout_sec: int
    max_output_kb: int
    max_memory_mb: int
    kill_policy: str          # "sigterm_then_sigkill" | "sigkill_only"
    kill_grace_sec: float     # grace period before SIGKILL (sigterm_then_sigkill only)
    execution_user: str       # "" = no switch; non-empty requires root (CAP_SETUID)
    shell_path: str
    audit_log_path: str
    sandbox_backend: str      # "firejail" | "none"
    env_allowlist: tuple[str, ...]
    env_denylist: tuple[str, ...]
```

- 不変の `frozen=True` dataclass — FastAPI、MCP、エージェントへの依存はない(shared → external のみ)
- `mcp_servers/shell/service.py`(`ShellService`)がその設定オブジェクトとして使用する。値のみを保持し、業務ロジックは持たない
- **失敗時の意図 (Failure behavior):** `__post_init__` で以下を検証し、違反時は `ValueError` を送出する: `kill_policy` は `{"sigterm_then_sigkill", "sigkill_only"}` のいずれか、`sandbox_backend` は `{"firejail", "none"}` のいずれか、`timeout_sec >= 1`、`max_output_kb >= 1`、`max_memory_mb >= 1`、`kill_grace_sec >= 0` (Explicit in code: `scripts/shared/protocols/shell.py`)
- 目的: シェル実行ポリシーを MCP サーバー実装から分離すること
- Import: `from shared.protocols.shell import ShellPolicy`

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_01_types_and_protocols-core-types.md`
- `90_shared_02_03_types_and_protocols-reference.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`

## Keywords

ToolCallResult
ActionResult
ToolSpec
CacheEntry
PluginFailure
ToolDefinition
ArtifactEvent
ShellPolicy
DbConfig
