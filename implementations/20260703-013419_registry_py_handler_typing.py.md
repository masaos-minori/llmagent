# Implementation: scripts/agent/commands/registry.py — Relax _get_handler() typing to support no-argument exact handlers

**Plan source:** `plans/20260702-202815_plan.md` (Phase 1)
**Target file:** `scripts/agent/commands/registry.py`

---

## Goal

`_get_handler()` の戻り型を `Callable[..., Any]` に変更し、引数なしの exact-match ハンドラを正しく型付けする。あわせて `dispatch()` 内の `handler("")` 呼び出しを `handler()` に修正し、不要な空文字引数を除去する。

---

## Scope

**In:**
- `_get_handler()` の戻り型を `Callable[[str], None] | Callable[[str], Awaitable[None]]` から `Callable[..., Any]` に変更
- `Any` を `typing` からインポート追加（既存インポートスタイルに合わせて `collections.abc` または `typing` から）
- `_get_handler()` の未使用パラメータ `is_async: bool` を削除（positional-only `/` も不要になるため削除）
- `return handler` 行の `# type: ignore[no-any-return]` を削除（mypy が通れば）
- `dispatch()` 内: `self._get_handler(cmd, cmd.is_async)` → `self._get_handler(cmd)` に変更
- exact-match ブランチの `handler("")` → `handler()` に変更
- `await handler(args)` / `await handler("")` 行の `# type: ignore[misc]` を削除（mypy が通れば）

**Out:**
- コマンド署名フレームワークの全体再設計
- `/exit` ハンドリングの変更
- `_dispatch_plugin` の変更
- `command_defs.py` の変更

---

## Assumptions

1. `_get_handler()` は `registry.py` 内の `dispatch()` からのみ呼び出される（外部呼び出し元なし）。
2. `_get_handler()` の `is_async` パラメータは受け取るだけで内部では使用されておらず、削除しても `dispatch()` の動作は変わらない。
3. `dispatch()` は `cmd.is_async` を独立して参照するため、`_get_handler()` から `is_async` を除去しても await 判定ロジックは影響を受けない。
4. exact-match ハンドラ (`_cmd_help`, `_cmd_config`, `_cmd_stats`, `_cmd_context`, `_cmd_plan`, `_cmd_undo`, `_cmd_reload`, `_cmd_compact`) はいずれも引数なしで定義されていることを事前に確認する。

---

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. **インポート追加**
   - `from typing import Any` を追加する（既存の `from collections.abc import Awaitable, Callable` はそのまま維持）

2. **`_get_handler()` 更新**
   - シグネチャ変更: `def _get_handler(self, cmd: CommandDef, is_async: bool, /) -> ...` から `def _get_handler(self, cmd: CommandDef) -> Callable[..., Any]:`
   - `return handler` 行の `# type: ignore[no-any-return]` を削除

3. **`dispatch()` 呼び出し側の更新**
   - `handler = self._get_handler(cmd, cmd.is_async)` → `handler = self._get_handler(cmd)` に変更
   - exact-match ブランチ: `handler("")` → `handler()` に変更（async/sync 両方）
   - `await handler(args)` の `# type: ignore[misc]` を削除（mypy 確認後）
   - `await handler("")` に対応する `# type: ignore[misc]` を削除（handler() に変更後、mypy 確認後）

4. **事前確認（grep）**
   - exact-match ハンドラのシグネチャを grep で確認: `grep -n "def _cmd_help\|def _cmd_config\|def _cmd_stats\|def _cmd_context\|def _cmd_plan\|def _cmd_undo\|def _cmd_reload\|def _cmd_compact"` を実行し、全て引数なし (`self` のみ) であることを確認

5. **バリデーション**
   - `ruff check scripts/agent/commands/registry.py`
   - `mypy scripts/agent/commands/registry.py`
   - `uv run pytest tests/test_cmd_registry_ingest_removal.py tests/test_cmd_registry_note_removal.py tests/test_cmd_plugins.py tests/test_repl.py -x -q`
   - `uv run pytest -x -q`

### Method

Edit tool（既存ファイルの差分編集）

### Details

変更前の `_get_handler()`:
```python
def _get_handler(
    self, cmd: CommandDef, is_async: bool, /
) -> Callable[[str], None] | Callable[[str], Awaitable[None]]:
    handler = getattr(self, cmd.handler, None)
    if handler is None:
        raise AttributeError(
            f"CommandRegistry has no handler method {cmd.handler!r}"
        )
    return handler  # type: ignore[no-any-return]
```

変更後の `_get_handler()`:
```python
def _get_handler(self, cmd: CommandDef) -> Callable[..., Any]:
    handler = getattr(self, cmd.handler, None)
    if handler is None:
        raise AttributeError(
            f"CommandRegistry has no handler method {cmd.handler!r}"
        )
    return handler
```

変更前の `dispatch()` 内 exact-match ブランチ:
```python
handler = self._get_handler(cmd, cmd.is_async)
...
if cmd.is_async:
    await handler("")  # type: ignore[misc]
else:
    handler("")
```

変更後:
```python
handler = self._get_handler(cmd)
...
if cmd.is_async:
    await handler()
else:
    handler()
```

prefix ブランチの `await handler(args)` は引き続き `str` を渡すため変更なし。`# type: ignore[misc]` は mypy 確認後に削除する。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 事前 grep | `grep -n "def _cmd_help\|def _cmd_config\|def _cmd_stats\|def _cmd_context\|def _cmd_plan\|def _cmd_undo\|def _cmd_reload\|def _cmd_compact" scripts/agent/commands/*.py` | 全ハンドラが `(self)` のみのシグネチャであること |
| Lint | `ruff check scripts/agent/commands/registry.py` | 0 errors |
| Type check | `mypy scripts/agent/commands/registry.py` | no new errors |
| Tests (targeted) | `uv run pytest tests/test_cmd_registry_ingest_removal.py tests/test_cmd_registry_note_removal.py tests/test_cmd_plugins.py tests/test_repl.py -x -q` | all pass |
| Tests (full) | `uv run pytest -x -q` | all pass |
