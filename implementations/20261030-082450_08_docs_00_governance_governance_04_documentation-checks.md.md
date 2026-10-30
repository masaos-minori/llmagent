## Goal
Register the two new ADR-authority checks in the Governance Verification Matrix of `docs/00_governance/governance_04_documentation-checks.md` (`Method = Auto` rows) so the auto-check inventory cross-reference passes (REQ-006).

## Scope
- In scope: matrix rows (and, if required by the doc's numbering discipline, the corresponding automated-checks list entries) for `check_adr_authority.py` and `generate_adr_authority.py`, plus the extended behavior note for `check_adr_reference.py`.
- Out of scope: tool code (rows 03–05), `routing.md` (row 09), `TOOL_DESCRIPTIONS.md` (row 10), `ci.yml` (row 11).

## Current shape (facts)
- The matrix exists with rows shaped `| GV-NNN | Check | Class | Auto/Manual | Tool | Stage | Severity | Status | Notes |` (verified rows GV-001..GV-004 at `:273-276`); automated check items 1-14 exist under `## Automated Checks` (`:24`) with a numbered item at `:181` describing `check_adr_invariant_matrix.py`/`check_adr_reference.py`.
- `tools/check_auto_check_inventory.py`'s docstring names this file as the authoritative enumeration of auto checks (plan evidence; tool exists — verified in `tools/`).

## Assumptions
- New rows continue GV numbering (implementation reads the current max GV number and appends two Auto rows: "ADR authority model validation" and "ADR index generated-section drift"). Needs confirmation: the exact next GV numbers at implementation time.
- The extension of `check_adr_reference.py` (row 05) is folded into the existing GV item's description text (as `:181` already folds both tools into one item), not a new GV row — one GV row for the front-matter/model cross-check is added only if the inventory checker requires per-check granularity; verify by running `check_auto_check_inventory.py` after the first edit.

## Design decisions
- Matrix severity/stage cells mirror the precedent rows: Stage `PR`, Severity `Blocking` (both checks gate ADR governance like GV-003's ADR-ID uniqueness).
- The `## Automated Checks` numbered list gains the two tools with one-sentence intent descriptions matching their `TOOL_DESCRIPTIONS.md` rows (row 10 authors those with identical wording — coordinate phrasing, single source of intent).

## Alternatives considered
- Registering only in `routing.md` — rejected: `check_auto_check_inventory.py` cross-references both `governance_04_documentation-checks.md` and `routing.md` enumerations against real scripts; a tool missing from either enumeration is an inventory finding (plan evidence).

## Implementation
### Target file
- `docs/00_governance/governance_04_documentation-checks.md` (modify)

### Procedure
1. Read current GV numbering and the Automated Checks item list fully.
2. Append two Auto matrix rows and two numbered item entries; extend the existing ADR-checks item with the new front-matter/model cross-check sentence.
3. Run `uv run python tools/check_auto_check_inventory.py` — if it demands granularity the fold-in doesn't satisfy, split row 05's extension into its own GV row.

### Method
Docs registration landing after rows 03–05 (tools exist as scripts before being inventoried). Part of the same landing batch as rows 09–11 (inventory must see tool + routing + CI + matrix together).

### Details
- Wording constraint: matrix rows describe what is checked (governance claims), not implementation internals.

## Compatibility considerations
- `check_auto_check_inventory.py` itself runs in CI already (row 11 does not add it; it is existing). This row must keep it green: every named script must exist at check time — hence landing after rows 03–05.

## Security considerations
- None.

## Rollback considerations
- Revert in lockstep with rows 09–11 to avoid inventory drift findings.

## Validation plan
- `uv run python tools/check_auto_check_inventory.py` exits 0.
- `uv run pytest tests/tools/test_check_auto_check_inventory.py` passes.
- Docs checkers from `routing.md` pass.

## Completion criteria
- Both new tools appear in matrix + automated-checks list; inventory checker green.

## Out of Scope
- `routing.md`/`TOOL_DESCRIPTIONS.md`/CI edits (rows 09–11).

## Execution Status

### Execution Status
| Status | Started | Completed | Notes |
|---|---|---|---|
| Pending | — | — | — |

### Blocker Log
| Date | Blocker | Impact | Resolution |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Type | Status | Notes |
|---|---|---|---|
| — | — | — | — |

## Traceability
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 08, REQ-006.
