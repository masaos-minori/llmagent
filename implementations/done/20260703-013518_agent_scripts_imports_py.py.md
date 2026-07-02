# Implementation: scripts/agent/ — Update four script files to remove agent.config re-export imports

**Plan source:** `plans/20260702-202905_plan.md` (Phase 1 (steps 2-5))
**Target file:** `scripts/agent/`

---

## Goal

scripts/agent/ 配下の 4 ファイルで `agent.config` からのインポートを `agent.config_dataclasses` または `agent.config_builders` の直接インポートに置き換え、re-export スタブへの依存を除去する。

---

## Scope

**In:**
- `scripts/agent/tool_policy.py` TYPE_CHECKING ブロック: `from agent.config import AgentConfig` -> `from agent.config_dataclasses import AgentConfig`
- `scripts/agent/tool_result_formatter.py` TYPE_CHECKING ブロック: 同上
- `scripts/agent/services/config_reload.py` 382 行目 deferred import: `from agent.config import (_build_mcp_servers,...)` -> `from agent.config_builders import _build_mcp_servers`; `# noqa: PLC0415` を保持
- `scripts/agent/commands/cmd_config_display.py` 216 行目 deferred import: `from agent.config import (_CONFIG_DIR,)` -> `from agent.config_builders import _CONFIG_DIR`; `# noqa: PLC0415` を保持

**Out:**
- それ以外のロジックや処理の変更
- noqa コメントの除去

---

## Assumptions

1. `AgentConfig` は `agent.config_dataclasses` に定義されており、TYPE_CHECKING ブロックで安全にインポート可能
2. `_build_mcp_servers` は `agent.config_builders` に定義されている
3. `_CONFIG_DIR` は `agent.config_builders` に定義されている
4. deferred import の `# noqa: PLC0415` は関数スコープ内インポートに必要なため保持する

---

## Implementation

### Target file

`scripts/agent/`

### Procedure

1. `scripts/agent/tool_policy.py` を開き、TYPE_CHECKING ブロック内の `from agent.config import AgentConfig` を `from agent.config_dataclasses import AgentConfig` に変更する。`uv run pytest -x -q` を実行する。
2. `scripts/agent/tool_result_formatter.py` を開き、TYPE_CHECKING ブロック内の `from agent.config import AgentConfig` を `from agent.config_dataclasses import AgentConfig` に変更する。`uv run pytest -x -q` を実行する。
3. `scripts/agent/services/config_reload.py` 382 行目付近の deferred import `from agent.config import (_build_mcp_servers,...)` を `from agent.config_builders import _build_mcp_servers` に変更する。`# noqa: PLC0415` を保持する。`uv run pytest -x -q` を実行する。
4. `scripts/agent/commands/cmd_config_display.py` 216 行目付近の deferred import `from agent.config import (_CONFIG_DIR,)` を `from agent.config_builders import _CONFIG_DIR` に変更する。`# noqa: PLC0415` を保持する。`uv run pytest -x -q` を実行する。

### Method

Edit tool でコード変更

### Details

各ファイルの変更パターン:

**tool_policy.py / tool_result_formatter.py (TYPE_CHECKING ブロック):**
```python
# Before
from agent.config import AgentConfig

# After
from agent.config_dataclasses import AgentConfig
```

**config_reload.py (deferred import):**
```python
# Before
from agent.config import (_build_mcp_servers, ...)  # noqa: PLC0415

# After
from agent.config_builders import _build_mcp_servers  # noqa: PLC0415
```

**cmd_config_display.py (deferred import):**
```python
# Before
from agent.config import (_CONFIG_DIR,)  # noqa: PLC0415

# After
from agent.config_builders import _CONFIG_DIR  # noqa: PLC0415
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check scripts/agent/tool_policy.py scripts/agent/tool_result_formatter.py scripts/agent/services/config_reload.py scripts/agent/commands/cmd_config_display.py | 0 errors |
| Type check | mypy scripts/agent/ | no new errors |
| Tests | uv run pytest -x -q | all pass (after each file change) |
