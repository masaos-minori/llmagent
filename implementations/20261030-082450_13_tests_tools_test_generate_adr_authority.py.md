## Goal
Create `tests/tools/test_generate_adr_authority.py` (new): generator reproducibility tests — regeneration byte-equals committed index sections and `--check` exits nonzero on drift (REQ-003 tests, AC-4).

## Scope
- In scope: this test module.
- Out of scope: validator tests (row 12), generator implementation (row 03).

## Current shape (facts)
- Precedent: `tools/generate_reference_table.py --check` is CI-tested for drift detection (marker constants at `:48-55`); its test precedent lives under `tests/` (locate the existing `generate_reference_table` test at implementation — absence in `tests/tools/` listing means the precedent may be under another tests subtree; adapt from whatever precedent exists).
- Marker contract constants belong to row 03 (`<!-- AUTO-GENERATED: generate_adr_authority.py <section> -->` / `<!-- END AUTO-GENERATED -->`); this module pins them.

## Assumptions
- Sandbox-first design: the core reproducibility tests run against a tmp sandbox copy of `adr_01_index.md` + fixture model (deterministic, no live-docs writes). One integration test runs `--check` against the live `docs/10_adr/adr_01_index.md` + live `config/adr_authority.toml` and asserts exit 0 — this test is the committed-state lock and only passes after rows 02/03/06 land (test-first contract: red until then).
- "Byte-equals committed" is implemented as: render sections to strings from the fixture model; compare against the guarded blocks extracted from a sandbox index that contains them verbatim (fixture built by running the generator once into the sandbox, then tampering).

## Design decisions
- Tests: (1) double-generation idempotence (render twice → identical bytes); (2) tamper inside guard → `--check` exit 1 with a finding naming the section; (3) missing guard → exit 1 (mirrors `generate_reference_table.py` semantics "block missing or differs"); (4) hand-written regions outside guards byte-unchanged after a write-mode run; (5) live integration clean check (Assumptions).
- Fixture model is a trimmed copy of the real model semantics (not the real file) for 1–4; deterministic regardless of model edits.

## Alternatives considered
- Snapshot-file comparisons (golden files in `tests/fixtures/`) — rejected: golden copies of governance content drift with every legitimate model edit; comparing generator output against generator-produced sandbox state tests reproducibility itself, the actual AC-4 claim.

## Implementation
### Target file
- `tests/tools/test_generate_adr_authority.py` (new)

### Procedure
1. Read `tools/generate_reference_table.py`'s existing test coverage (search `tests/` for its name) and mirror its idioms.
2. Author tests 1–5; sandbox construction via tmp_path fixtures.
3. Run after rows 02/03/06 land; keep green.

### Method
New pytest module; stdlib only; no writes outside tmp_path except the single read-only live-integration test.

### Details
- The live integration test is the CI-visible proof of AC-4; row 11's CI `--check` step duplicates it at workflow level — both kept (unit lock + pipeline gate).

## Compatibility considerations
- None beyond marker-constant coupling with row 03 (documented in Current shape).

## Security considerations
- None.

## Rollback considerations
- Reverts with rows 03/06.

## Validation plan
- `uv run pytest tests/tools/test_generate_adr_authority.py` green post-landing; tamper fixtures must fail (mutation spot-check).

## Completion criteria
- Five tests present and green; byte-reproducibility and drift detection proven.

## Out of Scope
- Validator behavior (row 12), CI wiring (row 11).

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
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 13, REQ-003 (AC-4; Tests section bullet 2).
