## Goal
Create `tools/generate_adr_authority.py` (new): a generator that emits the ADR index graph sections (Reference Graph, Authority Graph, Intentional Circular References) from `config/adr_authority.toml` with generated-content markers and a `--check` mode (REQ-003 byte-reproducible index sections).

## Scope
- In scope: the generator module and its CLI.
- Out of scope: the model (row 02), the index edit landing the blocks (row 06), the validator (row 04), the guide prose (row 07).

## Current shape (facts)
- `docs/10_adr/adr_01_index.md` "ADR Dependency Graph" (`:62`) is a hand-written `text` fence of `ADR-A → B` lines plus an "Intentional Circular References" prose section (`:83`) listing six bidirectional pairs with explanations.
- `tools/generate_reference_table.py` is the generator idiom: per-section `GUARD_START = "<!-- AUTO-GENERATED: generate_reference_table.py <name> -->"` / `GUARD_END = "<!-- END AUTO-GENERATED -->"` constants, replacement of the guarded block in the target doc, `--check` mode that writes nothing and exits 1 on drift (`:48-55`, CI step at `.github/workflows/ci.yml:35`).

## Assumptions
- The marker discipline is reused verbatim in form: `<!-- AUTO-GENERATED: generate_adr_authority.py adr-reference-graph -->`, `...adr-authority-graph -->`, `...adr-intentional-cycles -->`, each closed by `<!-- END AUTO-GENERATED -->`.
- The generator rewrites only the three guarded regions of `adr_01_index.md`; all hand-written prose outside markers (Purpose, Known Deviations, invariant matrix, keywords, ADR-011 note) is untouched (Plan Design).
- The generator validates minimally (model parses, edge types known) and defers semantic findings to `check_adr_authority.py` (row 04) — but refuses to emit when the model fails the validator core, so a broken model never lands generated content.

## Design decisions
- Single module reading `config/adr_authority.toml` via `tomllib`, importing the model loader/core from the shared core module introduced by row 04 (`tools/_adr_authority_core.py`) so generator and validator parse identically.
- Output shapes: Reference Graph keeps today's `ADR-A → B` fenced text (grouped per source ADR, sorted); Authority Graph emits typed lines `ADR-A --Requires--> ADR-B` for non-`Reference` edges plus the primary-authority table rows `target | primary | supplemental limits`; Intentional Cycles reproduces the six pair bullets from model `intentional = true` edges plus their recorded `notes` strings.
- `--check` (no writes) vs default (write) mode, exit codes 0/1 mirroring `generate_reference_table.py`; `--format json` finding output optional flag parity for CI friendliness.
- Cycle prose ("Each pair splits ownership...") stays hand-written below the generated bullet list; the generator emits only the bullets.

## Alternatives considered
- Generating the entire index from the model — rejected: only graph sections are derived; the ADR List, invariant matrix, and keywords remain hand-maintained (REQ-003 scope).
- Extending `generate_reference_table.py` with a new type — rejected: that tool's input is live code, this one's input is a governance model; mixing them couples unrelated regeneration contracts (Plan: extend idioms, not parallel-maintain inside one tool).

## Implementation
### Target file
- `tools/generate_adr_authority.py` (new)

### Procedure
1. Implement model loading via `tools/_adr_authority_core.py` (row 04 lands first in `seq`; this import is the plan's "one module both tools import").
2. Implement the three section renderers and guarded-block replacement with the exact marker constants.
3. Implement `--check` byte comparison and exit semantics; `--help` documents usage like `python tools/generate_adr_authority.py [--check] [--format json]`.
4. Keep the module in the `tools/` conventions: shebang, docstring naming plan/ADR-016, `if __name__ == "__main__"`.

### Method
New standalone tool; land after row 04 (shared core) and before row 06 (which invokes it to produce the committed blocks). Tested by row 13.

### Details
- Marker text is contract with row 06 (the committed index must carry the same constants) and row 13 (tests pin them).

## Compatibility considerations
- CI wiring is row 11; do not edit `ci.yml` here.
- `tools/TOOL_DESCRIPTIONS.md` and `routing.md` registration is rows 09–10; the auto-check inventory checker (row 08's validation) must see all three in the same landing.

## Security considerations
- Writes one docs file in default mode; `--check` is read-only (same discipline as the precedent generator).

## Rollback considerations
- If the tool is removed, row 06's guarded blocks revert to hand-maintained text and row 11's CI step is removed; all in one revert.

## Validation plan
- `uv run python tools/generate_adr_authority.py --check` exits 0 against the committed index (row 06's output).
- Deliberate index drift → `--check` exits 1 (row 13 regression test).
- `uv run pytest tests/tools/test_generate_adr_authority.py` passes.

## Completion criteria
- Three sections reproduce byte-identically from the model; `--check` detects tamper; no hand-written section is ever rewritten.

## Out of Scope
- Model semantics validation (row 04), CI registration (row 11), docs prose (rows 06–08).

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
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 03, REQ-003 (AC-4).
