# Implementation: tests/ — Update all test files importing from agent.config to direct modules

**Plan source:** `plans/20260702-202905_plan.md` (Phase 2 (steps 6-9))
**Target file:** `tests/`

---

## Goal

tests/ 配下の全テストファイルで `agent.config` からのインポートを `agent.config_dataclasses` または `agent.config_builders` の直接インポートに置き換え、re-export スタブへの依存を除去する。

---

## Scope

**In:**
- `test_config_loader.py`: `MemoryConfig` -> `config_dataclasses` から
- `test_tool_approval_repos.py`: `AgentConfig` -> `config_dataclasses`、`build_agent_config` -> `config_builders`
- `test_cmd_config_char.py`: inspect シンボルを確認し、種類によってインポートを 2 行に分割
- `test_tool_result_formatter.py`: `AgentConfig` -> `config_dataclasses`
- `test_tool_approval_paths.py`: `AgentConfig` -> `config_dataclasses`
- `test_plugin_ci_strict.py`: `build_agent_config` -> `config_builders`
- `test_tool_approval_preflight.py`: シンボル種類に応じて振り分け
- `test_tool_policy_comprehensive.py`: シンボル種類に応じて振り分け
- `test_tool_policy.py`: シンボル種類に応じて振り分け
- `test_tool_loop_guard.py`: シンボル種類に応じて振り分け
- `test_rag_get_cfg.py`: deferred import の `ConfigLoadError`, `load_config` -> `config_builders`
- `test_tool_audit.py`: シンボル種類に応じて振り分け
- `test_tool_runner.py`: シンボル種類に応じて振り分け
- `test_tool_approval_risk.py`: シンボル種類に応じて振り分け
- `test_llm_client.py`: 587 行目 deferred import の `build_agent_config` -> `config_builders`

**Out:**
- テストのロジック変更
- テストの追加・削除

---

## Assumptions

1. builder 系シンボル (`build_agent_config`, `_build_mcp_servers`, `ConfigLoadError`, `load_config` など) は `agent.config_builders` に定義されている
2. dataclass 系シンボル (`AgentConfig`, `MemoryConfig` など) は `agent.config_dataclasses` に定義されている
3. 両方の種類のシンボルをインポートしているファイルはインポートを 2 行に分割する
4. deferred import の `# noqa: PLC0415` は保持する

---

## Implementation

### Target file

`tests/`

### Procedure

1. 各テストファイルを Read ツールで開き、`from agent.config import` の行を特定する
2. インポートしているシンボルをリストアップし、builder 系と dataclass 系に分類する
3. dataclass 系シンボルがある場合: `from agent.config_dataclasses import <symbols>` に変更
4. builder 系シンボルがある場合: `from agent.config_builders import <symbols>` に変更
5. 両方ある場合: 1 行を 2 行に分割
6. deferred import (関数スコープ内) の場合は `# noqa: PLC0415` を保持
7. 各ファイル変更後に `uv run pytest -x -q` を実行して動作を確認する

### Method

Edit tool でコード変更

### Details

振り分けルール:
- **-> `agent.config_dataclasses`**: `AgentConfig`, `MemoryConfig` などのデータクラス/型
- **-> `agent.config_builders`**: `build_agent_config`, `_build_mcp_servers`, `_CONFIG_DIR`, `ConfigLoadError`, `load_config` などのビルダー/関数/例外/定数

インポート分割パターン (両方の種類がある場合):
```python
# Before
from agent.config import AgentConfig, build_agent_config

# After
from agent.config_dataclasses import AgentConfig
from agent.config_builders import build_agent_config
```

deferred import パターン (test_rag_get_cfg.py, test_llm_client.py):
```python
# Before
from agent.config import ConfigLoadError, load_config  # noqa: PLC0415

# After
from agent.config_builders import ConfigLoadError, load_config  # noqa: PLC0415
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check tests/ | 0 errors |
| Type check | mypy tests/ | no new errors |
| Tests | uv run pytest | all pass |
