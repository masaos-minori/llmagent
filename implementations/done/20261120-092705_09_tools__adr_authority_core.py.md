## Goal

- Close the three verified core-validator gaps in the shared ADR authority core: duplicate-edge detection (`EDGE_DUPLICATE` (new)), ADR status/ownership validation (`ADR_STATUS_INVALID` (new)), and a loopback assertion for the `eventbus.host` config-key pattern.

## Scope
**Release unit**: N/A: not part of a release unit

- REQ-001 (duplicate `(from, to)` pairs fail as `EDGE_DUPLICATE` (new)), REQ-004 (parse the allowed Status set and validate model-referenced ADRs), REQ-005 (`Withdrawn`/`Proposed` misuse findings), REQ-006 (`eventbus.host` loopback assertion with fixture path override).

## Assumptions
- Verified current source: `_check_config_key` (line 496) fail-closes on any pattern other than `LOOPBACK_PATTERN` (line 52); `by_pair` (line 407) silently overwrites duplicate `(from, to)` pairs; `validate_model` (line 651) never inspects `## Status`; `adr_files_by_id` (line 244) maps ADR ids to files; `check_assumptions`/`validate_model` already take a `config_path` override (lines 457, 655) that the new EventBus path override mirrors.
- The three new finding codes must land in the same commit as `config/adr_authority.toml` ARCH-002's `eventbus.host` key (its own procedure document), or the core fail-closes on the unknown pattern (Plan Risk mitigation).
- Status-set single source (corrected by 20261120 adversarial re-check): ADR-016 has no canonical allowed-status sentence — its only "Status" occurrence is the `## Status` heading (line 25, value `Accepted`). The allowed set must be parsed from `governance_01` "ADR Status Definitions" (`docs/00_governance/governance_01_documentation-policy.md` line 266, bullets `Proposed` / `Accepted` / `Withdrawn`); `tools/check_adr_structure.py` already pins a hard-coded `_ALLOWED_STATUSES` tuple to that section via a test, and the core's parse must stay equal to the same section. Live-status scan: every `adr_02_*.md` is `Accepted` except ADR-010 (`Withdrawn`, referenced by no model row), so the new validator leaves all live checkers exit 0.
- `tools/check_adr_authority.py` is a frozen-table Reference File, not a target: its wiring exercises the core's `validate_model`, so no edit is expected; if its imports or finding-code docstring turn out to require an edit, that is an additional-target-file discovery to report, not a change to make here.

## Design decisions
- Duplicate detection runs at model load, after `edges` validation, grouping `(from, to)` pairs and naming every duplicate location in the finding message; `by_pair` consumers stay unchanged because a duplicate can no longer pass silently (Plan Design).
- Status validation is a dedicated step inside `validate_model` using the same first-non-empty-line convention as `check_adr_structure.py` check (e), so the two parsers agree by construction (Plan Risk mitigation).
- The EventBus assertion reads `config/eventbus.toml` through a fixture-overridable path mirroring the existing `config_path` override: present `host` must be loopback, absent key asserts the documented `127.0.0.1` default of `scripts/eventbus/config.py`.

## Alternatives considered
- Rejecting duplicates at TOML parse time — rejected: the model load already validates edge shape and location tracking exists there; the finding must name both locations.
- Hard-coding the allowed status set in the core — rejected by REQ-004: the set is parsed from the governance documents so a governance change propagates.

