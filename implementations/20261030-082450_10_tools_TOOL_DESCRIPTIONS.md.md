## Goal
Register the two new tools in `tools/TOOL_DESCRIPTIONS.md` (summary table + detailed table) to keep the `tools/`↔`TOOL_DESCRIPTIONS.md` registry current (REQ-006, AGENTS rule 9).

## Scope
- In scope: two summary rows and two detail rows.
- Out of scope: everything else.

## Current shape (facts)
- `tools/TOOL_DESCRIPTIONS.md` has a compact registry table (`| tool | category | one-liner |`, e.g. `check_adr_reference.py` at `:22`, `generate_reference_table.py` at `:50`) and a detailed table (`| tool | inputs | behavior |`, e.g. `check_adr_reference.py` at `:90`, `generate_reference_table.py` at `:107` with `--check` exit-1 semantics spelled out).
- AGENTS.md rule 9 and the drift checker named in `routing.md` enforce this registry against real `tools/` scripts.

## Assumptions
- Summary categories: `ADR` for `check_adr_authority.py`, `Reference generation` for `generate_adr_authority.py` (mirrors the existing categories at `:22`/`:50`).
- Detail rows spell out: inputs (`config/adr_authority.toml`, `docs/10_adr/adr_02_*.md` front matter, `config/agent.toml` for config-check assumptions) and behavior (finding codes list for the validator; `--check` exit-1-on-drift for the generator) — one-sentence-per-claim style matching `:90`/`:107` rows.

## Design decisions
- Wording identical in intent to rows 08–09 (governance matrix and routing) — the three registrations are one claim stated in three registries; implementer drafts the sentence once (this row's wording is the canonical one; rows 08–09 shorten from it).
- Both new tools' rows note `Read-only.`/`Writes only docs/10_adr/adr_01_index.md guarded regions.` following the precedent suffix pattern (`:90` ends "Read-only.").

## Alternatives considered
- Skipping the detail table — rejected: precedent rows for every CI-running tool carry detail entries; drift checker and humans expect parity.

## Implementation
### Target file
- `tools/TOOL_DESCRIPTIONS.md` (modify)

### Procedure
1. Add two summary rows in the ADR/Reference-generation neighborhoods.
2. Add two detail rows after `generate_reference_table.py`'s detail row region.
3. Run the drift checker listed in `routing.md` plus `tools/check_auto_check_inventory.py`.

### Method
Registry edit landing after rows 03–05 (tools exist) in the same batch as rows 08–09, 11.

### Details
- High-churn file (73/30d per plan): keep the edit to four added rows only to minimize rebase conflict surface.

## Compatibility considerations
- The drift checker fails on registry↔scripts mismatch in either direction: land this row in the same commit as the tools themselves (rows 03–05) so no intermediate commit has an unregistered script.

## Security considerations
- None.

## Rollback considerations
- Revert with rows 08–09, 11 (registry consistency in lockstep).

## Validation plan
- Drift checker (per `routing.md` Tools → "When to run which tool") passes.
- `uv run python tools/check_auto_check_inventory.py` exits 0.

## Completion criteria
- Four rows present; checkers green.

## Out of Scope
- Tool behavior itself, other registries.

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
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 10, REQ-006.
