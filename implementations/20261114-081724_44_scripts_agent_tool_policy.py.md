## Goal

Remove the 15 remaining historical comment and docstring reference(s) in `scripts/agent/tool_policy.py` (REQ-001 / AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Comment-only change: no code, import, or behavior edit; the rewrite keeps the information and changes only tense and identifiers (Plan Assumptions).

## Design decisions
- N/A: comment-only change (Plan Design rewrite rules).

## Alternatives considered
- Keeping the provenance notes: rejected; AC-1 requires the whole tree free of these identifiers.

## Implementation
### Target file
`scripts/agent/tool_policy.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 48: """"REQ-007: read-only-by-construction shape rule for one shell executable."""" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 55: "# REQ-006: an executable absent from this table is never auto-approved, even when a" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 149: """"Raised when a path-argument value is neither `str` nor `list[str]` (REQ-002)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 163: "registered tool's declared resource_scope_keys (REQ-001)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 168: "policy (REQ-003). Order is stable: configured keys first." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 191: """"Yield each inspectable path value under the given keys (REQ-002)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 251: """"REQ-001: tokens whose value must be routed through the path checks." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 277: "# REQ-001: bare tokens and --flag=value values are path candidates" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 302: "REQ-006: rule absence is the denial mechanism (deny-by-default). REQ-007: allowed" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 383: "# REQ-002: fail closed on any shell metacharacter in raw command" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 386: "# REQ-001: parsed identity match replaces startswith below" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 396: "# REQ-003: route positional args through path/argument checks" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 399: "# REQ-008: one normalized executable name gates both the prefix match" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 402: "# REQ-006/REQ-007: safe-shape rule decides auto-approval; deny by default" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 539: "tool's declared scope keys available to the root-jail check (REQ-003)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/agent/tool_policy.py` returns nothing.
- `uv run pytest tests/agent` continues to pass.
- Comment-only guarantee: `git diff -U0` shows no changed line other than comment and docstring lines.

## Completion criteria
- The file-level acceptance search is clean and the phase test directory passes.

## Out of Scope
- The other rows of the Plan table are handled by their own procedures; test files citing these identifiers are out of scope (UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122030_rmcompat007_history-comment-sweep.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-081724
- **Related target files**: `scripts/agent/tool_policy.py`
