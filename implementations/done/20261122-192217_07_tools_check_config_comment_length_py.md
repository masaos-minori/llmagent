## Goal

Add the long-TOML-comment lint for `config/` (REQ-005 - the reduction's comment hygiene gate); no existing tool polices TOML comments, so it is a new tool, not an extension (resolved UNK-02).

## Scope
**Release unit**: N/A: not part of a release unit

One file is modified: the new lint tool. Its unit tests are the companion. Registration in `tools/TOOL_DESCRIPTIONS.md` and `rules/tool-gates.md` and CI wiring are sibling procedures seq 09, 10, 11.

## Assumptions
- Adversarial finding (2026-11-22): the Plan's "zero findings on live `config/`" premise does not hold. `config/` already contains 8 comment blocks over 5 consecutive comment lines: `adr_authority.toml` 6, `chunk_splitter.toml` 10, `cicd_mcp_server.toml` 8, `eventbus.toml` 9, `github_mcp_server.toml` 7, `mcp_dedup.toml` 12, `shell_mcp_server.toml` 15, `tool_catalog.toml` 23. Owner decision (2026-11-22): threshold = 5 consecutive comment lines, and the 8 existing blocks are recorded as allowlist exceptions following the `tools/compat_exceptions.toml` pattern; the CI step (seq 10) is wired only after the allowlist makes the live run clean. No `config/` file is reformatted (they are not plan targets).
- Registration rows and the CI step are separate frozen rows; this document does not write them. The gate mapping entry for the tool-gates row is sibling procedure seq 14.

## Design decisions
- Follows the existing `tools/` checker shape (design D2): findings as warnings (exit 0) or errors by a single threshold constant. The threshold is 5 consecutive comment lines, which is the unit `rules/tool-gates.md` and the Issue's "long comment" wording imply; a run that separates blocks by non-comment lines is what the existing repo convention reads as a comment block.
- **Deviation from the plan's wording**: the exception list is in-module (`EXCEPTIONS`, `(file, start_line) -> reason`) rather than a separate allowlist file, because `tools/compat_exceptions.toml` is read by its own tool and a new file would be an additional target file outside the frozen row. It follows the same pattern: one entry per existing block, each with a reason, and a recorded entry whose block no longer exists is itself a finding (`CFG-COMMENT-003`) so the exception list cannot drift from the live config.
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
- `routing.md` Tools sequence: `ruff format` + `ruff check --fix`, `uv run mypy` (file path passed explicitly), `uv run bandit`, then a manual smoke run against live `config/` — expected: zero findings, which holds only through the 8 recorded allowlist exceptions.
- Register in `tools/TOOL_DESCRIPTIONS.md` in the same change; run `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
The tool reports zero findings on the current reduced files, its tests pass, and its `TOOL_DESCRIPTIONS.md` row matches it (no drift).

## Out of Scope
CI wiring (sibling procedure seq 10), the gate row (seq 11), the `TOOL_DESCRIPTIONS.md` row (seq 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the lint tool per Procedure/Method/Details | Completed | 2026-11-22 | 2026-11-22 | Exception list is in-module; the live run reports 8 warnings and exits 0 |
| 2 | Add companion unit tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | 6 tests in `tests/tools/test_check_config_comment_length.py`, incl. the live-config `repo_scan` test required by `rules/test_policy.md` for a `config/`-reading tool |
| 3 | Run the `routing.md` Tools validation sequence incl. live-config smoke run | Completed | 2026-11-22 | 2026-11-23 | mypy/ruff/bandit clean; live run clean; file coverage 90.4% |

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
