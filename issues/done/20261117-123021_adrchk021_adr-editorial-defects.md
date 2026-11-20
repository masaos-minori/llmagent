# Fix editorial defects in ADR-012, ADR-014, ADR-015, and ADR-017

## Priority
Medium

## Summary
ADR-012, ADR-014, ADR-015, and ADR-017 have wording, coverage, or reference errors. Each is local to one ADR and needs no cross-ADR decision.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M09`; merged from ADRCHK-M35, M36, L03, L09, L11 (review findings M7, M19 and round 1 Low findings)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- ADR-012: INV-09 says the pipeline enforces stages 1 to 7 in order, but the first stages run before the pipeline is built; the protected-branch check for `git_add` and `git_commit` has no INV and no test; the cited test ID `test_git_service_dispatch.py::test_rejected_remote_forms` lacks the class name `TestWriteRefAllowlist`, so `.github/run_cited_adr_tests.py` may fail to resolve it.
- ADR-014: `tasks.status` allows `halted` but the stage transitions do not include it, and complete and completed are both used.
- ADR-015: the scope covers all guard-commented documents, but INV-01 and its verification cover only `generate_reference_table.py`; the Index guard is produced by `generate_adr_authority.py`.
- ADR-017: the checklist is shorter than the governed template.

## Implementation Intent
- Each ADR's invariants, tests, states, and checklist match its own Decision and the code.

## Target Files or Areas
- `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
- `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
- `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`
- `docs/10_adr/adr_02_03_017_mcp-authentication.md`

## Required Changes
- ADR-012: reword INV-09; add an INV and a test reference for the protected-branch check, or state why it is out of scope; fix the test ID.
- ADR-014: add `halted`, and use one term for the completed state, taken from the CHECK constraints in `scripts/db/schema_sql.py`.
- ADR-015: extend INV-01 to every generator that writes guard blocks, or narrow the scope.
- ADR-017: complete the checklist from the governed template.

## Constraints
- A new INV in ADR-012 or an INV-01 scope change in ADR-015 is a decision change; mark it as a pending amendment.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- `uv run python .github/run_cited_adr_tests.py` resolves every node ID cited in ADR-012.
- `uv run python tools/check_adr_structure.py` passes for all four ADRs.

## Testing Expectations
Documentation-only. Run `tools/check_adr_structure.py`, `.github/run_cited_adr_tests.py`, and the docs checkers. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The four ADRs.

## Out of Scope
- Cross-ADR decisions.
- Changing the Git write pipeline.

## Dependencies
- `issues/20261117-123001_adrchk001_mcp-auth-contract.md` also edits ADR-017; `issues/20261117-123022_adrchk022_history-comment-removal.md` also edits ADR-017 history text; fix the order with the owner.
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines the pending-amendment form.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- Mark a new INV or scope change as a pending amendment; do not write approval text.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123021
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`; `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`; `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`; `docs/10_adr/adr_02_03_017_mcp-authentication.md`
