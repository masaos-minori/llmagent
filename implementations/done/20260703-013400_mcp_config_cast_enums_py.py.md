# Implementation: scripts/shared/mcp_config.py — Remove _cast_enums() shim and add _validate_enum_types()

**Plan source:** `plans/20260702-202756_plan.md` (Phase 1)
**Target file:** `scripts/shared/mcp_config.py`

---

## Goal

McpServerConfig の _cast_enums() 互換シムを削除し、文字列を列挙型にキャストする代わりに isinstance チェックで不正な入力を即座に ValueError として弾く検証メソッドに置き換える。

---

## Scope

**In:**
- _cast_enums() メソッド本体および定義の削除
- __post_init__() からの self._cast_enums() 呼び出しの削除
- _validate_enum_types() メソッドの追加 (transport, startup_mode, healthcheck_mode の isinstance チェック、失敗時は ValueError)
- __post_init__() を self._validate_enum_types() → self._validate_cross_fields() の順で呼び出すよう更新

**Out:**
- _validate_cross_fields() の変更
- 他のクラスや他ファイルへの変更
- startup_mode / healthcheck_mode が Optional である場合の None 許容ロジックの変更 (既存の None 許容挙動はそのまま維持)

---

## Assumptions

1. transport は TransportType 型、startup_mode は StartupMode 型、healthcheck_mode は HealthcheckMode 型として定義されており、それぞれ None を許容するかどうかは既存フィールド定義に従う
2. _validate_cross_fields() は既存のまま変更なしで利用可能である

---

## Implementation

### Target file

`scripts/shared/mcp_config.py`

### Procedure

1. scripts/shared/mcp_config.py を Read して現在の _cast_enums() 実装と __post_init__() の内容を確認する
2. _cast_enums() メソッド全体 (定義から末尾まで) を削除する
3. __post_init__() 内の self._cast_enums() 呼び出し行を削除する
4. 以下の _validate_enum_types() メソッドを追加する:
   - transport が TransportType のインスタンスでなければ ValueError を raise する
   - startup_mode が None でなく StartupMode のインスタンスでもなければ ValueError を raise する
   - healthcheck_mode が None でなく HealthcheckMode のインスタンスでもなければ ValueError を raise する
   - ValueError のメッセージは型名と受け取った値の型を含める
5. __post_init__() を以下の順序で呼び出すよう更新する:
   - self._validate_enum_types()
   - self._validate_cross_fields()

### Method

Edit tool でコード変更を適用する

### Details

_validate_enum_types() の実装例:

```python
def _validate_enum_types(self) -> None:
    if not isinstance(self.transport, TransportType):
        raise ValueError(
            f"transport must be a TransportType instance, got {type(self.transport)!r}"
        )
    if self.startup_mode is not None and not isinstance(self.startup_mode, StartupMode):
        raise ValueError(
            f"startup_mode must be a StartupMode instance, got {type(self.startup_mode)!r}"
        )
    if self.healthcheck_mode is not None and not isinstance(self.healthcheck_mode, HealthcheckMode):
        raise ValueError(
            f"healthcheck_mode must be a HealthcheckMode instance, got {type(self.healthcheck_mode)!r}"
        )
```

__post_init__() の更新後:

```python
def __post_init__(self) -> None:
    self._validate_enum_types()
    self._validate_cross_fields()
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 動作確認 (正常) | python -c "from scripts.shared.mcp_config import McpServerConfig, TransportType; McpServerConfig(TransportType.HTTP, 'http://127.0.0.1:8000')" | エラーなし |
| 動作確認 (異常) | python -c "from scripts.shared.mcp_config import McpServerConfig; McpServerConfig('http', 'http://127.0.0.1:8000')" | ValueError が raise される |
| Lint | ruff check scripts/shared/mcp_config.py | 0 errors |
| Type check | mypy scripts/shared/mcp_config.py | no new errors |
| Tests | uv run pytest | all pass |
