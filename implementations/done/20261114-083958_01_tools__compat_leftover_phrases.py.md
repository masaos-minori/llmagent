## Goal

Create `tools/_compat_leftover_phrases.py (new)` holding the eleven path-scoped leftover-phrase patterns and `check_leftover_phrases (new)`, including the adjacent-line join for the multi-line phrase (REQ-001, REQ-002 / AC-1, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The maintainer can narrow or drop one pattern at the execution step without changing the module structure (Plan UNK-01).
- Pattern text uses character classes (for example `Extracted[ ]from`) so neither this helper nor the checker matches its own source; the fallback for an unavoidable literal is the existing `[checker_self_reference]` table in `tools/compat_exceptions.toml`, reported rather than widened.
- The helper imports the standard library only and stays below the 24576-byte tools module-size default.

## Design decisions
- Helper shape fixed by the Plan Design: `LEFTOVER_PHRASES (new)`: `dict[str, tuple[re.Pattern[str], tuple[str, ...], bool]]` mapping a pattern name to a compiled regex, path prefixes relative to the repository root, and a multi-line flag.
- `check_leftover_phrases (new)` takes `content`, `filepath`, and the allowlist and returns issue strings in the same format as `check_compat_patterns` in `tools/check_compat_shims.py`; it skips allowlisted files and files outside every pattern's prefixes, and for a multi-line pattern tests each stripped line joined with its successor (REQ-002).
- Severity is blocking (exit non-zero), matching every `COMPAT_PATTERNS` entry and the Issue's acceptance criteria; the documentation side of the same phrases stays with the adrrev018 rules in `config/doc_quality_rules.json`.

## Alternatives considered
- Putting the table in `tools/check_compat_shims.py`: rejected; the file already sits at its 36243-byte size baseline.
- Unscoped phrases: rejected; they hit `tests/` and `tools/` and would force exemptions the Issue forbids.
- Bare "bypass", "additive", and "replaces the": rejected; hundreds of ordinary uses.

## Implementation
### Target file
`tools/_compat_leftover_phrases.py` (new)
### Procedure
Create the module with the pattern table and the check function exactly as described in Details, then run the static gates for the new file.
### Method
Standard library only (`re`, `pathlib`); table style follows the existing self-safe tables in `tools/check_compat_shims.py` (character classes such as `[ ]` instead of a plain space).
### Details
Eleven entries in `LEFTOVER_PHRASES (new)` (name -- regex in self-safe form -- path prefixes):
- `Extracted from` -- `Extracted[ ]from` -- `scripts/`.
- `Refactored:` -- literal -- `scripts/`.
- `Precedent:` -- literal -- `scripts/`.
- `signature stability` -- literal -- `scripts/`.
- `re-exported for` -- literal -- `scripts/`.
- `predates` -- literal -- `scripts/` (the one live `docs/` match is troubleshooting prose, out of this scope).
- `user-approved` -- literal -- `scripts/` and `docs/`.
- `pre-migration gate|database` -- the two exact pairs `pre-migration gate` and `pre-migration database` -- `scripts/`.
- `additive (wire) field` -- `additive (wire )?field` wording that matches additive wire-field claims only -- `scripts/`.
- `bypass(es) build_db_config` -- wording that matches the `build_db_config` bypass claim specifically -- `scripts/rag/` only, so the documented current behavior of `SQLiteHelper` in `scripts/db/helper.py` is not flagged.
- `mirror... exactly` -- a gap-tolerant mirror-claim regex with the multi-line flag set: tested by joining each stripped line with its successor (REQ-002).
The module docstring states the Plan id and that entries are self-safe by construction.

## Compatibility considerations
- New file under `tools/`; nothing is deployed. The check only becomes active once the checker procedure wires it in and the hook and CI rows include the file.

## Security considerations
- N/A: a static regex table; `bandit` runs on the file.

## Rollback considerations
- Delete the file and revert the checker import and call; no runtime or configuration state is involved.

## Validation plan
- `uv run pytest tests/tools/test_check_compat_shims.py` passes once the test row's fixtures are added.
- `uv run ruff format tools/_compat_leftover_phrases.py`, `uv run ruff check tools/_compat_leftover_phrases.py`, `uv run mypy tools/_compat_leftover_phrases.py`, and `uv run bandit tools/_compat_leftover_phrases.py` are clean.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` reports the helper below 24576 bytes.

## Completion criteria
- The module exists with the eleven scoped entries and passes the gates; the checker call is wired by its own procedure row.

## Out of Scope
- Wiring `check_all`, the test fixtures, the tool descriptions, and the path filters are their own procedure rows. Phase 4 of the Plan (live-repository smoke run) is executed only after the sweep Plan's procedures have run; any pattern with a residual match is removed from this change and reported, never exempted (REQ-007, UNK-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-031704 | 20261115-031704 | STEP 1: helper created; ruff/mypy/bandit/size gate clean; smoke-verified. Full-suite+coverage deferred to single-directory batch end (procedure 03). |
| 2 | Add or update tests per Validation plan | N/A | — | — | Tests consolidated in the single-directory batch (procedure 03) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115 | 20261115 | ruff format/check, mypy, bandit, and the tools size gate clean; smoke-verified; full-suite + coverage ran once at the batch end (procedure 03) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation handled by procedure 04 |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20261110-171157_rmcompat008_compat-checker-patterns.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122408_rmcompat008_compat-checker-patterns.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-083958
- **Related target files**: `tools/_compat_leftover_phrases.py`