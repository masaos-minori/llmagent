# Extend identifier matching to snake_case names and config keys in docs verification

## Priority
Low

## Summary
Decide whether to extend identifier verification so that snake_case-only references and config key names in `docs/` are checked, not only CamelCase names and `name()` forms.

## Background
`memo4.md` ("Remaining work", item 6) records that the identifier matching used to verify the docs cleanup covers CamelCase names and `name()` forms only; snake_case-only references and config key names are not matched exhaustively. `tools/check_docs_consistency.py` already provides `portdrift`, `tooldrift`, `scripts/`-path existence, and backtick-quoted function-reference existence (see `rules/toolchain.md`). Whether those cover snake_case-only and config key references is unknown and must be confirmed. The cleanup-time matching itself appears ad hoc (assumption from the memo).

## Problem
A doc that names a snake_case function, variable, or a config key that no longer exists in `scripts/` or `config/` can pass the verification used for the docs cleanup.

## Reason for Change
Docs compression removes inventories and keeps references to representative symbols and keys. If those references are not checked, they can go stale unnoticed.

## Implementation Intent
First measure, then extend. Determine what `check_docs_consistency.py` already catches for snake_case-only and config-key references on the live `docs/`. Close only the remaining gap, preferably by extending that existing tool rather than adding a new script. Config key checks should use the canonical config model or `config/*.toml` as source, not a hardcoded list.

## Target Files or Areas
- `tools/check_docs_consistency.py`, `tools/_docs_consistency_lib.py`
- `tests/tools/` (matching tests, if present)
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Run the existing checks on live `docs/` and record which snake_case-only and config-key references are and are not verified.
- Define the minimal reference forms to check (for example backtick-quoted snake_case names and `[section].key` forms) and their canonical source.
- Extend the existing tool for the uncovered forms, or record the remaining limit as accepted.
- Run the new check at Warning level first and triage findings on the live corpus.

## Constraints
- Report-only at first; no blocking gate on the existing corpus.
- Avoid false positives on prose words in backticks; define an explicit allowlist mechanism if needed (`# ...-ok` style, as other tools do).
- Tool changes follow `routing.md` "Adding a new tool" validation (ruff, mypy with explicit path, bandit, smoke run, description sync).

## Acceptance Criteria
- The covered reference forms are documented, and the uncovered ones are either checked or listed as an accepted limit.
- On live `docs/`, the check runs and its findings are triaged (fixed in docs, allowlisted, or filed).
- Existing checks and tests still pass.

## Testing Expectations
- Unit tests with fixtures for a valid and a stale snake_case reference and config key.
- `uv run python tools/check_docs_consistency.py --domain <each domain>` on live docs.
- `uv run ruff`, `uv run mypy tools/<file>.py`, `uv run bandit tools/<file>.py`.
- `uv run python tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Possibly: `tools/TOOL_DESCRIPTIONS.md` and the `rules/toolchain.md` description of what `check_docs_consistency.py` verifies, if its scope changes.

## Out of Scope
- Fixing every stale reference found (triage and file follow-ups instead).
- Enumeration generalization detection (separate issue).
- Domains that do not exist for the tool (separate item in `memo4.md` "未実行の検査").

## Dependencies
N/A: none (sibling-issue check: no open issue overlaps). Related to the enumeration-generalization issue in the same batch; both may share code.

## Unresolved Questions
- Which snake_case-only and config-key references does `check_docs_consistency.py` already verify?
- Is the gap worth extending the tool, or is it an accepted limit?

## AI Implementation Instruction
Measure existing coverage before changing code. Extend the existing tool; do not add a parallel script. Keep new findings at Warning level and do not edit docs content in the same change.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-100351
- **Related target files**: `tools/check_docs_consistency.py`, `tools/_docs_consistency_lib.py`, `tools/TOOL_DESCRIPTIONS.md`
