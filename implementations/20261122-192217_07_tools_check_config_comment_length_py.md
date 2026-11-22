## Goal

Add the long-TOML-comment lint for `config/` (REQ-005 - the reduction's comment hygiene gate); no existing tool polices TOML comments, so it is a new tool, not an extension (resolved UNK-02).

## Scope
**Release unit**: N/A: not part of a release unit

One file is modified: the new lint tool. Its unit tests are the companion. Registration in `tools/TOOL_DESCRIPTIONS.md` and `rules/tool-gates.md` and CI wiring are sibling procedures seq 09, 10, 11.

## Assumptions
- The tool is tuned to zero findings on the current reduced `config/` files before it gates CI (Risk mitigation); an allowlist follows the `tools/compat_exceptions.toml` pattern for intentional long comments such as the `plan_blocked_tools` denylist comment.
- Registration rows and the CI step are separate frozen rows; this document does not write them.

## Design decisions
- Follows the existing `tools/` checker shape (design D2): findings as warnings (exit 0) or errors by a single threshold constant.
- Read-only over `config/`; no write, no network, no production access.

## Alternatives considered
Extending an existing checker was rejected (nothing exists to police `config/` comments — verified against the tool inventory).

## Compatibility considerations
CI gate behavior begins only when sibling procedure seq 10 wires the CI step; standalone execution stays safe before that.

## Security considerations
N/A: static text scan.

## Rollback considerations
N/A: revert the commit (remove the tool and its registration rows together per the same-change rule).

## Implementation
### Target file
`tools/check_config_comment_length.py` (new)
### Procedure
1. Scan `config/` files for comment lines longer than the threshold constant; emit findings with a finding code and documented allowlist behavior.
2. Exit 0 on warnings, non-zero on error-level findings, following the existing checker exit-code shape.
### Method
Single threshold constant; allowlist loaded in the `tools/compat_exceptions.toml` pattern, tuned to zero findings on live `config/`.
### Details
- Mirrors the existing `tools/` checker structure (e.g., `check_suppression_justification.py` comment handling) for consistency of output shape.

### Companion test files
- `tests/tools/test_check_config_comment_length.py` (new)
  - Procedure: Unit tests for finding codes, exit codes, and allowlist behavior (REQ-005).
  - Validation: `uv run pytest tests/tools/test_check_config_comment_length.py`

## Validation plan
- `routing.md` Tools sequence: `ruff format` + `ruff check --fix`, `uv run mypy` (file path passed explicitly), `uv run bandit`, then a manual smoke run against live `config/` — expected: zero findings.
- Register in `tools/TOOL_DESCRIPTIONS.md` in the same change; run `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
The tool reports zero findings on the current reduced files, its tests pass, and its `TOOL_DESCRIPTIONS.md` row matches it (no drift).

## Out of Scope
CI wiring (sibling procedure seq 10), the gate row (seq 11), the `TOOL_DESCRIPTIONS.md` row (seq 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the lint tool per Procedure/Method/Details | Pending | — | — | |
| 2 | Add companion unit tests per Validation plan | Pending | — | — | Companion: `tests/tools/test_check_config_comment_length.py` |
| 3 | Run the `routing.md` Tools validation sequence incl. live-config smoke run | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (long-TOML-comment lint for `config/`)
- **Source issue**: `issues/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192217
- **Related target files**: `tools/check_config_comment_length.py`, `tests/tools/test_check_config_comment_length.py`
