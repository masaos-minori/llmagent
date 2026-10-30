## Goal
Create the machine-readable authority model `config/adr_authority.toml` (new): authority matrix, typed ADR edges, and the architecture-assumption registry that rows 03–05 consume (REQ-002 model file).

## Scope
- In scope: the TOML file and its three entry families with seed content transcribed from current prose authorities.
- Out of scope: tools (rows 03–05), index generation (row 06), ADR-016 body (row 01).

## Current shape (facts)
- `config/documentation_canonical_sources.toml` exists with `version = "1"` and `[[canonical_sources]]` tables (`decision_target`, `claim_type`, `source_paths`, `area`, `notes`) — the naming/registry idiom this file mirrors; it maps targets to source paths, not to ADRs.
- Today's prose authorities (verified in `docs/10_adr/adr_01_index.md` ADR List and dependency rows): ADR-001 workflow control; ADR-014 component responsibility; ADR-003 routing/LLM visibility/dynamic health/approval; ADR-007 transport; ADR-012 MCP technical safety; ADR-006 EventBus persistence; ADR-013 EventBus authorization; ADR-008 DB separation/recovery; ADR-005 RAG canonical data; ADR-010 fallback; ADR-015 reference generation.
- Six intentional circular reference pairs are listed under `docs/10_adr/adr_01_index.md` "Intentional Circular References" (`:83` heading); they seed the `Reference`-edge `intentional` flags.

## Assumptions
- Plan Assumption transcribed: separate file from `documentation_canonical_sources.toml`; same TOML/checker idiom; owner-revisable placement.
- No target is contested today (Plan UNK-02); transcription records prose as-is. If row 04's first run finds a duplicate primary, that becomes an owner question — do not silently pick a winner here.
- Assumption seed (Plan Assumption): single-host, local SQLite, loopback-only, single-Agent. Exact per-ADR wordings across the 7 matching ADR files are enumerated during implementation (Plan UNK-01) before finalizing `applicable_adrs` lists. Needs confirmation: the enumerated `applicable_adrs` per assumption after the file-level wording pass.

## Design decisions
- Three entry families exactly as the Plan Design specifies:
  - `[[authority]]`: `decision_target` (dotted, mirroring canonical-sources naming, e.g. `agent.tool-routing`), `primary_adr`, `supplemental_adrs = [{adr, limit}]`.
  - `[[adr_edge]]`: `from`, `to`, `edge_type` in {`Requires`, `Governs`, `Specializes`, `Extends`, `Exception-to`, `Reference`}; `intentional = true` on the six circular `Reference` pairs.
  - `[[assumption]]`: `id` (`ARCH-NNN`), `name`, `current_value`, `applicable_adrs`, `validation_method` (`config-check` | `manual-review`), `owner`, `review_triggers`.
- 14 governed targets from REQ-002's list; `validation_method = "config-check"` initially only for loopback-only and single-Agent (Plan UNK-03); others `manual-review`.
- `version = "1"` header and comment blocks naming ADR-016 as the normative owner of this file's semantics.

## Alternatives considered
- Extending `documentation_canonical_sources.toml` with ADR fields — rejected by Plan Assumption: mixes source-path claims with ADR-authority claims in one registry.
- YAML model — rejected: the config registry family is TOML and `check_canonical_source_registry.py`'s loader idiom transfers directly.

## Implementation
### Target file
- `config/adr_authority.toml` (new)

### Procedure
1. Enumerate the 14 `[[authority]]` entries from the verified prose authorities (Design/Current shape); supplemental limits transcribed from ADR text (e.g. ADR-004 on failure-classification targets).
2. Transcribe typed edges from the index dependency rows (`adr_01_index.md` "ADR Dependency Graph", `:62`) plus ADR-016's own edges; classify normative vs `Reference`; flag the six intentional cycles.
3. Search the 7 assumption-bearing ADR files for the four shared assumptions; record canonical wordings and populate `[[assumption]]` entries (ARCH-001..), resolving UNK-01 at authoring time.
4. Confirm with a first `tools/check_adr_authority.py` run (row 04, once implemented) that the model validates — iterate here if findings appear.

### Method
New file in `config/`; land first in `seq` order (rows 03–05 consume it). Do not edit `documentation_canonical_sources.toml`.

### Details
- `ADR-016` must appear as a node in `[[adr_edge]]` entries once row 01's `related` edges exist; land the two rows in one sitting to keep AC-5 satisfied at every commit.

## Compatibility considerations
- `deploy.sh` copies `config/` selectively per server; a docs-governance config must not be added to any server copy list (Plan Affected areas: confirm at deploy step, no `deploy.sh` edit).

## Security considerations
- None; the model holds governance metadata only.

## Rollback considerations
- Any revert of this file must be paired with row 06 regeneration and row 04 rerun; a stale generated index would otherwise diverge from the model.

## Validation plan
- `uv run python tools/check_adr_authority.py` clean (after row 04 lands).
- `uv run python tools/generate_adr_authority.py --check` byte-reproducible (after row 03 lands).
- `uv run python tools/check_canonical_source_registry.py` unaffected (file untouched).

## Completion criteria
- All 14 targets resolve to exactly one primary; every edge type is in the closed set; four assumptions registered with wordings; validator and generator pass.

## Out of Scope
- CI wiring (row 11), docs prose (rows 06–08), tool code (rows 03–05).

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
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 02, REQ-002/REQ-004; resolves UNK-01 and tests UNK-02 on first validator run.
