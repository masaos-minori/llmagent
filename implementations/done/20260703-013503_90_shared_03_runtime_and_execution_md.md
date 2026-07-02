# Implementation: docs/90_shared_03_runtime_and_execution.md — Clarify _cast_enums() as non-public API

**Plan source:** `plans/20260702-202849_plan.md` (Phase 2)
**Target file:** `docs/90_shared_03_runtime_and_execution.md`

---

## Goal

`docs/90_shared_03_runtime_and_execution.md` の §11 McpServerConfig セクションを読み込み、`_cast_enums()` が公開 API として記述されている場合に非公開旨の注記を追加する。文字列→enum 変換が public contract であるかのような記述を削除または明確化する。

---

## Scope

**In:**
- §11 McpServerConfig セクションの `_cast_enums()` に関する記述の確認
- `_cast_enums()` が公開 API として記述されている場合の非公開注記追加
- 文字列→enum の直接強制変換が public contract であることを示唆する記述の削除・明確化

**Out:**
- ランタイム動作の変更
- `McpServerConfig` データクラス自体の変更
- `agent.config` 参照の修正 (Target 1 担当)

---

## Assumptions

1. `McpServerConfig._cast_enums()` はランタイムの互換性のためにソースコードに残っているが、外部から呼び出す public API ではない。
2. TOML 文字列→enum 変換は `agent/config_builders.py` のコンフィグビルダーが担当し、データクラス内部では実施しない。

---

## Implementation

### Target file

`docs/90_shared_03_runtime_and_execution.md`

### Procedure

1. `docs/90_shared_03_runtime_and_execution.md` を全文読み込み、§11 McpServerConfig セクションを特定する。
2. `_cast_enums()` の記述を確認する。
   - 公開 API として記述されている場合 → 手順 3 を実施する。
   - 記述がない / 既に非公開として明示されている場合 → 変更不要。
3. 該当箇所に次の注記を追加する（既存テキストの直後またはコードブロック末尾）:
   > "Not a public API. TOML string-to-enum conversion is performed by the config builder (agent/config_builders.py), not inside the dataclass."
4. 「直接 string-enum 強制変換が public contract」を示唆する記述があれば削除または次のように書き換える:
   > "Transport strings in TOML are converted to enum values by the config builder (agent/config_builders.py) before being stored in McpServerConfig."

### Method

Read ツールで全文確認後、Edit ツールで対象箇所を編集する。

### Details

- 検索対象: `_cast_enums`, `string-to-enum`, `McpServerConfig` 周辺のコードブロック
- 追加する注記のキーフレーズ: "Not a public API", "config builder (agent/config_builders.py)"
- `_cast_enums` への言及がゼロであれば本ファイルへの変更は不要

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Grep 確認 | `grep -n "_cast_enums" docs/90_shared_03_runtime_and_execution.md` | 0件 または注記付きのみ |
| Lint | `ruff check docs/` | 0 errors |
| Type check | `mypy docs/` | no new errors |
| Tests | `uv run pytest` | all pass |