## Implementation
### Target file
`tools/_adr_authority_core.py`
### Procedure
- Add duplicate detection in model load: after `edges` validation, group `(from, to)` pairs; report each group of size > 1 as `EDGE_DUPLICATE` (new) with the location of every duplicate row (REQ-001).
- Add a status-validation step to `validate_model`: collect every ADR id referenced by authorities, edges, and assumptions; resolve each via `adr_files_by_id`; parse the first non-empty line of its `## Status`; report `ADR_STATUS_INVALID` (new) for (a) a value outside the parsed allowed set (REQ-004), (b) a `Withdrawn` ADR owning a decision target or holding a non-`Reference` edge, (c) a `Proposed` ADR listed as a target's primary (REQ-005).
- Add the `EVENTBUS_HOST_PATTERN` (new) constant = `"eventbus.host"` and a second branch in `_check_config_key` for it, reading `config/eventbus.toml` (new path parameter with a fixture override mirroring `config_path`): assert `host` is loopback when present, assert the `127.0.0.1` default when absent, and keep the existing `current_value` cross-check semantics; unknown `config_keys` patterns keep fail-closing (REQ-006).
### Method
- Extend the existing validator functions in place; `Finding` shape unchanged (recorded in the Plan: `tests/tools/test_tool_report_output.py` is unaffected).
### Details
- Duplicate grouping keyed on `(edge.from_adr, edge.to_adr)` with `location` values taken from the existing model-load location tracking.
- Allowed-set parsing target: the `## ADR Status Definitions` bullets in `docs/00_governance/governance_01_documentation-policy.md` (ADR-016 has no such sentence — verified); a parse failure reports `ADR_STATUS_INVALID` (new) fail-closed rather than skipping the check.
- Loopback test reuses the existing loopback host logic already applied to `mcp_servers.*.url` values.

### Companion test files
- `tests/tools/test_adr_authority.py`
  - Procedure: add fixtures for a duplicate `(from, to)` edge pair, an unknown Status value, a `Withdrawn` ADR owning a target, a `Proposed` ADR as primary, and a non-loopback `eventbus.host` via the new path override (plus the absent-key pass) (REQ-027).
  - Validation: `uv run pytest tests/tools/test_adr_authority.py` — each fixture produces the named finding code; the live model stays clean.

## Compatibility considerations
- Blast radius (Plan Design consumer scan): the core is imported by `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/generate_adr_authority.py` and three test modules; the live model has no duplicates and no invalid statuses, so all live checkers must stay exit 0 (AC-1).
- File growth past 25689 bytes requires the module-size baseline raise — handled by the baseline row's own procedure document, in the same commit as the growth.

## Security considerations
- The `eventbus.host` assertion enforces the loopback-only exposure assumption (ARCH-002) for the EventBus, mirroring `scripts/eventbus/config.py` `_is_public_host` semantics; a non-loopback host fails the CI validator.

## Rollback considerations
- Revert the single Phase 1 commit (core + ARCH-002 config + tests + baseline together); no persisted state depends on the new codes.

## Validation plan
- `uv run pytest tests/tools/test_adr_authority.py` — new fixtures fail as designed (AC-1).
- `uv run python tools/check_adr_authority.py` — exit 0 on the live model.
- `rules/toolchain.md` sequence (ruff, mypy, bandit, full `uv run pytest`).

## Completion criteria
- Each of the four fixture classes produces its finding code and the live model passes all consumers unchanged (AC-1); the file stays within the raised module-size baseline.

## Out of Scope
- `tools/check_adr_authority.py` docstring wiring (frozen-table reference row — report instead of editing), the ARCH-002 config wording (config row), the baseline raise (baseline row), and generator behavior (generator row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `EDGE_DUPLICATE` (new) detection at model load (REQ-001) | Completed | 20261120 | 20261120 | — |
| 2 | Implement status-set parsing and status/ownership validation (REQ-004, REQ-005) | Completed | 20261120 | 20261120 | same Phase 1 commit as steps 1 and 3 |
| 3 | Implement the `eventbus.host` loopback validator with path override (REQ-006) | Completed | 20261120 | 20261120 | same Phase 1 commit as the ARCH-002 config row |
| 4 | Add the companion fixtures per Validation plan (REQ-027) | Completed | 20261120 | 20261120 | — |
| 5 | Run the validation sequence (`rules/toolchain.md`) plus `check_adr_authority.py` | Completed | 20261120 | 20261120 | — |

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
- **Requirement ID**: REQ-001 (duplicate-edge detection), REQ-004 (status-set validation), REQ-005 (status/ownership misuse), REQ-006 (`eventbus.host` loopback assertion)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `tools/_adr_authority_core.py`, `tests/tools/test_adr_authority.py`
