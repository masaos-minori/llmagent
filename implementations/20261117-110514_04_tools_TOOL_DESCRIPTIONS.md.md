## Goal
Update the `check_compat_shims.py` and `_compat_leftover_phrases.py` rows in `tools/TOOL_DESCRIPTIONS.md` (short table and detailed section) so the described behavior includes the always-on contract guards and the helper's expanded responsibility, in the same change as the procedure 02 wiring (`REQ-008`).

## Scope
**Release unit**: N/A: not part of a release unit; ship in the same change as procedure 02 (the wiring that expands the described behavior).

- `tools/TOOL_DESCRIPTIONS.md`: the two short-table rows (currently near lines 85-86) and the two detailed-section rows (currently near lines 185-186).
- No other file changes.

## Assumptions
- The described behavior changes under `check_tool_descriptions_sync.py` semantics: the checker gains always-on contract-guard rules and the helper no longer owns only the eleven leftover-phrase regexes — the current rows would then describe a narrower tool than the code is.
- The "eleven `LEFTOVER_PHRASES`" count claim stays correct (the new doc-phrase rule lives in a separate table dispatched by `check_contract_guards`), so only additive description changes are needed, not corrections.

## Design decisions
- Describe rules by behavior, not implementation detail: "always-on contract guards that reject reintroduced dataclass defaults on `RetryPolicy.retry_on` / `WorkflowDef.stages` / `WorkflowDef.retry_policy`, an optional or defaulted `lease_duration_sec` in the attempt writer path, nullable `owner_id` / `lease_expires_at` in the canonical `attempts` DDL, and current-tense `legacy age threshold` wording in `docs/` unless marked `removed`/`historical`/`withdrawn`".
- Record the extraction: the helper now also owns `check_mcp_health_reexport_import` (moved from the checker by procedure 02), so the checker row's "syntax-tree rules" phrasing must attribute helper-owned rules to the helper rather than imply they live in the checker file.

## Alternatives considered
- Leaving the rows unchanged: rejected — `check_tool_descriptions_sync.py` exists precisely to fail on this drift, and the plan `REQ-008` mandates the same-change update.

## Implementation
### Target file
- `tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. After procedure 02 lands, run `uv run python tools/check_tool_descriptions_sync.py` and read its findings.
2. Update the `check_compat_shims.py` short-table row: add the always-on contract guards in one clause and name the helper aggregate `check_contract_guards (new)` as the supplier.
3. Update the `check_compat_shims.py` detailed row: extend the "always-on syntax-tree (AST) rules" paragraph with the contract guards and note `check_mcp_health_reexport_import` is now helper-supplied; keep the `--check-removed-names` / `--check-doc-symbols` / manifest paragraphs byte-for-byte unless their facts changed.
4. Update both `_compat_leftover_phrases.py` rows: state the helper now owns the guard tables (`GUARDED_DATACLASS_DEFAULTS (new)`, `GUARDED_DEFAULTED_PARAMS (new)`) and the four guard functions (`check_dataclass_field_defaults (new)`, `check_optional_guarded_params (new)`, `check_attempts_ddl_nullability (new)`, `check_historical_doc_phrases (new)`) dispatched through `check_contract_guards (new)`, in addition to the eleven phrase regexes and `python_nodes`; the path-scope wording gains `docs/` for the historical doc-phrase rule.
5. Re-run `uv run python tools/check_tool_descriptions_sync.py` until it exits 0.

### Method
- Row edits only; no new rows (no tools are added or removed).

### Details
- Keep each row's existing column structure and tone; the short rows are one sentence, the detailed rows are the long policy paragraphs.
- If the sync checker also flags the module-size baseline tightening (it should not — it is tool data, not a described behavior), leave it out of the description.

## Compatibility considerations
- `tools/TOOL_DESCRIPTIONS.md` is consumed by `check_tool_descriptions_sync.py` (and is out-of-scope for deployment rsync per `skills/DESIGN.md` Out-of-scope paths); no runtime consumer changes.
- `tests/tools/test_check_tool_descriptions_sync.py` keeps its current contract; no test change is expected.

## Security considerations
N/A: documentation-only change; no code surface.

## Rollback considerations
- Revert this file together with procedure 02 (description and behavior move as one change); reverting only the description would re-trigger `check_tool_descriptions_sync.py`.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — exits 0 with the expanded behavior described.
- `uv run python tools/check_workitem_structure.py --file tools/TOOL_DESCRIPTIONS.md` if the checker applies to this file per `routing.md` "When to run which tool"; otherwise the sync checker is the gate.

## Completion criteria
- Both tools' rows in both the short table and the detailed section describe the contract guards, the helper-owned `check_mcp_health_reexport_import`, and the `docs/` historical doc-phrase allowance; `check_tool_descriptions_sync.py` exits 0 in the same change as procedure 02.

## Out of Scope
- Any `docs/*.md` change (the workflow/lease documentation is owned by the sibling plans); the `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md` consistency question stays a plan Reference File item for the compat002 implementer, not this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Gated: only meaningful after procedure 02's wiring lands (compat002 gate) |
| 2 | Add or update tests per Validation plan | N/A | — | — | Existing sync test covers this |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Blocked | — | — | check_tool_descriptions_sync.py after procedure 02 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document is the documentation change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Description update only applies once procedure 02 wires the rules (after compat002 lands) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (tool description updated in the same change when behavior changes)
- **Source issue**: `issues/20261116-114953_compat004_compat-regression-guards.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-235333_compat004_compat-regression-guards.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-110514
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
