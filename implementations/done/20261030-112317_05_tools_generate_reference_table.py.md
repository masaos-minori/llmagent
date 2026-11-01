# Implementation Procedure: generate_reference_table.py manifest mode

## Goal

Give `tools/generate_reference_table.py` a manifest mode: generate schema-validated
YAML manifests into `registry/manifests/`, render the guarded Markdown blocks FROM
those manifests, and extend `--check` to detect drift in both directions
(REQ-005; plan AC-4).

## Scope

**In scope:**
- Manifest builders per doc-backed domain (`mcp`, `deployment`, `agent`, `eventbus`,
  `memory` constant groups at `tools/generate_reference_table.py:296-337`).
- Renderer change: `render_updated_doc` (`:342`) and `check_drift` (`:357`) consume the
  manifest as the single intermediate representation instead of calling the table
  generators directly.
- New CLI surface: `--manifests` (write manifests + re-render docs) and
  `--check` extended to manifest↔source and block↔manifest comparisons.

**Out of scope:**
- The seven manifest entry contents (docs 06-13 define sources and rows).
- CI/pre-commit invocation (docs 14-15).

## Assumptions
- Re-verified 2026-10-31 at HEAD `b88531438`: generator is 422 lines; guard constants
  `:47-56`; `DOMAIN_GENERATORS`/`DOMAIN_DOCS`/`DOMAIN_GUARDS`/`DOMAIN_WELCOME_LINES`/
  `DOMAIN_HEADING` `:288-339`; `render_updated_doc :342`; `check_drift :357`; `--check`
  exits 1 on drift; `--type` required without `--check`.
- `registry/manifests/` exists as an empty directory (created during procedure
  generation); YAML files are generated, not hand-written.
- Resolved 2026-10-31: `rag` gets no manifest — its table (`:24-53`) is outside all
  guards and REQ-006 names no rag manifest.

## Design decisions
- One builder function per manifest name returning `(manifest_dict, table_markdown)`;
  the dict is validated against `schemas/contract_manifest.json` (doc 06) with
  `jsonschema` (already a dependency) before any write.
- Rendering manifests beyond the seven REQ-006 names: `agent_api` (new), `eventbus_api` (new),
  `memory_api` (new). The seven REQ-006 manifests carry no symbol-table entries, so the three
  guarded class/function blocks (docs 20/21 and the memory doc) cannot render FROM a
  manifest without them; the schema enum (doc 06) has 10 names. `eventbus_route_roles`
  and `config_ownership`/`health_contracts` are fact manifests with no guard block of
  their own. `mcp` renders from `mcp_endpoints` + `tool_ownership`; `deployment` from
  `db_schema_versions`.
- Migration gate (AC-4): re-rendering all five guarded docs from the generated manifests
  must produce zero git diff except the welcome-line wording change in the three
  plan-targeted docs (mcp_01, eventbus_08, agent_13; the plan's Implementation Target
  Files table excludes the deployment and memory docs); the current table generators'
  scan primitives stay the build path, their formatting code becomes the entry→markdown
  renderers.
- Welcome lines (`DOMAIN_WELCOME_LINES`): the `mcp`/`agent`/`eventbus` entries gain
  "rendered from `registry/manifests/<name>.yaml`" wording in this code change (docs
  19-21 only commit the regenerated blocks); `deployment`/`memory` wording unchanged so
  those two blocks stay byte-identical.
- Deterministic output: entries sorted by natural key; `generated_at` is NOT written to
  the committed YAML (schema key optional) — a timestamp would break doc 14's
  `git diff --exit-code registry/manifests/` freshness step. Reproducibility is an AC-4
  test target (doc 18).
- Drift model: `--check` iterates the registered manifest set; a missing committed
  manifest file is itself drift. Then regenerate in memory; compare against the
  committed YAML (manifest vs source) and against the guarded block rendered from the
  committed YAML (block vs manifest). This catches hand-edited blocks and stale
  manifests with one code path.
- Module size (plan Risk mitigation): manifest entry models, YAML load/write, and the
  shared render helpers move to a new private module `tools/_contract_manifests.py`;
  builders stay per-domain functions. `tools/_contract_manifests.py` needs a
  `tools/TOOL_DESCRIPTIONS.md` row (doc 22) because `check_tool_descriptions_sync`
  requires a row for every `tools/*.py` except `__init__.py`.

