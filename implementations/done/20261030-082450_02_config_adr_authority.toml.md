## Goal
Create the machine-readable authority model `config/adr_authority.toml` (new): authority matrix, typed ADR edges, and the architecture-assumption registry that rows 03–05 consume (REQ-002 model file).

## Scope
- In scope: the TOML file and its three entry families with seed content transcribed from current prose authorities.
- Out of scope: tools (rows 03–05), index generation (row 06), ADR-016 body (row 01).

## Current shape (facts)
- `config/documentation_canonical_sources.toml` exists with `version = "1"` and `[[canonical_sources]]` tables (`decision_target`, `claim_type`, `source_paths`, `area`, `notes`) — the naming/registry idiom this file mirrors; it maps targets to source paths, not to ADRs.
- Today's prose authorities (verified in `docs/10_adr/adr_01_index.md` ADR List and dependency rows): ADR-001 workflow control; ADR-014 component responsibility; ADR-003 routing/LLM visibility/dynamic health/approval; ADR-007 transport; ADR-012 MCP technical safety; ADR-006 EventBus persistence; ADR-013 EventBus authorization; ADR-008 DB separation/recovery; ADR-005 RAG canonical data; ADR-010 fallback; ADR-015 reference generation.
- Six intentional circular reference pairs are listed under `docs/10_adr/adr_01_index.md` "Intentional Circular References" (`:83` heading); they seed the `Reference`-edge `intentional` flags.

### Verified 20261030 (adversarial pass)
- Confirmed anchors: Dependency Graph heading `:62`, fence block `:67-81` (13 lines, 33 edges), circular heading `:83`, six pair bullets `:87-92`, closing area-graph prose `:94-97`, ADR List `:41-58`, ADR-011 note `:60`.
- New fact: the six ADR files' front matter `related` lists 31 ADR→ADR edges — a strict subset of the 33 fence edges; `ADR-003 → ADR-004` and `ADR-012 → ADR-007` exist only in the fence. Divergence rule agreed across rows 04/05 (resolves a plan ambiguity: bidirectional detection must not flag today's consistent index): every front-matter `adr_02_*` related edge must exist in the model (else `FRONTMATTER_DIVERGENCE`); every non-`Reference` model edge must appear in the owning ADR's front matter (else `FRONTMATTER_DIVERGENCE`); a model-only `Reference` edge is allowed — the model is the superset the generated graph reproduces. No ADR-file front matter is edited by this plan.
- New constraint: in each of the six bidirectional pairs exactly one direction may carry a non-`Reference` type, or `AUTHORITY_CYCLE` fires; and typed directions must be front-matter-present (see rule above). Proposed split (derived from the bullets' ownership wording, to re-confirm at authoring): `001 →(Requires) 004` / `004 →(Reference, intentional)`; `014 →(Extends) 001` / `001 →(Reference, intentional)`; `004 →(Requires) 002` / `002 →(Reference, intentional)`; `004 →(Extends) 003` / `003 →(Reference, intentional)` — typed direction flipped to `004 → 003` because `003 → 004` is front-matter-absent; `010 →(Exception-to) 004` / `004 →(Reference, intentional)`; `013 →(Specializes) 006` / `006 →(Reference, intentional)`. All other fence edges (incl. `012 → 007`) seed as `Reference`. `ADR-016` adds exactly one edge: `016 →(Reference) 015`.
- Assumption wording pass (partial UNK-01 resolution): loopback/127.0.0.1 wording found in 3 ADR files (ADR-007, ADR-006, ADR-013); broad single/local-SQLite wording matches 11 ADR files — exact `applicable_adrs` per assumption still finalized at authoring (UNK-01 remains open until row 02 is authored).
- Deviation found: `config/agent.toml` has no single-agent key (top-level keys enumerated 20261030; no agent-count/process setting) — the single-Agent assumption cannot be `validation_method = "config-check"`. Decision: `ARCH` single-Agent → `manual-review`; loopback-only stays `config-check` via `mcp_servers.*.url` hosts (all 10 verified `http://127.0.0.1:*`). Needs confirmation: owner sign-off for deviating from Plan UNK-03's config-check pair.

## Assumptions
- Plan Assumption transcribed: separate file from `documentation_canonical_sources.toml`; same TOML/checker idiom; owner-revisable placement.
- No target is contested today (Plan UNK-02); transcription records prose as-is. If row 04's first run finds a duplicate primary, that becomes an owner question — do not silently pick a winner here.
- Assumption seed (Plan Assumption): single-host, local SQLite, loopback-only, single-Agent. Exact per-ADR wordings across the 7 matching ADR files are enumerated during implementation (Plan UNK-01) before finalizing `applicable_adrs` lists. Needs confirmation: the enumerated `applicable_adrs` per assumption after the file-level wording pass.

## Design decisions
- Three entry families exactly as the Plan Design specifies:
  - `[[authority]]`: `decision_target` (dotted, mirroring canonical-sources naming, e.g. `agent.tool-routing`), `primary_adr`, `supplemental_adrs = [{adr, limit}]`.
  - `[[adr_edge]]`: `from`, `to`, `edge_type` in {`Requires`, `Governs`, `Specializes`, `Extends`, `Exception-to`, `Reference`}; `intentional = true` on the six circular `Reference` pairs.
  - `[[assumption]]`: `id` (`ARCH-NNN`), `name`, `current_value`, `applicable_adrs`, `validation_method` (`config-check` | `manual-review`), `owner`, `review_triggers`.
- 14 governed targets from REQ-002's list; `validation_method = "config-check"` only for loopback-only (single-Agent moved to `manual-review` per the Verified note — config knob absent). Others `manual-review`.
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
| Completed | 20261030-193223 | 20261030-193223 | Adversarial verification complete 20261030: 14 REQ-002 targets confirmed; divergence rule + typed-edge split recorded; single-Agent config-check deviation found (owner confirmation needed). Lands first among code rows. |

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