# Fix ROOT_DIR depth, stale path references, and DEFAULT_ALLOWLIST in tools/check_no_compat.py

## Goal
`tools/check_no_compat.py`'s default (no-args) scan resolves `ROOT_DIR` to the actual
repository root and scans real files, and every `DEFAULT_ALLOWLIST` entry references a
path that currently exists.

## Scope
- In scope: `ROOT_DIR` computation (line 21), module docstring header + `Usage:` line,
  all 29 `DEFAULT_ALLOWLIST` entries (path corrections, dedup, removal of entries for
  deleted files), triage of genuinely new findings surfaced after the fix.
- Out of scope: `COMPAT_PATTERNS` detection logic/regexes; `main()`'s crash on directory
  positional arguments (tracked separately in `issues/20260807-101021_risks.md`); any
  change to `tools/check_suppression_justification.py`.

## Assumptions
- `tools/check_suppression_justification.py`'s `ROOT_DIR = Path(__file__).resolve().parent.parent`
  is the correct depth pattern to copy, since both files live directly under `tools/`.
- No other module imports `check_no_compat.ROOT_DIR` or `check_no_compat.DEFAULT_ALLOWLIST`
  as a public symbol — this is a standalone pre-commit-hook script, not a library import
  target, so the blast radius of changing these values is confined to this file and its
  test.

## Design decisions
- Copy the `ROOT_DIR` pattern verbatim from `tools/check_suppression_justification.py`
  rather than introducing a new resolution strategy (e.g. searching upward for a marker
  file) — the sibling module already establishes the project convention for a `tools/`-level
  script, and matching it keeps the fix minimal.
- Fix allowlist paths in-place (same dict, corrected string values) rather than
  restructuring `DEFAULT_ALLOWLIST`'s shape — this is a data-correction task, not a design
  change.
- Sequence the fix as ROOT_DIR + docstring first, then allowlist audit, then triage —
  each step is independently verifiable by running the tool, matching the plan's
  phase-by-phase validation approach.

## Alternatives considered
- Deriving `ROOT_DIR` by walking upward until a marker file (e.g. `pyproject.toml`) is
  found, instead of a fixed `.parent` chain: rejected — over-engineered for a script whose
  location is fixed and already has a working sibling-module precedent at this exact
  directory depth.

## Implementation

### Target file
`tools/check_no_compat.py`

### Procedure
1. Change line 21 from `ROOT_DIR = Path(__file__).resolve().parent.parent.parent` to
   `ROOT_DIR = Path(__file__).resolve().parent.parent`.
2. Fix the module docstring: line 1's `"""scripts/checks/check_no_compat.py` becomes
   `"""tools/check_no_compat.py`; the `Usage: python -m scripts.checks.check_no_compat`
   line becomes `Usage: python -m tools.check_no_compat`.
3. Run `uv run python -m tools.check_no_compat` and confirm the reported scanned-file count
   is non-zero (expect real findings at this point, including allowlist-path false
   positives from step 4-5 not yet applied — that is expected, not a regression).
4. For each of the 29 `DEFAULT_ALLOWLIST` entries, verify the referenced path exists under
   the corrected `ROOT_DIR`. At minimum, correct these 10 confirmed-stale entries:
   - `tests/test_rag_get_cfg.py` -> `tests/agent/test_rag_get_cfg.py`
   - `tests/test_route_resolver.py` -> `tests/shared/test_route_resolver.py`
   - `tests/test_mcp_rag_pipeline.py` -> `tests/mcp_servers/rag_pipeline/test_mcp_rag_pipeline.py`
   - `tests/test_rag_pipeline_mcp_service.py` -> `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`
   - `tests/test_rag_tools_consistency.py` -> `tests/shared/test_rag_tools_consistency.py`
   - `tests/test_cmd_registry_note_removal.py` -> `tests/agent/commands/test_cmd_registry_note_removal.py`
   - `tests/test_removed_commands.py` -> `tests/agent/commands/test_removed_commands.py`
   - `tests/test_create_schema.py` -> `tests/db/test_create_schema.py`
   - `tests/test_check_no_compat.py` -> `tests/tools/test_check_no_compat.py`
   - `tests/test_mcp_tool_schema_exports.py` -> `tests/mcp_servers/test_mcp_tool_schema_exports.py`
5. For the `scripts/checks/check_no_compat.py` and `scripts/checks/check_docs_consistency.py`
   entries: run `git log --diff-filter=D -- scripts/checks/check_no_compat.py` (and the
   `check_docs_consistency.py` equivalent) to determine whether the old file was deleted
   outright (remove the allowlist entry) or its content moved under a new `tools/` name
   (repoint the entry to the new path).
6. Remove the duplicate `test_rag_get_cfg.py` entry (currently listed twice, ~lines 94 and
   122), keeping a single corrected copy.
7. Re-run `uv run python -m tools.check_no_compat` after steps 1-6. For every remaining
   reported match, decide individually: fix the genuine compatibility-leftover in the
   source file it was found in, or add a new `DEFAULT_ALLOWLIST` entry with an inline
   justification comment. Do not bulk-allowlist.
8. If the remaining real-finding count after step 7 is large or ambiguous enough to need a
   product/judgment call, stop implementation and report to the user rather than resolving
   it unilaterally.

### Method
Direct text edits to `tools/check_no_compat.py` (constant value changes and dict entry
corrections) — no new functions, classes, or control flow.

### Details
- `ROOT_DIR` (line 21): single-line change, three-level to two-level `.parent` chain.
- Docstring (lines 1, ~11): two string literal edits, no code-path change.
- `DEFAULT_ALLOWLIST` (lines 87-133): value-only edits to existing dict entries; one entry
  removed (duplicate); zero-to-few entries added only after step 7's individual review.
- No change to `COMPAT_PATTERNS`, `main()`'s argument parsing, or exit-code logic.

## Compatibility considerations
- The `no-compat-stubs` pre-commit hook's invocation (`entry: python -m tools.check_no_compat`,
  `pass_filenames: false`) is unchanged — this fix only changes what the hook's existing
  invocation actually scans.
- No CLI flag or public function signature changes.

## Security considerations
N/A — no security-sensitive logic (secrets, auth, network, deserialization) is touched.

## Rollback considerations
Single-file, additive-to-correct-data change with no schema or state migration. Revert via
`git revert` of the commit; no data cleanup required since `DEFAULT_ALLOWLIST` and
`ROOT_DIR` are pure in-memory constants re-evaluated on every run.

## Validation plan
| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tools/check_no_compat.py` | Manual/integration run | `uv run python -m tools.check_no_compat` | Non-zero scanned-file count; `All checks passed` after triage, or nonzero exit with concrete reviewed findings |
| `tools/check_no_compat.py` | Existing unit tests | `uv run pytest tests/tools/test_check_no_compat.py -v` | All existing `TestPatternDetection` / `TestWorkflowEnforcementPatterns` cases still pass |
| Repo-wide hook | Integration | `uv run pre-commit run no-compat-stubs --all-files` | Passes |
| Changed file | Lint/type | `uv run ruff check tools/`, `uv run mypy tools/` | No new errors |
| Changed file | Security | `uv run bandit tools/check_no_compat.py` | No new high/medium findings |

## Out of scope
- `COMPAT_PATTERNS` regex changes.
- `main()`'s directory-argument crash (`issues/20260807-101021_risks.md`).
- Changes to `tools/check_suppression_justification.py`.
- The regression test for `main()`'s default-scan path — covered by the companion
  implementation procedure for `tests/tools/test_check_no_compat.py`.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-100914_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-102112
- Related target files: tools/check_no_compat.py
