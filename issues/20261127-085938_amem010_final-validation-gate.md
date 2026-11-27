# Run the final validation and release gate for the Memory and retention rework

## Priority
Medium

## Summary
Update ADR invariant evidence and run the complete repository validation gate after implementation and documentation synchronization.

## Background
Source: bundle item M-03. Verified against master on 2026-11-27:
- `Explicit in code`: the validation sequence and gate entry point are documented in `rules/toolchain.md` (`tools/run_validation_gates.py`, `tools/generate_reference_table.py --check`, `.github/run_cited_adr_tests.py`).
- `Documentation only`: ADR-006 INV-19 to INV-22 are recorded as not verified (see `issues/20261125-103310_adrr004_eventbus-retention-replay.md`); ADR-008 invariants for Repository Context, Episodic Memory, and JSONL absence are covered by `issues/20261125-103316_adrr010_agent-memory-schema.md`.

## Problem
The work is incomplete until ADR bodies, ADR Index evidence, Known Issues, generated references, configuration manifests, source, and tests agree.

## Reason for Change
This is a merge and release gate, not optional cleanup; it follows issues/20261127-085937_amem009_docs-manifests-sync.md.

## Implementation Intent
Use real test evidence, keep accurate Manual, Partial, and Not Verified classifications, and attach reproducible results to the pull request.

## Target Files or Areas
- `docs/10_adr/` (ADR-006, ADR-008, the ADR index), `registry/manifests/invariant_coverage.yaml`
- CI workflows and the checkers listed in `rules/tool-gates.md`

## Required Changes
- Update ADR-006 retention evidence and ADR-008 Repository Context, Episodic Memory, JSONL-absence, retention, and capacity evidence; cite only real, non-skipped, non-xfailed tests; keep incomplete evidence as Manual, Partial, or Not Verified.
- Run the ADR structure, authority, reference, preservation, and invariant-matrix checks; Known Deviation and Issue Inventory synchronization; canonical-source and generated-reference checks; internal-link validation and Markdown lint; configuration ownership and key consistency; Ruff, Mypy, targeted tests, and the full test suite.
- Record commands and results in the pull request and document approved preservation mappings for intentional ADR amendments.

## Constraints
- Do not mark incomplete evidence as Confirmed; do not cite nonexistent or skipped tests.
- Do not remove Known Issues before implementation and verification evidence exists.
- Treat this issue as a required merge gate.

## Acceptance Criteria
- No blocking invariant cites invalid evidence and ADR body and index evidence agree.
- All mandatory repository checks pass and results are attached to the pull request.
- The release is not approved while a mandatory check fails.

## Testing Expectations
Run `uv run python tools/run_validation_gates.py --full`, `uv run python tools/generate_reference_table.py --check`, `uv run python .github/run_cited_adr_tests.py`, and the checks in `rules/toolchain.md`.

## Documentation Impact
ADR bodies and index evidence rows; Known Issues; preservation mappings for ADR amendments.

## Out of Scope
- Fixing implementation defects found by the gate beyond recording them (file a new issue instead) and Approval Ledger hardening (issues/20261127-085939_amem011_approval-ledger-checks.md).

## Dependencies
- Depends on issues/20261127-085937_amem009_docs-manifests-sync.md.
- Blocks issues/20261127-085939_amem011_approval-ledger-checks.md.

## Unresolved Questions
- `不明`: the target branch and pull request in which the evidence is attached (this repository's branch policy is to commit on master).

## AI Implementation Instruction
Report each failing check and stop; do not weaken a check or mark evidence Confirmed to pass the gate.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085938
- **Related target files**: `docs/10_adr/`, `registry/manifests/invariant_coverage.yaml`
