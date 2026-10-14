## Goal

Register `/mdq` as a removed command in `COMPAT_PATTERNS` (REQ-003: guard reintroduction).

## Scope

- Add one dictionary entry. One entry in `COMPAT_PATTERNS` (the dict ends at line 84); `_REMOVED_NAME_PATTERNS` is not touched.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Add `"/mdq command": r"(?<![\w/.-])/mdq(?![\w./-])"` next to the other removed-command entries (`/note`, `/db` aliases, lines 41-45).
- Apply last, after procedures 01-11 and 14-19 have removed every `/mdq` string outside the allowlisted files; a trial run before the removal reported 44 findings in 9 files.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tools/check_compat_shims.py`

### Procedure

Insert the entry after the `/db recover alias` entry.

### Method

The lookbehind excludes a preceding word character, slash, dot, or hyphen and the lookahead excludes a following word character, dot, slash, or hyphen, so `mdq.sqlite`, `mdq-mcp`, and `scripts/mcp_servers/mdq/` do not match.

### Details

`test_removed_commands.py`, `test_cmd_registry_note_removal.py`, `tests/tools/test_check_compat_shims.py`, and this file are already on `DEFAULT_ALLOWLIST`.

## Compatibility considerations

Adds a default-on CI check; a leftover `/mdq` in code or docs now fails `tools/check_compat_shims.py`.

## Security considerations

No new input path; the pattern only reads text.

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run python tools/check_compat_shims.py` reports no finding after all other procedures.
- `uv run pytest tests/tools/test_check_compat_shims.py -q` passes.

## Completion criteria

- The entry exists and the default checker run is clean.

## Out of scope

- `_REMOVED_NAME_PATTERNS`, `--check-removed-names`, and the two pre-existing findings.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the pattern entry | Pending | — | — | |
| 2 | Run the tests that cover this file | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: tools/check_compat_shims.py
