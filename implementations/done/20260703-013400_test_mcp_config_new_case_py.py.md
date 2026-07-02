# Implementation: tests/test_mcp_config.py — 有効な文字列値を列挙型インスタンスとして渡さない場合の拒否テストを追加

**Plan source:** `plans/20260702-202756_plan.md` (Phase 3)
**Target file:** `tests/test_mcp_config.py`

---

## Goal

Phase 1 で追加した _validate_enum_types() の動作を検証するため、文字列 "http" を transport に渡した場合に ValueError が raise されることを確認するテストを tests/test_mcp_config.py に追加する。

---

## Scope

**In:**
- test_valid_string_transport_rejected() テスト関数の追加: McpServerConfig("http", "http://127.0.0.1:8000") を呼び出し ValueError が raise されることを assert する

**Out:**
- 既存テストの変更
- 無効な文字列値 (存在しない transport 名など) のテスト (本テストは「有効な文字列値でも列挙型インスタンスでなければ拒否される」ことを確認するもの)

---

## Assumptions

1. tests/test_mcp_config.py が既に存在し、McpServerConfig の他のテストが含まれている
2. pytest.raises(ValueError) パターンが既存テストで使用されているか、または標準的な pytest の使用が可能である

---

## Implementation

### Target file

`tests/test_mcp_config.py`

### Procedure

1. tests/test_mcp_config.py を Read して既存のテスト構造と import を確認する
2. ファイル末尾 (または適切なテストクラス内) に test_valid_string_transport_rejected() を追加する:
   - McpServerConfig("http", "http://127.0.0.1:8000") を pytest.raises(ValueError) コンテキストマネージャ内で呼び出す
   - テスト名に "valid_string" を含め、「有効な文字列値だが列挙型インスタンスでない」ケースであることを明示する
3. pytest が未 import であれば import を追加する

### Method

Edit tool でコードを追加する。追加前に Read tool でファイル内容を確認すること。

### Details

追加するテスト関数:

```python
def test_valid_string_transport_rejected() -> None:
    """'http' is a valid transport string value but not a TransportType instance — must be rejected."""
    with pytest.raises(ValueError):
        McpServerConfig("http", "http://127.0.0.1:8000")
```

テスト名の命名根拠:
- "valid_string" = 文字列の内容自体は TransportType.HTTP に対応する有効な値
- "rejected" = 列挙型インスタンスでないため拒否される
- 「無効な文字列値 (例: "ftp") が拒否される」テストとは明確に区別される

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 新規テスト単体 | uv run pytest tests/test_mcp_config.py::test_valid_string_transport_rejected -v | PASSED |
| 既存テスト影響確認 | uv run pytest tests/test_mcp_config.py | all pass |
| Lint | ruff check tests/test_mcp_config.py | 0 errors |
| Type check | mypy tests/test_mcp_config.py | no new errors |
| Full tests | uv run pytest | all pass |
