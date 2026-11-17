# Make one source of truth for MCP retry classes

## Priority
Medium

## Summary
MCP retry classification is kept in two places by hand, and one key matches no tool. Define one source and derive or check the other.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M06`; merged from ADRCHK-M20 (review finding N39)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
`config/mcp_dedup.toml` has a `web_search` key (`Explicit in code`, confirmed by `rg`), while the tool constants name the tool `search_web` (`Explicit in code`). The remaining claims come from the review.

## Reason for Change
- There are two sources: `RETRYABLE_TOOLS` in `scripts/shared/tool_constants.py` calls itself the single source of truth, but it must be synchronized by hand with `[retry_class]` in `config/mcp_dedup.toml`.
- One key matches no tool, so the entry is silently unused although the file header says keys are live tool names.
- Risky tools such as `git_push`, `github_merge_pull_request`, and `delete_directory` are retryable, so their safety depends entirely on dedup, and that risk is not recorded.
- Comments are wrong: a port comment names the wrong server and a comment cites ADR-008, which is not about retry.

## Implementation Intent
- One source defines the retry classes, and the other is derived from it or checked against it at load.
- Unknown keys are rejected.
- The retry risk of external side effects is recorded.

## Target Files or Areas
- `scripts/shared/tool_constants.py`
- `config/mcp_dedup.toml`
- `scripts/shared/mcp_dedup.py`
- `tests/shared/`

## Required Changes
- Choose the source, and derive the other side, or add a load-time equality check.
- Rename `web_search` to `search_web`, and reject keys that match no known tool.
- Fix the port comment and the ADR citation.
- Report the retryable tools with external side effects for a maintainer decision.

## Constraints
- Do not change any tool's retry class without approval.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- A test fails when a `retry_class` key is not a known tool name.
- A test fails when the two sources disagree, or only one source remains.

## Testing Expectations
Unit tests under `tests/shared/`; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Not required unless an MCP dedup guide cites the two sources; check with `rg` before finishing.

## Out of Scope
- Changing retry classes.
- Dedup storage changes.

## Dependencies
- N/A: none

## Unresolved Questions
- `scripts/shared/mcp_dedup.py` was not reviewed; the loader behavior is `Needs confirmation`.

## AI Implementation Instruction
- Do not change any tool's retry class without approval.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123018
- **Related target files**: `scripts/shared/tool_constants.py`; `config/mcp_dedup.toml`; `scripts/shared/mcp_dedup.py`; `tests/shared/`
