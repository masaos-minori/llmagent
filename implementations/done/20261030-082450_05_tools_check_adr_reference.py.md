## Goal
Extend `tools/check_adr_reference.py` to cross-check ADR front matter `related` edges against `config/adr_authority.toml`, detecting unknown edge targets and model/front-matter divergence (REQ-005, AC-5).

## Scope
- In scope: additive extension of the existing tool importing the shared core from row 04.
- Out of scope: the core module itself (row 04), the model (row 02), CI wiring (row 11), tests (row 12).

## Current shape (facts)
- `tools/check_adr_reference.py` today: verifies that `scripts/<path>.py` files cited in the ADR Invariant Verification Matrix carry `# ADR-NNN` comment markers; matrix parsed by header names; fails when the matrix yields no source references; `--format json` supported (docstring verified at `:1-31`).
- ADR front matter `related` lists repository-relative `.md` paths (e.g. `adr_02_05_008_db-sqlite-4db-separation.md` in `docs/10_adr/adr_01_index.md` front matter); field contract in `tools/_front_matter_schema.py` (`title`, `area`, `tags`, `related`, `status`).
- ADR List rows name the file path per ADR ID; the model's `adr_edge` rows key on ADR IDs — the mapping from file to ID uses the filename pattern `adr_<group>_<NN>_<slug>.md` already relied on by `check_adr_structure.py`/`check_adr_preservation` tooling.

### Verified 20261030 (adversarial pass)
- Confirmed all three facts above (docstring scope `:1-31`, example `adr_02_05_008_db-sqlite-4db-separation.md` in the index front matter, filename-ID pattern in `check_adr_structure.py` `_ADR_FILE_RE` `:174`).
- Corrected CI claim: `check_adr_reference.py` is not a direct ci.yml step; it runs as pre-commit hook `adr-reference-scoped` (`.pre-commit-config.yaml:60-62`, entry `python -m tools.check_adr_reference`) and reaches CI through the `Pre-commit` step (`ci.yml:40-41`). The new cross-check section must not break hook invocation.
- Confirmed today's front matter is a 31-edge subset of the 33-edge fence (`ADR-003 → ADR-004`, `ADR-012 → ADR-007` front-matter-absent); with the finalized divergence rule (Assumptions) and row 02 seeding the fence set, the extension passes against the live ADR set with zero findings — no ADR front-matter edits are needed.

## Assumptions
- Extension is additive: the matrix-marker check stays exactly as-is; a second check section runs the core's front-matter cross-check over every `docs/10_adr/adr_02_*.md` file and reports `FRONTMATTER_DIVERGENCE` findings through the same reporter/exit machinery.
- Divergence rules (both directions, per AC-5 — finalized 20261030, see Verified): a front-matter `related` entry naming an ADR file with no corresponding model `adr_edge` (any edge type) is a finding; a model `adr_edge` of a non-`Reference` type whose `from` ADR lists no matching `related` entry is a finding; a model-only `Reference` edge is clean (it seeds the generated graph beyond today's front matter without demanding front-matter edits). Non-ADR `related` entries (governance docs, reference docs like `mcp_01_tool_ownership_matrix.md`) are out of scope for this cross-check: only edges between two ADR files are model-governed. `adr_01_index.md` and `adr_00_document-guide.md` front matter are excluded entirely (navigation lists, not ADR decision records).
- Resolved (was Needs confirmation): typed/normative edges must appear in front matter `related` — verified 20261030 that all six proposed typed directions (row 02 Verified note) already exist in today's front matter lists, so no ADR file needs front-matter edits and `Exception-to` follows the same rule.

## Design decisions
- Import the cross-check function from `tools/_adr_authority_core.py`; do not reimplement model parsing here (single drift-detection logic, Plan Design).
- Keep CLI surface unchanged (no new flags needed; `--format json` already reports findings generically).
- File→ADR-ID mapping lives in the core (row 04) since both tools and the generator need it; this row consumes it.

## Alternatives considered
- A separate new tool `check_adr_frontmatter.py` — rejected: REQ-005 names the extension of `check_adr_reference.py`; a third ADR tool would inflate the auto-check inventory (rows 08–10) for no gain.
- Making the core import the reference tool instead — rejected: dependency direction must keep the core dependency-free of CLI tools.

## Implementation
### Target file
- `tools/check_adr_reference.py` (modify)

### Procedure
1. Import the core module; add a `check_frontmatter_vs_model(...)` section invoked after the existing matrix-marker scan, merging findings into the same exit-code logic.
2. Preserve existing docstring sections and add one paragraph describing the new model cross-check with its GV number (row 08 registers it).
3. Do not alter the matrix parsing, tokenizer logic, or existing finding text.

### Method
Land after row 04 (core must exist). Regression: the existing behavior stays locked by `tests/tools/test_check_adr_reference.py` (existing tests, untouched) and must pass unmodified.

### Details
- Test coverage for the new section lives in row 12 (`test_adr_authority.py`), per the plan's test row layout; row 05 adds no test file.

## Compatibility considerations
- CI already runs this tool (`.github/workflows/ci.yml` runs `check_adr_reference.py`; verify exact step placement during implementation — the plan's Tests section lists it). The extension must pass against today's front matter before new ADRs land, or row 02's model edges must be authored to match today's `related` lists exactly.

## Security considerations
- Read-only.

## Rollback considerations
- Removing the extension reverts to marker-only checking; core module stays for the other two consumers.

## Validation plan
- `uv run pytest tests/tools/test_check_adr_reference.py` unmodified passes (existing behavior).
- `uv run pytest tests/tools/test_adr_authority.py` (row 12) covers: front-matter edge missing from model → finding; model edge missing from front matter → finding; conforming pair → clean.
- `uv run python tools/check_adr_reference.py` clean against the final docs set.

## Completion criteria
- Bidirectional divergence detection active; existing behavior regression-free.

## Out of Scope
- Model authoring, index generation, guide/docs updates.

## Execution Status

### Execution Status
| Status | Started | Completed | Notes |
|---|---|---|---|
| Completed | 20261030-193223 | 20261030-193223 | Adversarial verification complete 20261030: divergence rule finalized (typed⊆front-matter, front-matter⊆model, model-only Reference allowed); index/guide front matter excluded; hook execution context corrected. |

### Blocker Log
| Date | Blocker | Impact | Resolution |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Type | Status | Notes |
|---|---|---|---|
| — | — | — | — |

## Traceability
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 05, REQ-005 (AC-5).