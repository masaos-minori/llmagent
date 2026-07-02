# Implementation: scripts/agent/config_builders.py — Remove re-export comment from module docstring

**Plan source:** `plans/20260702-202905_plan.md` (Phase 3 (step 10))
**Target file:** `scripts/agent/config_builders.py`

---

## Goal

scripts/agent/config_builders.py の 20 行目付近のコメントから "— re-exported via agent.config" という記述を削除し、もはや存在しない re-export スタブへの言及を除去する。

---

## Scope

**In:**
- 20 行目のコメント内 "— re-exported via agent.config" の文言を削除

**Out:**
- `# noqa: F401` の削除 (シンボルが本モジュールからエクスポートされている場合は保持)
- それ以外のコードや処理の変更

---

## Assumptions

1. 対象コメントは `# noqa: F401` を含む行または直前行にある
2. `# noqa: F401` はシンボルがこのモジュールでも re-export されている場合に必要なため保持する
3. 変更は 1 行のみのコメント編集で完結する

---

## Implementation

### Target file

`scripts/agent/config_builders.py`

### Procedure

1. `scripts/agent/config_builders.py` を開き、20 行目付近の "— re-exported via agent.config" を含むコメントを特定する
2. その文言のみを削除し、他の内容 (`# noqa: F401` など) は保持する
3. `ruff check scripts/agent/config_builders.py` を実行して確認する

### Method

Edit tool でコメント編集

### Details

変更パターン例:
```python
# Before
# build_agent_config — re-exported via agent.config  # noqa: F401

# After
# build_agent_config  # noqa: F401
```

または行内のコメント文字列が前後にある場合も同様に "— re-exported via agent.config" 部分のみを除去する。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check scripts/agent/config_builders.py | 0 errors |
| Type check | mypy scripts/agent/config_builders.py | no new errors |
| Tests | uv run pytest | all pass |
