## Goal

Extend the pinned GitHub check inventory in this test with the two checks row 4 adds, and assert the statuses the Plan defines for them (REQ-009: the posture reports what the code enforces). This file is the only place that pins the inventory, so the added checks cannot be validated anywhere else (AC-9).

## Scope
**Release unit**: N/A: not part of a release unit — no Plan `Implementation steps` entry cites this file; Phase 4 adds the checks and this file's assertions in the same phase, so both sides land together.

## Assumptions

- This row has its own document rather than being a companion because the Plan names this file only from its own row, which satisfies the companion condition in `skills/plan-to-implementation-procedure/SKILL.md`.
- The two ids are appended at the end of `GITHUB_SERVER_CHECK_IDS` (lines 27-36), because `test_order_is_fixed` (line 208) asserts the produced order equals the tuple order and row 4 appends its checks at the end of the fixed sequence.
- The inventory here is a mirror of `REQUIRED_CHECK_IDS["github"]` in `scripts/shared/security/posture_contract.py` (lines 50-60); `test_ids_match_the_frozen_contract` (line 198) compares against the contract, so the two ids must be added there too for this file's assertions to hold. That file is not a row of the original frozen table; it was added as a fallout target row on 2026-11-24 with the user's approval, and its procedure is `implementations/20261124-103302_24_scripts_shared_security_posture_contract.py.md`, which also covers its mirror test.

## Design decisions

- Assert the status, not the message text, and keep the file's existing style: build a `GitHubConfig` through the `_safe_cfg()` helper and read statuses from `validate_github_security()`.
- Keep the existing eight ids in their current positions so the pinned tuple stays a record of the earlier decision rather than a rewrite; only the two new ids are appended.

## Alternatives considered

- Assert the two new checks in `tests/mcp_servers/github/test_github_health_posture.py` — rejected: that file asserts a subset (`_GITHUB_CHECK_IDS <= published`, line 89) and does not pin the inventory; the inventory assertion belongs in this file.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_security_validation.py`

### Procedure
1. Append `"server.global_search"` and `"server.max_file_read_size"` to `GITHUB_SERVER_CHECK_IDS` (lines 27-36), in that order.
2. Add cases for `server.global_search`: `OK` when the boundary is enforced at the default `allow_global_search = false`, and `WARNING` when `true` is explicitly opted in — as row 4's check defines; assert the two statuses from the guard's own rule rather than from the config value.
3. Add cases for `server.max_file_read_size`: `OK` for a positive value, `NOT_APPLICABLE` with `REASON_NOT_APPLICABLE` at `0`.
4. Keep `test_ids_match_the_frozen_contract`, `test_order_is_fixed`, and `test_check_set_is_identical_across_configurations` (lines 198, 206, 212) unchanged; the length assertion at line 224 follows the tuple, so it needs no edit.
5. The contract table and its mirror are covered by `implementations/20261124-103302_24_scripts_shared_security_posture_contract.py.md`; this document adds no case there, and the assertions here pass only after that row lands.

### Method
- Use the existing `_safe_cfg()` helper for config construction; no new fixture. Put the warning-status case in `TestWarningPolicySettings` (line 75) and the not_applicable/ok cases in `TestInapplicableChecks` (line 101), following the style of the cases already in those classes.

### Details
- `test_check_set_is_identical_across_configurations` iterates several configurations (lines 212-224); the two new configurations for the new checks must produce the same check set, so the new cases use configs that keep the other eight checks unchanged.
- This is a test-only change; `check_adr_invariant_matrix.py` is not affected (no ADR citation names this file).

## Plan Gap (resolved in this cycle)

- `scripts/shared/security/posture_contract.py` (`REQUIRED_CHECK_IDS`, github row, lines 50-60) and `tests/shared/test_security_posture_contract.py` (`SERVER_CHECK_IDS`, github row, lines 46-55, asserted at lines 343, 351) must both carry the two new ids, otherwise line 198 fails. Neither was a row of the Plan's `Implementation Target Files`, and the Plan's consumer scan stated the inventory is pinned only in this file. Both were added as target rows on 2026-11-24 with the user's approval (Fallout class: files needed to keep an existing inventory and its mirror checker working); the mirror test is the companion of `implementations/20261124-103302_24_scripts_shared_security_posture_contract.py.md` and has no document of its own.

## Compatibility considerations

- The `/health` security block gains two entries; `check_docs_consistency.py --domain mcp` is re-run after the docs mapping rows (row 22) change, which is the Plan's own stated requirement.

## Security considerations

- A published check whose status is not asserted is a claim the documentation makes without evidence; these cases make the two new controls observable through the same path the Agent reads during startup readiness.

## Rollback considerations

- N/A: revert the commit; test-only change.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/mcp_servers/github/test_github_security_validation.py` | Unit (posture inventory and statuses) | `uv run pytest tests/mcp_servers/github/test_github_security_validation.py` | The tuple includes the two new ids in the produced order; `server.global_search` reports the opt-in; `server.max_file_read_size` is `ok` when positive and `not_applicable` at `0` (AC-9) |
| Same file | Mirror contract | `uv run pytest tests/shared/test_security_posture_contract.py` | Green only after the two ids are added to the contract table and its mirror (see Plan Gap) |
| Same file | Quality gate | `uv run ruff check tests/mcp_servers/github/test_github_security_validation.py` | No finding |

## Completion criteria

- The pinned inventory and the produced check set agree on ten ids, and both new checks' statuses are asserted (AC-9).

## Out of Scope

- Defining the two checks (row 4) and the docs settings-to-check mapping rows (row 22).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the tuple and add the two cases per Procedure | Pending | — | — | |
| 2 | Run this file's tests and the mirror contract test | Pending | — | — | The mirror test needs the Plan Gap resolved first |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The two ids must also be added to `scripts/shared/security/posture_contract.py` and its mirror test, which were not Plan target rows | Yes | 2026-11-24 (both files added as fallout target rows with the user's approval) |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-009 (the posture reports the settings it enforces)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `tests/mcp_servers/github/test_github_security_validation.py`
