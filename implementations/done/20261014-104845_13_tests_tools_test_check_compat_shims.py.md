## Goal

Add a test case for the `/mdq` compat pattern (REQ-003: guard reintroduction).

## Scope

- Add one test method. One method in `TestPatternDetection` (lines 40-73).

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- The existing phrase test passes on any pattern, so add a method that matches `COMPAT_PATTERNS["/mdq command"]` directly: positives `/mdq status`, `` `/mdq` ``; negatives `mdq.sqlite`, `/opt/llm/db/mdq.sqlite`, `<log_dir>/mdq-mcp.log`, `scripts/mcp_servers/mdq/server.py`.
- Name it `test_mdq_command_pattern_matches_command_form_only` (new).

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/tools/test_check_compat_shims.py`

### Procedure

Add the method to `TestPatternDetection`.

### Method

Use `re.search(COMPAT_PATTERNS["/mdq command"], text)` per sample; follow the file's style and run `ruff format`.

### Details

The file is allowlisted, so its own `/mdq` samples do not fail the checker.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/tools/test_check_compat_shims.py -q` passes and fails if the entry is removed.

## Completion criteria

- The method exists and covers positives and negatives.

## Out of scope

- Other pattern tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test | Completed | 20261014-110318 | 20261014-110318 |  |
| 2 | Run the tests that cover this file | Completed | 20261014-110318 | 20261014-110318 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-110318 | 20261014-110318 |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: tests/tools/test_check_compat_shims.py