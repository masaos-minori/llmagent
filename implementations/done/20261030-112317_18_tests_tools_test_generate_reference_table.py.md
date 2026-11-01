# Implementation Procedure: test_generate_reference_table.py manifest cases

## Goal

Extend the generator's test module with manifest reproducibility and two-way drift
fixtures (REQ-005; test-side of docs 05-13).

## Scope

**In scope:**
- New cases in `tests/tools/test_generate_reference_table.py`: schema validation of
  generated manifests, byte-deterministic regeneration (two runs, byte-identical — the
  generator writes no `generated_at`, doc 05/06), manifest-vs-source drift, missing-
  manifest drift, and block-vs-manifest drift.
- Reuse the existing synthetic-repo fixture style of `TestCheckDrift`
  (`tests/tools/test_generate_reference_table.py:120`).

**Out of scope:**
- Generator code (doc 05), schema file (doc 06).

## Assumptions
- Existing module must stay green unchanged (characterization lock on current table
  output).
- Manifest tests point the generator at tmp synthetic sources (small agent.toml, fake
  server dirs) rather than the live repo — matches the module's existing tmp-fixture
  pattern.

## Design decisions
- Drift tests mutate each side independently (source-only change vs doc-block-only
  change) and assert the specific `DRIFT:` line direction (doc 05 step 5).

## Alternatives considered
- Live-repo manifest snapshots in tests: rejected — live sources change with unrelated
  commits and would make the suite flaky.

## Implementation
### Target file
`tests/tools/test_generate_reference_table.py`

### Procedure
1. Add `TestManifestGeneration` (new): builds a synthetic repo, runs the manifest
   builder path, asserts schema-valid YAML and determinism.
2. Add drift directions: `test_manifest_stale_vs_source` (new),
   `test_block_stale_vs_manifest` (new) asserting distinct messages.
3. Add `test_unknown_manifest_name_rejected` (new) via the schema (doc 06).

### Method
Pure additions; existing classes untouched.

### Details
- Determinism: raw byte-compare of two `--manifests` runs (no `generated_at` is written;
  `git diff --exit-code registry/manifests/` in CI relies on this).

## Compatibility considerations
CI step `generate_reference_table.py --check` (`.github/workflows/ci.yml:35`) output
contract must remain unchanged — covered by existing `TestCheckDrift` staying green.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_generate_reference_table.py` (new cases red until
  doc 05); full `rules/toolchain.md`.

## Completion criteria
Both drift directions, determinism, and schema rejection each have a green case after
doc 05 lands; all pre-existing cases still pass.

## Out of Scope
Generator code, manifest contents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 20261031-093000 | 20261031-105251 | Deviation note: the 2 synthetic-repo `TestCheckDrift` cases needed fixture extension (synthetic deployment sources + committed manifest) because `check_drift` is now manifest-coupled; their DRIFT-string assertions are unchanged. 6 new cases added |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261031-093000 | 20261031-105251 |  |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_adrcov001_contract-manifests-invariant-coverage.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-112317
- **Related target files**: `tests/tools/test_generate_reference_table.py`