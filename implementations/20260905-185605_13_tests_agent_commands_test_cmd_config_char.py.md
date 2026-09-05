## Goal
Remove the `"Semantic cache:"` section's output-snippet assertions from
`tests/agent/commands/test_cmd_config_char.py`, since
`_print_semantic_cache_settings()` (procedure document `09`) no longer exists
(`REQ-007`, `REQ-009`).

## Scope
- **In-Scope**: remove three entries from `test_output_lines_match_snapshot()`'s
  `expected_snippets` list — `"Semantic cache:"` (the section header),
  `"  use_semantic_cache  : False"` (line 145), and `"  sem_cache_threshold : 0.92"`
  (the entry immediately following it).
- **Out-of-Scope**: every other snippet in `expected_snippets` (`"Settings:"`, `"SSE
  stream settings:"`, `"Execution settings:"`, `"MCP / security settings:"`, `"Approval
  settings:"`, etc.) — confirmed unrelated by reading the full list; every other test
  method in this file.

## Assumptions
- `test_output_lines_match_snapshot()` asserts each snippet is a substring of the full
  captured output (`assert snippet in out`-style, or equivalent) rather than an exact
  full-output match — removing these three lines from the expected list does not
  require renumbering or reordering the remaining snippets, only deleting the three
  entries.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- **Correction to the Plan's stated evidence**: the Plan's row for this file states
  "Remove the `\"  use_semantic_cache  : False\"` output assertion" (singular, one
  line, `rg -n` match at line 145) — Step 3a Adversarial Verification found the
  section header `"Semantic cache:"` and a second value line
  `"  sem_cache_threshold : 0.92"` immediately adjacent to it in the same
  `expected_snippets` list, both of which the Plan's `rg -n "semantic_cache"` search
  did not match (`"Semantic cache:"` is capitalized differently and `sem_cache_threshold`
  does not contain the literal substring `semantic_cache`). This is recorded here as
  the corrected, actual scope for this row — all three lines must be removed together,
  since `_print_semantic_cache_settings()` (procedure document `09`) no longer prints
  any of them once removed.

## Alternatives considered
N/A: straightforward removal of three now-nonexistent-output assertions.

## Implementation
### Target file
`tests/agent/commands/test_cmd_config_char.py`

### Procedure
1. In `test_output_lines_match_snapshot()`'s `expected_snippets` list, remove
   `"Semantic cache:"`.
2. Remove `"  use_semantic_cache  : False"` (line 145).
3. Remove `"  sem_cache_threshold : 0.92"` (the entry immediately following line 145).

### Method
Direct removal via `Edit` on three list-literal entries.

### Details
- Confirm no `"sem_cache_max_size"` entry exists in this list (confirmed by reading —
  only two of `_print_semantic_cache_settings()`'s three printed values were asserted
  here; the third was apparently never covered by this snapshot test) — no fourth
  entry needs removing.
- Confirm after editing: `rg -n "semantic_cache|sem_cache"
  tests/agent/commands/test_cmd_config_char.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `09` (`cmd_config_display.py`'s `_print_semantic_cache_settings()`
  removal) to avoid this test asserting on output that document no longer produces.

## Validation plan
- `uv run pytest tests/agent/commands/test_cmd_config_char.py -v` — passes;
  `test_output_lines_match_snapshot()` no longer expects the removed section.
- `rg -n "semantic_cache|sem_cache" tests/agent/commands/test_cmd_config_char.py` —
  zero matches.

## Completion criteria
- No reference to the removed "Semantic cache:" output section remains in this file
  (Plan `AC-6`, `AC-8`).

## Out of scope
- `scripts/agent/commands/cmd_config_display.py`'s
  `_print_semantic_cache_settings()` itself (procedure document `09`).
- Every other snippet assertion in `expected_snippets`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: assertion cleanup only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007` (assert the removed output no longer appears); `REQ-009` (remove tests referencing the removed API)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/agent/commands/test_cmd_config_char.py