## Alternatives considered
- Keep generators direct-to-doc and treat manifests as a parallel export: rejected —
  plan AC-4 requires the blocks to be rendered FROM manifests (single source), and
  two-way drift is impossible to express without the manifest as IR.
- Separate new tool `tools/generate_manifests.py`: rejected — plan row names
  `generate_reference_table.py` as the extension point and the guard/doc constants are
  already there.

## Implementation
### Target file
`tools/generate_reference_table.py`

### Procedure
1. Add `MANIFEST_DIR = REPO_ROOT / "registry" / "manifests"` and
   `CONTRACT_MANIFEST_SCHEMA = REPO_ROOT / "schemas" / "contract_manifest.json"` (new
   constants).
2. Add `build_manifest(domain)` (new) dispatching per-domain builders that read the
   live sources named in docs 07-13 and return the envelope dict.
3. Add `write_manifest(domain)` (new): validate with `jsonschema.validate`, serialize
   entries to YAML sorted by natural key, write `registry/manifests/<name>.yaml`.
4. Add `load_manifest(domain)` (new) and rewire `render_updated_doc` (`:342`) to build
   the table from the loaded manifest entries (existing table generators become the
   entry→markdown renderers).
5. Extend `check_drift` (`:357`): for each domain compare in-memory regenerated
   manifest vs committed manifest, then committed manifest vs guarded block; print
   `DRIFT:` lines in the existing format (`:388`).
6. Add `--manifests` flag (new): `--manifests` writes manifests then re-renders docs
   (`--dry-run` respected); `--check` unchanged CLI semantics, now covering both
   directions.

### Method
Incremental: pilot `mcp` and `deployment` manifests first (plan Phase 2), then port the
remaining domains (Phase 3). Existing `--type` behavior stays byte-compatible for
non-manifest domains.

### Details
- YAML serialization: `yaml.safe_dump(sort_keys=True)`; module import `import yaml`
  (new) (PyYAML is already used by tools in this repo).
- Guard markers (`:47-56`) are unchanged. The `DOMAIN_WELCOME_LINES` constants
  (`:325-330`) are edited in this change so regenerated blocks name their manifest;
  docs 19-21 only commit the regenerated output.

## Compatibility considerations
- `--check` output contract (`DRIFT: <path>` lines, exit 1) is consumed by CI
  (`.github/workflows/ci.yml:35`) and must not change format.
- Existing tests `tests/tools/test_generate_reference_table.py` (`TestCheckDrift` at
  `:120`) must stay green — the renderer refactor must produce identical tables.

## Security considerations
Manifests embed config file paths and tool names only; no secrets. Sources are read
from the repo working tree.

## Rollback considerations
Single-commit revert; committed manifests (docs 07-13) revert with it.

## Validation plan
- `uv run pytest tests/tools/test_generate_reference_table.py` (existing + doc 18 cases).
- `uv run python tools/generate_reference_table.py --manifests` then `--check` green on
  the live repo; rerun determinism check (two `--manifests` runs → identical bytes).
- Full `rules/toolchain.md` sequence.

## Completion criteria
For each shipped domain: manifest validates against the schema, the guarded doc block
equals the render of the manifest, and `--check` fails when either side drifts
(direction-specific fixture cases in doc 18).

## Out of Scope
CI/pre-commit wiring, individual manifest source semantics, deferred REQ-007 manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement manifest builders/validation/write path | Completed | 20261031-093000 | 20261031-105251 | All 10 builders implemented. Deviation note: the mcp guarded table renders from `mcp_endpoints` (server-centric layout); `tool_ownership` belongs to the domain and is drift-checked but is not the render source |
| 2 | Rewire renderer + two-way check_drift | Completed | 20261031-093000 | 20261031-105251 | Migration gate (AC-4) verified: deployment and memory blocks byte-identical; mcp/agent/eventbus blocks differ only in the welcome line |
| 3 | Add or update tests per Validation plan | Completed | 20261031-093000 | 20261031-105251 | Doc 18 co-authored in the same change |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261031-093000 | 20261031-105251 |  |
| 5 | Port remaining domains to manifests | Completed | 20261031-093000 | 20261031-105251 | Phase 3 |

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
- **Requirement ID**: `REQ-005` (manifest mode, from-manifest rendering, two-way drift check)
- **Source issue**: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_adrcov001_contract-manifests-invariant-coverage.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-112317
- **Related target files**: `tools/generate_reference_table.py`