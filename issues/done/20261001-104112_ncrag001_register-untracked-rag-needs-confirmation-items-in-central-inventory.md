# Register untracked RAG Needs Confirmation items in the central inventory

## Priority
Medium

## Summary
Two inline Needs Confirmation markers under `docs/21_rag/` denote real unresolved design questions but have no entry in the central Needs Confirmation Inventory (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`, Part 2). Register each as an Active Item with all required fields so that the Inventory reflects the actual open uncertainty and `tools/check_needs_confirmation_inventory.py` no longer reports them as untracked.

## Background
- The Inventory is the single centralized place for Needs Confirmation items; its `### Active Items` currently states that no active items remain open. `Explicit in code` (document content)
- Inventory entries require fifteen fields: ID, Source File, Section, Line Number, Question, Evidence, Impact, Required Action, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking.
- The Inventory's Extraction Process states that source documents are not modified during extraction.
- `chunking_strategy` question history: `issues/done/20260913-183004_chunking_strategy_enforcement_needs_confirmation.md` asked for an inventory entry; `plans/done/20260913-203130_plan.md` instead recorded it in the RAG Constraints Reference table and left it as "the tracked Needs Confirmation item". No Inventory entry was ever added (`git log -S` on `docs/00_governance/` finds no change mentioning `chunking_strategy`). `Explicit in code`
- `_is_stale_update()` question history: open issue `issues/20260930-135010_etagexc01_etagmanager-_is_stale_update-exception-type-distinction-unresolved.md` tracks the design decision itself, but no Inventory entry exists.

## Problem
`uv run python tools/check_needs_confirmation_inventory.py` (2026-10-01) reports these two RAG markers as untracked:
- `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` — ETagManager staleness check: both timestamp-validation failures raise the same `ValueError`; open question is whether distinct exception types are intended.
- `docs/21_rag/rag_05_5-constraints-reference.md` — Constraints table row for `chunking_strategy`: any non-empty string is accepted; open question is whether a closed value set is intended.

Both markers express genuine unresolved design intent (not definitional uses of the label). `Documentation only`

## Reason for Change
- The Inventory understates open uncertainty, contradicting the governance rule that unresolved items must be registered centrally.
- Unregistered questions risk being treated as settled design.

## Implementation Intent
- Add one Active Item per marker to Part 2 `### Active Items`, filling all fifteen fields from the source document context and existing issues/plans.
- Use the existing issue `etagexc01` as Related/Resolution Target for the ETagManager item rather than creating a duplicate decision issue.
- For `chunking_strategy`, record the prior history (issue and plan) as Evidence; if a resolution vehicle is needed, reference or file a dedicated follow-up issue.
- Replace the "No other active Needs Confirmation items remain open." sentence so it is consistent with the new entries.
- Do not change the RAG source documents or RAG code.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 2 `### Active Items`)

## Required Changes
- Add an Active Item for the ETagManager exception-type question (source `rag_02_06_ingestion_pipeline-supporting-components.md`).
- Add an Active Item for the `chunking_strategy` closed-value-set question (source `rag_05_5-constraints-reference.md`).
- Assign sequential IDs consistent with the Inventory's existing ID scheme (confirm the scheme from document history before choosing).
- Set Status, Priority, and Blocking with a stated rationale.
- Update the Active Items lead sentence accordingly.

## Constraints
- Do not modify `docs/21_rag/*.md` (Extraction Process: never modify source documents).
- Do not decide the underlying design questions in this issue.
- `docs/` text must follow `skills/DESIGN.md` Shared Vocabulary (English, no source-code line numbers, no concrete config values). The Inventory's own `Line Number` field refers to the doc line and is required by the Inventory schema.
- `governance_03` must keep passing `check_issue_inventory_conformance.py`.

## Acceptance Criteria
- Part 2 `### Active Items` contains exactly one entry for each of the two markers, each with all fifteen fields populated.
- `uv run python tools/check_needs_confirmation_inventory.py` no longer reports the two RAG markers as untracked.
- The ETagManager entry references `etagexc01`; no duplicate decision issue is created.
- `docs/21_rag/` files are unchanged.

## Testing Expectations
Documentation-only. Run and record:
- `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_issue_inventory_conformance.py`
- `uv run python tools/check_docs_structure.py "docs/00_governance/*.md"` and `uv run python tools/check_docs_quality.py`

## Documentation Impact
Yes. Needs Confirmation Inventory entries only.

## Out of Scope
- Deciding or implementing distinct exception types for `_is_stale_update()` (issue `etagexc01`).
- Enforcing a closed value set for `chunking_strategy`.
- The `docs/23_agent/` markers (issue `ncagent001`).
- Changes to `tools/check_needs_confirmation_inventory.py` (issue `ncinv001`).

## Dependencies
- Related: `issues/20260930-135010_etagexc01_etagmanager-_is_stale_update-exception-type-distinction-unresolved.md`.
- Related: `canon001` may also add entries to `governance_03` Part 2; coordinate to avoid ID collisions.

## Unresolved Questions
- The Inventory's ID scheme (for example `NC-0NN`) and next free number must be confirmed from history, since the list is currently empty.
- Owner (`Assigned To`) for each item is not stated anywhere in the repository.
- Whether the `chunking_strategy` question needs its own resolution issue.

## AI Implementation Instruction
- Edit only Part 2 of `governance_03`; do not touch source docs or code.
- Populate every field from cited repository evidence; write `Unknown` with a reason rather than inventing an owner or date.
- Run the listed checkers and report their actual output.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-104112
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
