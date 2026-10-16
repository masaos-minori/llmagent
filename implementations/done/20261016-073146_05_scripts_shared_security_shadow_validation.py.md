## Goal

Implement the Shadow Validation harness that runs the old Agent-side audit and the new server
self-validation in parallel and compares their outcomes, so the switch to canonical self-validation
is evidence-based (`REQ-016`).

## Scope

- One new module `scripts/shared/security/shadow_validation.py`: the comparison outcome enum, the
  comparison function, and the non-secret diff report.
- The harness is a migration-time tool. Driving it (feeding it real audit output and real
  postures) is done from tests, not from this module.

## Assumptions

- The six comparison outcomes are fixed by the Plan's Design section: `MATCH_PASS` (new), `MATCH_FAIL` (new),
  `AGENT_ONLY_FAIL` (new), `SERVER_ONLY_FAIL` (new), `CHECKSET_MISMATCH` (new), `CONTRACT_ERROR` (new).
- **Needs confirmation**: whether the harness is kept after canonicalization or deleted with the
  old audit. The Plan keeps it as a target row; the retirement decision is recorded in the Plan's
  Open Items, not decided here.

## Design decisions

- The harness receives both result sets as arguments — an old-audit outcome list and a
  `SecurityPosture` — and imports neither `agent.services.security_audit` nor any server module.
  `shared` must remain a leaf (`.importlinter:19-28`), so importing the old audit from this module
  would break `shared-is-leaf`. The wiring that imports both sides lives in a test module.
- Comparison is on check identity and pass/fail, never on messages: `CHECKSET_MISMATCH` (new) is raised
  when the two sides do not agree on the set of check ids in scope, which is the condition the
  Plan says must block the switch.
- The diff report carries check ids, reason codes, and statuses only. Raw config values are never
  part of it (`REQ-016`).

## Alternatives considered

- Implement the harness as a script under `tools/` — rejected: the Plan's frozen table names it as
  a shared module so both the Agent-side tests and the server-side tests can import it, and a
  `tools/` script cannot be imported by `mcp_servers` tests without a path hack.
- Compare message strings — rejected: messages are human-readable and unstable, so message
  comparison produces false `CHECKSET_MISMATCH` (new) results.

## Implementation
### Target file

`scripts/shared/security/shadow_validation.py` (new)

### Procedure

1. Define `ShadowOutcome` (new) with the six Plan values.
2. Define `ShadowComparison` (new): frozen dataclass holding `outcome`, `server_key`,
   `matched_check_ids` (new), `agent_only_check_ids` (new), `server_only_check_ids` (new), `status_conflicts` (new).
3. Define `compare_shadow_results()` (new) taking the old-audit outcome list and a
   `SecurityPosture` and returning `ShadowComparison` (new).
4. Define `format_shadow_report()` (new) returning a single non-secret log line per server.

### Method

- Derive the old-audit side's check ids from a caller-supplied mapping of audit warning text to
  check id, so this module does not need the retired audit's internals.
- Decide the outcome in this order: malformed posture first (`CONTRACT_ERROR` (new)), then check-set
  difference (`CHECKSET_MISMATCH` (new)), then pass/fail agreement (`MATCH_PASS` (new), `MATCH_FAIL` (new),
  `AGENT_ONLY_FAIL` (new), `SERVER_ONLY_FAIL` (new)). Ordering matters: a check-set difference makes a
  pass/fail verdict meaningless.
- `format_shadow_report()` emits `server_key`, `outcome`, and sorted check-id lists only.

### Details

- The old audit produces `list[str]` warnings from `audit_security_defaults`
  (`scripts/agent/services/security_audit.py:40`); the mapping from those strings to check ids is
  defined in the driving test, not here, and is deleted together with the audit in row `20`.
- Keep the module under 140 lines.

## Compatibility considerations

- New module, no runtime call site: it is used by tests and by an operator command only, so it
  cannot affect startup behavior.
- It is deleted or retired only after `REQ-017` (rows `20`-`25`) lands, because before that the
  old audit is the only source of the comparison's left side.

## Security considerations

- `REQ-016` / `REQ-004`: the report must not contain a raw config value, allowlist entry, path, or
  token. The report is built from ids and reason codes, and `format_shadow_report()` must not
  include any message text that came from the audit side.

## Rollback considerations

- Revert the commit. Nothing depends on the harness at runtime.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Outcome matrix | `uv run pytest tests/shared/test_shadow_validation.py -v` (new test file) | each of the six outcomes is produced by a dedicated fixture |
| Blocking condition | same test file | `CHECKSET_MISMATCH` (new) is returned whenever the two check-id sets differ, regardless of pass/fail |
| Non-secret report | same test file | a fixture whose audit messages contain a token-like string produces a report without it |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; `shared-is-leaf` keeps |

## Completion criteria

- Plan `AC-009`: the harness compares old-audit and new-self-validation results and emits no raw
  config value.
- A `CHECKSET_MISMATCH` (new) result is representable and testable, because the Plan makes it the
  condition that blocks canonicalization.

## Out of scope

- Removing the old audit (rows `20`-`25`).
- Deciding the per-server check lists (rows `07`-`16`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `shadow_validation.py` per Procedure/Method/Details | Completed | — | 20261016-184342 | retirement decision open stale gate: 11 unmarked (new) names marked (21 markers); the detector was run after writing the module, so its only finding was new_target_exists for the file this row creates (no symbol_missing or target_missing), i.e. the doc is not stale. Contract finalized: compare_shadow_results(audit_warnings, posture, audit_check_ids) -> ShadowComparison; audit_check_ids maps each old-audit warning text to the new-side check id and lives in the driving test, so it is retired with the audit in row 20. Decision: a server check counts as flagged when its status is FAILED or WARNING, because the old audit's only signal is a warning, so MATCH_PASS and MATCH_FAIL compare flagged sets rather than FAILED sets. Outcome order: CONTRACT_ERROR, then CHECKSET_MISMATCH, then pass/fail. CONTRACT_ERROR covers a server key that is not non-secret (reported under the placeholder unknown), posture contract_version drift, check-to-posture version drift, duplicate check ids, and an audit mapping id that is not non-secret. format_shadow_report emits outcome plus sorted ids only; audit message text never reaches it. Module is 131 lines, within the 140-line guideline |
| 2 | Add `tests/shared/test_shadow_validation.py` per Validation plan | Completed | 20261016-184342 | 20261016-184342 | tests/shared/test_shadow_validation.py: 19 tests, all pass; covers the six-outcome matrix, CHECKSET_MISMATCH winning over both a matching pass and a matching failure, CONTRACT_ERROR winning over a check-set difference, and a report built from an audit message containing a token-like string and an absolute path |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-184342 | 20261016-184342 | ruff clean; mypy 421 files clean; lint-imports 6 kept (shared-is-leaf holds, no audit or server import); bandit 3 Low B105 false positives across scripts/shared/security (enum values named common.auth_token, auth_token_missing, match_pass), no medium or high; bare-except constraint 0 hits; check_docstrings.py reports no finding in scripts/shared/security/; full suite 8595 passed, 19 skipped, 9 pre-existing failures in tests/agent/test_startup_rollback.py; N/A: no docs/00_index.md task-scope mapping for scripts/shared/security/shadow_validation.py |

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
- **Requirement ID**: `REQ-016` (Shadow Validation during migration)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/shared/security/shadow_validation.py`