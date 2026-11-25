## Goal

Turn the section prepare phase into a typed-candidate phase that carries the field path, and remove
the half of the module that no production path reaches (REQ-001, typed candidate; REQ-003,
startup-only filtering; REQ-013, dead-code removal).

## Scope
**Release unit**: R2-typed-registry

## Assumptions
- Verified against current source: `prepare_direct_section` (`config_section_reload.py:109`) and
  `apply_direct_section` (`config_section_reload.py:144`) are called only for `section_path == "mcp"`
  from `config_reload.py:127`, and `registry_for("mcp")` returns an empty list, so the direct path
  validates nothing.
- `reload_validated_section` (`config_section_reload.py:87`) and `reload_direct_fields`
  (`config_section_reload.py:161`) have no callers in `scripts/` or `tests/` — fully dead code.
- The transaction that owns the undo token is row 7; this module returns the candidate and the token
  the transaction records, it does not commit.

## Design decisions
- `prepare_validated_section` returns a typed section object rather than a raw changed-field dict, so
  the candidate is the same object shape the startup builder produces.
- The field path travels with the candidate, which is what lets the error name the field.

## Alternatives considered
- Keeping the direct-section pair for the MCP section — rejected: the MCP section is restart-only
  under this Plan (row 8), so a live direct apply is the behavior AC-4 removes.

## Implementation
### Target file
`scripts/agent/services/config_section_reload.py`

### Procedure
Make candidates typed objects carrying the field path; delete `reload_validated_section`,
`reload_direct_fields`, `prepare_direct_section`, and `apply_direct_section`.

### Method
- `prepare_validated_section` keeps its no-mutation contract and returns the typed candidate built by
  the shared primitives plus the field paths it changed.
- `apply_validated_section` becomes the commit-side call the transaction drives and returns the undo
  token row 7 defines.

### Details
- The `extra_changed_fields` argument stays for `masked_fields`, which is not a registry entry
  (`config_section_reload.py:31` records this); its value is compared against live state before any
  mutation.
- Deleting the four functions removes the only path that applied a section without a snapshot.
- Executed: the declared `FieldRule` runs before the unchanged comparison, so a wrong-typed value is
  rejected instead of being skipped because `1 == True`. This needed a new shared symbol,
  `apply_field_rule(rule, value, field_path, *, allow_empty)`, beyond the Plan's row 1 symbol list;
  `config_outcome_classification.classify_startup_only_fields` applies the same type-aware rule so a
  wrong-typed startup-only value is reported as pending rather than silently equal.

## Compatibility considerations
- No test references the deleted helpers, so their deletion needs no test retargeting; row 34
  retargets the other reload tests.

## Security considerations
- No raw value in error text; the field path is the only identifier in the message.

## Rollback considerations
- Revert the Phase 2 commit; the module is stateless.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_parity.py -q`
- `uv run vulture scripts/agent/services/ --min-confidence 60` — no unreachable reload helper remains
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- No function in this module performs a live mutation without returning an undo token, and the deleted
  helpers have no remaining reference in `scripts/` or `tests/`.

## Out of Scope
- The transaction and rollback model (row 7).
- Test retargeting (row 34).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-154000 | 20261125-163000 | deletion lands with row 34 retargeting typed frozen SectionCandidate returned; prepare_direct_section and apply_direct_section deleted; the mcp direct loop removed from config_reload.py; declared field rule applied before the unchanged comparison via new shared apply_field_rule; undo-token return deferred to row 7 (R4) |
| 2 | Add or update tests per Validation plan | Completed | 20261125-154000 | 20261125-163000 | row 34 row 27 parity file plus the retargeted tests/agent/services/test_config_reload.py suite |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-154000 | 20261125-163000 | vulture scripts/ shows only pre-existing unused-variable findings; no reload helper remains |

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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-003 (startup-only fields stay pending), REQ-013 (dead reload code removed); AC-2
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/config_section_reload.py`