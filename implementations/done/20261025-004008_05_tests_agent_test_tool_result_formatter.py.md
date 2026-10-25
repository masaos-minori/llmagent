# Implementation Procedure: tests/agent/test_tool_result_formatter.py

## Goal

Add default-config end-to-end masking tests proving that a directly constructed `ToolConfig`
masks `write_file`/`edit_file`-shaped arguments at the real key names (`content`,
`old_text`, `new_text`), including nested `edits` entries.

## Scope

In scope:
- New import line and new test class `TestMaskArgsDefaultConfig` (new) with two tests in
  `tests/agent/test_tool_result_formatter.py`.

Out of scope:
- Existing test classes (`TestMaskArgs`, `TestBuildPreview`, etc.) — untouched.
- Code defaults (procedures 01-02), config (procedure 03), pin update (procedure 04),
  audit case (procedure 06), docs (procedure 07).

## Assumptions

- Assumption: the file's `_cfg` helper hardcodes `masked_fields: []` in its builder
  defaults (verified at `:36`), so it cannot express the default path without changing
  every existing consumer. Direct `ToolConfig()` construction is the chosen default path —
  it is the dataclass path REQ-003 pins.
- Assumption: nested masking already works — `mask_args` recurses dicts and lists (verified
  at `scripts/agent/tool_result_formatter.py:42-54`, commit `3cdacc601`), and this file
  already proves nesting with explicit lists (`test_masks_key_in_list_of_dicts`).
- Assumption: these tests fail (red) against the current `["file_content"]` default —
  expected per plan Phase 1 — and go green once procedures 01-02 land.

## Design decisions

- Decision: construct `ToolConfig()` directly instead of extending the `_cfg` builder
  helper; the helper's hardcoded `[]` keeps every existing test hermetic, and adding a
  default-path fixture via the helper would silently flip behavior of unrelated tests.
- Decision: the first test also asserts the default list equals the frozen triple — a
  cheap drift guard mirroring AC-1 without duplicating procedure 04's builder pin.
- Decision: test secrets are literal sentinel strings (`s3cr3t`, `s3cr3t-old`,
  `s3cr3t-new`), matching the file's existing `secret123`-style fixtures.

## Alternatives considered

- Alternative: reuse `_cfg` with a `masked_fields` override. Rejected: an explicit override
  no longer tests the default path the Issue is about.
- Alternative: test through `tool_audit`/`tool_approval` sinks instead. Rejected: sink
  coverage for the audit path is procedure 06's job; here the unit under test is the
  default value flowing into `mask_args`.

## Implementation

### Target file

`tests/agent/test_tool_result_formatter.py`

### Procedure

1. Add `ToolConfig` to the existing `agent.config_dataclasses` import line (`:8`).
2. Append the new test class after `TestMaskArgs` (class ends before `TestBuildPreview` at
   `:118`).

### Method

New import (edit of existing line):

```python
from agent.config_dataclasses import AgentConfig, ToolConfig
```

New class, added after `TestMaskArgs`:

```python
class TestMaskArgsDefaultConfig:
    def test_default_masks_write_file_content(self) -> None:
        masked_fields = ToolConfig().masked_fields
        assert masked_fields == ["content", "old_text", "new_text"]
        result = mask_args({"path": "/tmp/f.txt", "content": "s3cr3t"}, masked_fields)
        assert result == {"path": "/tmp/f.txt", "content": "***"}

    def test_default_masks_edit_file_nested_edits(self) -> None:
        result = mask_args(
            {
                "path": "/tmp/f.txt",
                "edits": [{"old_text": "s3cr3t-old", "new_text": "s3cr3t-new"}],
            },
            ToolConfig().masked_fields,
        )
        assert result["edits"][0]["old_text"] == "***"
        assert result["edits"][0]["new_text"] == "***"
```

No existing tests or fixtures change.

### Details

- `ToolConfig` is the dataclass at `scripts/agent/config_dataclasses.py:154` whose
  `masked_fields` field (procedure 01) these tests pin behaviorally.
- Run in plan Phase 1, before procedures 01-02: both tests must fail against the current
  default (`content`/`old_text`/`new_text` pass through unmasked), then pass after.
- Existing explicit-name tests such as `test_masks_nested_dict` (which masks a key literally
  named `file_content`) stay green throughout — they pass their own mask lists.

## Compatibility considerations

- No public API or fixture changes; existing classes keep their behavior (AC-6).
- Until procedures 01-02 land, this file has two failing tests by design; the plan Phase 2
  gate command includes this file and must be run after all of 01-04.

## Security considerations

- These tests are the behavioral regression guard for REQ-001: if the default ever drifts
  back to a name no tool accepts, they fail.
- Sentinel values only; no real secrets in test data.

## Rollback considerations

- Rollback: delete the new class and revert the import line; the suite returns to its
  pre-change state with no coupling to other files.
- Safe to revert independently of procedures 01-04 (unlike the pin in procedure 04, which
  must revert with the code defaults).

## Validation plan

1. Phase 1 (before code change): `uv run pytest tests/agent/test_tool_result_formatter.py
   -q` shows the two new tests failing against the current default (expected red).
2. After procedures 01-02: same command is fully green.
3. Full gate: `uv run pytest tests/agent -q` and `uv run mypy scripts/ tests/ --strict`
   (mypy validates the `list[str]` flows in the new tests).

## Completion criteria

- `TestMaskArgsDefaultConfig` (new) contains both tests and passes against the new default.
- The write-file test asserts the exact frozen default list.
- The nested test proves `edits[0]["old_text"]` and `edits[0]["new_text"]` become `***`.

## Out of Scope

- Existing test classes and fixtures in this file.
- Audit-path coverage (procedure 06) and builder pin (procedure 04).
- Code and config changes (procedures 01-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import line (`AgentConfig, ToolConfig`) + `TestMaskArgsDefaultConfig` (2 tests) | Completed | 20261025-091340 | 20261025-091340 | Appended after `TestMaskArgs`, before `TestBuildPreview`; procedure code used verbatim; no existing tests/fixtures changed |
| 2 | RED -> GREEN runs (Phase 1 -> Phase 2) | Completed | 20261025-091340 | 20261025-091340 | RED (Phase 1, before procedures 01-02): both tests fail against `["file_content"]` (`masked_fields == ['file_content']`; `content`/nested `old_text`/`new_text` pass unmasked); GREEN after procedures 01-02 — target-file gate 179 passed, `tests/agent` 3694 passed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | N/A |

**Reconcile note (2026-10-25):** the source fixes for this procedure landed on `origin/master` from a separate session (fix commit `0d3ead56e`, archive commit `e6c0d6eef`). A second session independently re-executed and fully validated the same procedure on the pre-reset tree; `origin/master` was then adopted as canonical and the source state re-confirmed there with targeted tests.

## Traceability

- Plan: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- Plan section: Implementation Target Files — row 5 of 7
  (`tests/agent/test_tool_result_formatter.py`); Tests section; Implementation steps Phase 1
- Requirements: REQ-005
- Acceptance criteria: AC-1, AC-3
- Procedure file:
  `implementations/20261025-004008_05_tests_agent_test_tool_result_formatter.py.md`
- Validation commands: `uv run pytest tests/agent/test_tool_result_formatter.py -q`;
  `uv run pytest tests/agent -q`
