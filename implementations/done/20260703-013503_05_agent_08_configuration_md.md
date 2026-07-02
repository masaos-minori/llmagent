# Implementation: docs/05_agent_08_configuration.md — Fix deprecated agent.config references

**Plan source:** `plans/20260702-202849_plan.md` (Phase 2)
**Target file:** `docs/05_agent_08_configuration.md`

---

## Goal

`docs/05_agent_08_configuration.md` 内の `agent.config` シムへの参照をすべて正規の `agent.config_builders` / `agent.config_dataclasses` モジュール参照に置き換える。`build_agent_config()` のソース参照を `agent/config.py:627` から `agent/config_builders.py` に修正する。

---

## Scope

**In:**
- `build_agent_config()` の参照元を `agent/config.py:627` -> `agent/config_builders.py` (正しい行番号) に変更
- `from agent.config import` 形式のインポート例を `from agent.config_builders import` / `from agent.config_dataclasses import` に置換
- `_cast_enums()` が公開 API として記述されていた場合、非公開 API 旨の注記を追加

**Out:**
- ランタイム動作の変更
- シムファイル (`agent/config.py`) の削除
- テストファイルの import 修正

---

## Assumptions

1. `agent/config.py` はシムであり、`build_agent_config` の実装は `agent/config_builders.py` に存在する。
2. ドキュメント内のインポート例は読者が実際に使用する正規パスを示すべきであり、シムパスは掲載しない。

---

## Implementation

### Target file

`docs/05_agent_08_configuration.md`

### Procedure

1. Phase 1 監査: `docs/05_agent_08_configuration.md` を全文読み込み、`agent.config` 参照箇所を特定する。
2. `build_agent_config() (agent/config.py:627)` の記述を `build_agent_config() (agent/config_builders.py)` に変更する（正しい行番号があれば付記）。
3. `from agent.config import` 形式のインポート例をすべて `from agent.config_builders import` または `from agent.config_dataclasses import` に置換する。
4. `_cast_enums()` が公開 API として記述されている場合、次の注記を追加する:
   > "Not a public API. TOML string-to-enum conversion is performed by the config builder (agent/config_builders.py), not inside the dataclass."

### Method

Edit tool で対象ファイルを直接編集する。変更前に Read ツールで全文読み込みを実施すること。

### Details

- 検索対象パターン: `agent\.config`, `agent/config\.py`, `_cast_enums`
- 置換先:
  - `agent.config_builders` — `build_agent_config`, `load_config`, `ConfigLoadError`
  - `agent.config_dataclasses` — `AgentConfig`, `LLMConfig`, `RAGConfig` などのデータクラス
- `agent/config.py:627` -> `agent/config_builders.py` (行番号は実際のファイルを grep して確認)

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Grep 確認 | `grep -n "agent\.config\|agent/config\.py" docs/05_agent_08_configuration.md` | 0件 (シム参照なし) |
| Lint | `ruff check docs/` | 0 errors |
| Type check | `mypy docs/` | no new errors (対象外だが念のため) |
| Tests | `uv run pytest` | all pass |
