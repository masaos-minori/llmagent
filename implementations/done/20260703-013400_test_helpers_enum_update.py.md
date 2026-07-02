# Implementation: tests/ — テストヘルパー内の文字列リテラルを列挙型インスタンスに置き換え

**Plan source:** `plans/20260702-202756_plan.md` (Phase 2)
**Target file:** `tests/`

---

## Goal

テストヘルパー関数内で McpServerConfig に渡している transport/startup_mode/healthcheck_mode の文字列リテラルを、対応する列挙型インスタンス (TransportType, StartupMode, HealthcheckMode) に置き換える。Phase 1 で _cast_enums() が削除されると文字列渡しは ValueError になるため、テスト側を先に修正する。

---

## Scope

**In:**
- tests/test_route_resolver.py 14行目: McpServerConfig("http",...) を McpServerConfig(TransportType.HTTP,...) に変更
- tests/test_cmd_mcp.py 47行目: transport="http" を TransportType.HTTP に変更; _stdio() ヘルパー (53-59行目) の文字列リテラルを列挙型に変換、または不要なら削除
- tests/test_lifecycle.py: _http_cfg() と _http_subprocess_cfg() 内の "http" を TransportType.HTTP、"subprocess" を StartupMode.SUBPROCESS に変更; _stdio_* および _ondemand_* ヘルパー内の不正な列挙文字列をすべて列挙型インスタンスに変換または削除

**Out:**
- テストロジック (assert 内容) の変更
- Phase 1 の mcp_config.py 変更

---

## Assumptions

1. tests/test_route_resolver.py、tests/test_cmd_mcp.py、tests/test_lifecycle.py の 3 ファイルが対象であり、他のテストファイルには McpServerConfig への文字列渡しは存在しない
2. _stdio() / _stdio_* / _ondemand_* ヘルパーが有効な列挙値を文字列で渡している場合はインスタンスへの置き換えで対応し、そもそも無効な文字列を渡すことをテストしているヘルパーであれば削除・書き換えが必要である

---

## Implementation

### Target file

`tests/test_route_resolver.py`, `tests/test_cmd_mcp.py`, `tests/test_lifecycle.py`

### Procedure

1. 各対象ファイルを Read して現在の McpServerConfig 呼び出し箇所を確認する
2. tests/test_route_resolver.py:
   - 14行目の McpServerConfig("http",...) を McpServerConfig(TransportType.HTTP,...) に変更する
   - ファイル冒頭に TransportType の import がなければ追加する
3. tests/test_cmd_mcp.py:
   - 47行目の transport="http" を transport=TransportType.HTTP に変更する
   - _stdio() ヘルパー (53-59行目) 内の文字列リテラルを列挙型インスタンスに変更する
   - ファイル冒頭に必要な列挙型の import を追加する
4. tests/test_lifecycle.py:
   - _http_cfg() 内の "http" を TransportType.HTTP に変更する
   - _http_subprocess_cfg() 内の "http" を TransportType.HTTP、"subprocess" を StartupMode.SUBPROCESS に変更する
   - _stdio_* ヘルパー内の文字列リテラルを TransportType.STDIO 等の列挙型インスタンスに変更する
   - _ondemand_* ヘルパー内の文字列リテラルを適切な列挙型インスタンスに変更する
   - ファイル冒頭に必要な列挙型の import を追加する
5. 変更後、テストファイル内に McpServerConfig へ文字列リテラルを transport/startup_mode/healthcheck_mode として渡している箇所がゼロであることを grep で確認する

### Method

Edit tool でコード変更を適用する。変更前に各ファイルを Read tool で確認すること。

### Details

import 追加パターン (既存 import ブロックに追記):

```python
from scripts.shared.mcp_config import TransportType, StartupMode, HealthcheckMode
```

文字列から列挙型への変換マッピング:
- "http" → TransportType.HTTP
- "stdio" → TransportType.STDIO
- "subprocess" → StartupMode.SUBPROCESS
- "ondemand" → StartupMode.ONDEMAND (存在する場合)

確認用 grep コマンド:

```bash
grep -n 'McpServerConfig(' tests/test_route_resolver.py tests/test_cmd_mcp.py tests/test_lifecycle.py
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 文字列渡し残存確認 | grep -rn '"http"\|"stdio"\|"subprocess"' tests/test_route_resolver.py tests/test_cmd_mcp.py tests/test_lifecycle.py | McpServerConfig の引数としての文字列リテラルが 0 件 |
| Lint | ruff check tests/test_route_resolver.py tests/test_cmd_mcp.py tests/test_lifecycle.py | 0 errors |
| Type check | mypy tests/test_route_resolver.py tests/test_cmd_mcp.py tests/test_lifecycle.py | no new errors |
| Tests | uv run pytest tests/test_route_resolver.py tests/test_cmd_mcp.py tests/test_lifecycle.py | all pass |
| Full tests | uv run pytest | all pass |
