## Goal

Extend `tools/check_needs_confirmation_inventory.py` so GV-008 automates all four
Needs-Confirmation field-groups. Add parsers and three `WARNING` checks for the two
previously manual groups — `Last Reviewed` (presence + ISO date) and `Priority`
(enum membership) plus Status/Blocking consistency (`Blocking` references a valid NC
id) — and wire them into `main()`'s aggregation.

## Scope

- **In-Scope**: extend `NcEntry` and `_parse_inventory_entries` to capture
  `last_reviewed`, `priority`, `blocking`; add `check_last_reviewed`,
  `check_priority_valid`, `check_blocking_reference`; register them in `main()`.
- **Out-of-Scope**: recency-threshold enforcement for `Last Reviewed` (no policy
  defines one — UNK-01); serializing/persisting the new fields; any change to another
  governance rule or its tool.

## Assumptions

- New checks adopt `WARNING` severity to match the existing `Assigned To` /
  `Resolution Target` checks and preserve the exit-0-on-warning contract.
- `Priority` matching is case-insensitive against the `governance_03` enum
  (`High`/`Medium`/`Low`).
- Inventory entries use `**Last Reviewed:**`, `**Priority:**`, `**Blocking:**` markers
  consistent with the fifteen-field schema; missing markers map to `None`.
- Currently no active NC items remain, so the new checks operate on an empty list
  against the live corpus; unit tests must supply fixtures.

## Design decisions

- Each new check mirrors the existing shape `(entries: list[NcEntry]) -> list[Issue]`
  with `severity="WARNING"` and is appended to `all_issues` in `main()` — the single
  aggregation/reporting path. No new module-level function signature shape is invented.
- Missing markers map to `None` in the parser so pre-existing entries that lack
  `Last Reviewed`/`Priority`/`Blocking` do not raise, mirroring the existing
  `check_missing_nc_fields` guard for resolved entries.

## Alternatives considered

- Storing parsed values in a plain dict per entry instead of extending the `NcEntry`
  dataclass — rejected; the dataclass matches the existing parser/check pattern and
  keeps field access explicit and typed.

## Implementation

### Target file

`tools/check_needs_confirmation_inventory.py`

### Procedure

1. Extend `NcEntry` with `last_reviewed`, `priority`, `blocking` attributes.
2. Extend `_parse_inventory_entries` to read the three markers (new regexes), treating
   missing values as `None`, and pass them to the `NcEntry` constructor.
3. Add `check_last_reviewed(entries)` — presence + ISO `YYYY-MM-DD` date.
4. Add `check_priority_valid(entries)` — enum membership against `High`/`Medium`/`Low`.
5. Add `check_blocking_reference(entries)` — `Blocking` references a real NC id.
6. Wire all three into `main()` alongside the existing checks.

### Method

- Add three module-level regexes following the existing marker convention
  (`_ASSIGNED_TO_RE`, `_RESOLUTION_TARGET_RE`), allowing the optional trailing `*`
  before the colon so both `**Priority:**` and `**Priority:` parse:

  ```python
  _LAST_REVIEWED_RE = re.compile(
      r"(?:\*\*Last Reviewed:\*\*|\*\*Last Reviewed:\*):\s*(.+)$"
  )
  _PRIORITY_RE = re.compile(
      r"(?:\*\*Priority:\*\*|\*\*Priority:\*):\s*(.+)$"
  )
  _BLOCKING_RE = re.compile(
      r"(?:\*\*Blocking:\*\*|\*\*Blocking:\*):\s*(.+)$"
  )
  ```

- In `_parse_inventory_entries`, add `current_last_reviewed`, `current_priority`,
  `current_blocking` locals (initialized `None`), reset them in the `_NC_ENTRY_RE`
  branch, and populate them via `.search(line)` in the field-discovery loop; pass them
  to `NcEntry(...)` in `flush()`.
- Gate each new check on `entry.status == "open"` to match `check_missing_nc_fields`
  (active items only).
- `check_last_reviewed`: append a `WARNING` when `last_reviewed` is `None` or
  `datetime.strptime(value.strip(), "%Y-%m-%d")` raises.
- `check_priority_valid`: append a `WARNING` when `priority` is `None` or
  `priority.strip().lower()` is not in `{"high", "medium", "low"}`.
- `check_blocking_reference`: build `{e.nc_id for e in entries}`; for each entry with
  `blocking` set (non-empty, non-`None`), append a `WARNING` when that value is absent
  from the id set. Unset `blocking` produces no issue.

### Details

- `REQ-001` (`Last Reviewed`): the check enforces presence and well-formedness only;
  recency is intentionally not enforced (UNK-01). Malformed or missing → `WARNING`.
- `REQ-002` (`Priority`): case-insensitive enum membership; anything outside
  `High`/`Medium`/`Low` → `WARNING`. Values trace to `governance_03` Priority Values.
- `REQ-003` (`Blocking`): per UNK-02 this validates the `Blocking` field, not a
  `Blocked` status (which does not exist in `governance_03`'s Status Values
  `open/investigating/deferred`). A `Blocking` value referencing a non-existent NC id
  → `WARNING`.
- `main()`: add the three calls after `check_missing_nc_fields(entries)`:

  ```python
  all_issues += check_last_reviewed(entries)
  all_issues += check_priority_valid(entries)
  all_issues += check_blocking_reference(entries)
  ```

## Compatibility considerations

No public interface, CLI argument, or exit-code contract changes. Severity stays
`WARNING`, preserving the "warnings → exit 0, ERROR → non-zero" behavior verified by
`TestExitCodeBehavior`.

## Security considerations

N/A: detection-only governance checker; no user input executed, no secrets handled.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_needs_confirmation_inventory.py` | Unit (direct calls with fixtures) | `.venv/bin/python -m pytest tests/tools/test_check_needs_confirmation_inventory.py` | New checks pass; existing 14 tests still pass |
| `tools/check_needs_confirmation_inventory.py` | Integration (corpus run) | `.venv/bin/python tools/check_needs_confirmation_inventory.py` | "No issues found", exit 0 |

## Completion criteria

- `NcEntry` carries `last_reviewed`/`priority`/`blocking`; parser reads the three
  markers without raising on absent values.
- All three checks exist, are gated on `open`, and are wired into `main()`.
- Unit tests cover each new check (valid vs invalid) and the extended parser.
- Existing 14 tests pass; exit-0-on-warning contract holds.

## Out of scope

Recency-threshold enforcement, field serialization, and any other governance rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `NcEntry` + `_parse_inventory_entries` for the three markers | Pending | — | — | REQ-001/002/003 |
| 2 | Add `check_last_reviewed` / `check_priority_valid` / `check_blocking_reference` and wire into `main()` | Pending | — | — | REQ-001/002/003 |
| 3 | Run the tool test suite + corpus run | Pending | — | — | all REQs |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` (automate the `Last Reviewed`,
  `Priority`, and Status/Blocking field-groups of GV-008)
- **Source issue**: `issues/20261018-172829_gov008_automate-needs-confirmation-review-metadata-checks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-175819_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-033526
- **Related target files**: `tools/check_needs_confirmation_inventory.py`
