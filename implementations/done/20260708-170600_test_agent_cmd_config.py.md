# Implementation: M-2 — Update partial-completion assertions in test_agent_cmd_config.py

## Goal

Update `test_partial_completion_hint_shown_when_count_positive` and
`test_partial_completion_no_hint_when_zero` to assert on `"session_diagnostics"` instead of
`"llm_partial_completion"`, matching the `/stats` display text change already specified in
`implementations/20260708-163521_cmd_config_stats.py.md` (an H-4 doc whose target string is
identical to this plan's — see that doc for the source-code change itself, which is NOT
duplicated here).

## Scope

**Target**: `tests/test_agent_cmd_config.py`

**Already covered elsewhere — do not duplicate**: the source change to
`scripts/agent/commands/cmd_config_stats.py` is fully specified by
`implementations/20260708-163521_cmd_config_stats.py.md` (H-4), whose target string
(`"  (stored in session_diagnostics)"`) is byte-for-byte identical to this plan's Design section.
This doc covers ONLY the test file, which H-4's doc did not catch — H-4's own risk-check grepped
for the literal string `"stored as tool_result"` appearing as SOURCE TEXT in test files, but this
test file's assertions check for the substring `"llm_partial_completion"` in the FUNCTION'S
RUNTIME OUTPUT (`capsys.readouterr().out`), not as literal source text — a different grep pattern
that H-4's check did not cover. This is a genuine, confirmed gap: running
`grep -n "llm_partial_completion" tests/test_agent_cmd_config.py` shows two real assertions that
will break once the H-4 source change lands.

**Depends on**: `scripts/agent/commands/cmd_config_stats.py`'s change (per the H-4 doc) already
applied (or applied together with this doc).

**Out of scope**: `test_cmd_stats_with_llm_service_prints_sse_stats`,
`test_cmd_stats_with_llm_service_shows_correct_values`,
`test_cmd_stats_without_llm_service_shows_zeros` — none of these assert on
`"llm_partial_completion"` or `"tool_result"`; all check `"Partial compl"` (the label prefix,
unaffected by this change) or numeric values.

## Assumptions

1. `_make_llm_svc()` and `_make_ctx()` (shared fixtures) need no changes — only the two
   assertion lines themselves change.

## Implementation

### Target file

`tests/test_agent_cmd_config.py`

### Procedure

#### Step 1: Confirm the two assertion lines

```bash
grep -n "llm_partial_completion" tests/test_agent_cmd_config.py
```

Expected: two matches, at `test_partial_completion_hint_shown_when_count_positive` (line ~107)
and `test_partial_completion_no_hint_when_zero` (line ~117).

#### Step 2: Update `test_partial_completion_hint_shown_when_count_positive`

Current:

```python
    def test_partial_completion_hint_shown_when_count_positive(
        self, capsys: Any
    ) -> None:
        ctx = _make_ctx()
        llm = _make_llm_svc()
        llm.stat_partial_completions = 2
        ctx.services_required.llm = llm
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "llm_partial_completion" in out
```

Replace the final assertion line with:

```python
        assert "session_diagnostics" in out
```

#### Step 3: Update `test_partial_completion_no_hint_when_zero`

Current:

```python
    def test_partial_completion_no_hint_when_zero(self, capsys: Any) -> None:
        ctx = _make_ctx()
        llm = _make_llm_svc()
        llm.stat_partial_completions = 0
        ctx.services_required.llm = llm
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "llm_partial_completion" not in out
        assert "Partial compl : 0" in out
```

Replace the `assert "llm_partial_completion" not in out` line with:

```python
        assert "session_diagnostics" not in out
```

The `assert "Partial compl : 0" in out` line stays unchanged.

### Method

- Two single-line assertion replacements; no other test logic, fixture, or method signature
  changes.
- Function names are NOT renamed (unlike some other H-x/M-x test docs in this rollout) since
  `test_partial_completion_hint_shown_when_count_positive` /
  `test_partial_completion_no_hint_when_zero` already describe behavior generically enough
  (hint shown/not-shown) that they remain accurate regardless of the hint's exact wording.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_agent_cmd_config.py` | 0 errors |
| Type check | `mypy tests/test_agent_cmd_config.py` | no new errors |
| Grep (old substring gone from assertions) | `grep -n "llm_partial_completion" tests/test_agent_cmd_config.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_agent_cmd_config.py -v` | all pass once the companion `cmd_config_stats.py` source change (H-4 doc) is applied |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
