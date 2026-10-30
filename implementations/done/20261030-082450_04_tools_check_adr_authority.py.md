## Goal
Create `tools/check_adr_authority.py` (new) plus the shared validator core `tools/_adr_authority_core.py`: reject duplicate primaries, dangling ADR IDs, authority-graph cycles, and assumption drift (REQ-004 CI validator, finding-code design).

## Scope
- In scope: the validator CLI module and the core module imported by both row 04's CLI and row 05's extended `check_adr_reference.py`.
- Out of scope: the model (row 02), front-matter extension wiring inside `check_adr_reference.py` (row 05), CI steps (row 11), tests (row 12).

## Current shape (facts)
- No ADR-graph cycle check exists: `tools/check_dependency_graph_cycles.py` covers only the software area graph, and `docs/10_adr/adr_01_index.md` states the cycle prohibition "applies to the area nodes ... not to this ADR reference graph" (verified `:95-97`).
- `tools/_front_matter_schema.py` exists as the underscore-prefixed shared-helper precedent in `tools/` — the core module follows that naming.
- `check_adr_reference.py` already fails when its matrix yields no source references — the fail-closed pattern this validator mirrors.

### Verified 20261030 (adversarial pass)
- Confirmed: `check_dependency_graph_cycles.py` covers the software area graph only; the index closing prose excluding the ADR graph from the cycle prohibition is at `adr_01_index.md:94-97` (procedure said `:95-97`).
- Resolved (was Needs-confirmation): the loopback `config-check` assertion is implementable — `config/agent.toml` `[mcp_servers.*].url` hosts, all 10 verified `http://127.0.0.1:*` (20261030 tomllib pass). The single-Agent assumption has NO config knob in `config/agent.toml` (top-level keys enumerated; no agent-count/process key) → single-Agent is `manual-review` in the model, and the core's config-check dispatch covers loopback-only. Deviation from Plan UNK-03 recorded in row 02; owner sign-off flagged in the final report.
- Confirmed: `tools/_front_matter_schema.py` exists as the underscore shared-helper precedent, and underscore tools must ALSO be registered in `tools/TOOL_DESCRIPTIONS.md` (`check_tool_descriptions_sync.py` lists every `tools/*.py` except `__init__.py`; `_docs_consistency_lib.py`/`_front_matter_schema.py` carry "Shared base" rows at `TOOL_DESCRIPTIONS.md:19-20`, `:80-81`) — row 10 registers `_adr_authority_core.py` likewise.
- Front-matter cross-check scope decision (prevents false findings on today's consistent set): only `adr_02_GG_NNN_*.md` files participate; `adr_01_index.md` and `adr_00_document-guide.md` front matter lists ADR paths as navigation links, not edges. Divergence directions flagged: front-matter `adr_02_*` related edge missing from the model; non-`Reference` model edge missing from the owning ADR's front matter. Model-only `Reference` edges are clean (row 02's Verified note holds the full rule).
- Confirmed: `check_adr_reference.py` runs via pre-commit hook `adr-reference-scoped` (`.pre-commit-config.yaml:60-62`), not a direct ci.yml step — the row 05 extension must stay compatible with hook invocation (`python -m tools.check_adr_reference`, `pass_filenames: false`).

## Assumptions
- Core module name: `tools/_adr_authority_core.py` (Plan Design: "validator core lives in one module both tools import"; underscore naming per `_front_matter_schema.py` precedent). It holds: TOML model loader, finding dataclass with codes `DUP_PRIMARY`, `DANGLING_ADR`, `AUTHORITY_CYCLE`, `ASSUMPTION_DRIFT`, `EDGE_UNKNOWN_TYPE`, `FRONTMATTER_DIVERGENCE`, model validation entry points, and the front-matter/model cross-check function row 05 calls.
- `DANGLING_ADR`: every `primary_adr`, `supplemental_adrs[].adr`, `adr_edge.from/to`, and `applicable_adrs` entry must resolve to an ADR file present in `docs/10_adr/` (filename pattern `adr_*_<NN>_*`), closing Plan UNK-02 mechanically.
- Assumption drift for `validation_method = "config-check"`: assert model `current_value` against live config values — resolved 20261030 to the `mcp_servers.*.url` loopback hosts only (single-Agent has no config key; see Verified note, model records it `manual-review`).

## Design decisions
- Authority graph = all non-`Reference` edges; cycle detection (DFS on the directed graph) applies there only. `Reference` edges may cycle; the six intentional pairs must carry `intentional = true` — an unflagged `Reference` cycle is a finding, and a flagged cycle missing from the model is `AUTHORITY_CYCLE`-adjacent bookkeeping handled as a finding code reuse note (flag consistency check lives in core).
- `ASSUMPTION_DRIFT` for `manual-review` assumptions is not a hard failure at validator level: only `config-check` assumptions fail; review triggers are documented in the model and enforced by PR review (Plan Design), keeping the check fail-closed but not review-policing.
- CLI contract mirrors `check_adr_reference.py`: no args required, `--format json`, nonzero exit on any finding, findings printed one per line with code + detail.

## Alternatives considered
- Putting the core inside `check_adr_authority.py` and importing the tool module from `check_adr_reference.py` — rejected: importing a CLI module for library use invites argparse/side-effect coupling; underscore core matches `_front_matter_schema.py`.
- Enforcing acyclicity on the whole reference graph — rejected: contradicts the six owner-approved intentional cycles (REQ-001 graph rules).

## Implementation
### Target file
- `tools/check_adr_authority.py` (new)

### Procedure
1. Write `tools/_adr_authority_core.py` first (loader, findings, validators, cycle DFS, cross-check helper). Note: the core file is created by this row's landing (it is a helper of the two registered tools, not a separate Implementation Target Files row; rows 03/05 import it).
2. Write the CLI: load model → run all validators → report; exit 1 on any finding.
3. `config-check` assumptions validated against `config/agent.toml` values read via the existing config-reading idiom used in `tools/` (no new config parser).
4. Register nothing here: rows 09–11 handle `routing.md`, `TOOL_DESCRIPTIONS.md`, and CI.

### Method
Land before rows 03 and 05 in `seq` order (both import the core). Pure-stdlib tool (tomllib, no new deps per `rules/coding.md`).

### Details
- The core's front-matter cross-check enumerates ADR `related` entries (per `_front_matter_schema.py` field contract) and model `adr_edge` rows; `FRONTMATTER_DIVERGENCE` findings list the ADR file and the offending edge.

## Compatibility considerations
- Row 05 keeps `check_adr_reference.py`'s existing matrix-marker check untouched; the new section calls core functions additively.
- `tools/check_auto_check_inventory.py` (row 08's validation target) must find this tool registered in `routing.md` and `governance_04_documentation-checks.md` in the same landing batch (rows 08–10).

## Security considerations
- Read-only tool; no writes. `--format json` output must not leak config file contents beyond the compared values (report key names + mismatch, not full config dumps).

## Rollback considerations
- Revert requires undoing rows 03/05 imports and row 11's CI step in one change set; a dangling import would crash CI otherwise.

## Validation plan
- `uv run pytest tests/tools/test_adr_authority.py` (row 12) passes: each finding code has a fixture-model failure case plus a conforming-model clean case.
- First real run against the row 02 model is clean (or findings are escalated as owner questions per UNK-02, not silently patched).
- `uv run python tools/check_adr_reference.py` still passes its original scope.

## Completion criteria
- Six finding codes implemented and tested; authority-cycle detection proven on fixture cycles; clean run on the real model.

## Out of Scope
- Model content (row 02), generator (row 03), `check_adr_reference.py` body edits (row 05), CI/docs registration (rows 08–11).

## Execution Status

### Execution Status
| Status | Started | Completed | Notes |
|---|---|---|---|
| Completed | 20261030-193223 | 20261030-193223 | Adversarial verification complete 20261030: config-check keys resolved (mcp_servers loopback hosts; single-Agent → manual-review), front-matter cross-check scope/direction rules recorded, pre-commit hook compatibility noted. Lands first in the batch work order. |

### Blocker Log
| Date | Blocker | Impact | Resolution |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Type | Status | Notes |
|---|---|---|---|
| — | — | — | — |

## Traceability
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 04, REQ-004 (AC-2, AC-3); core also serves REQ-005 via row 05.