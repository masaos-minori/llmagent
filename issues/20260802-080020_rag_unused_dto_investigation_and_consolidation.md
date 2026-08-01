# Investigate and consolidate unused-DTO status (docs/03_rag_04_01, 04_03, 04_04, 04_05) into Known Issues

## Priority
Medium

## Summary
Several DTOs/dataclasses across the RAG domain are confirmed (via grep) to have no references outside their own definition: `RegisteredDocument` (`04_01`), `AuditLogRecord`/`ApprovalDecision` (`04_03`), various config dataclasses (`04_04`) — including whether `models_config.py`'s ingestion-config dataclasses have any planned future role in TOML schema validation (currently, `ConfigLoader` returns raw dicts that bypass them entirely) — and `PipelineRunResult.result_source` (`04_05`, tracked more specifically in a separate dual-definition issue).

## Reason for Change
Being unused is confirmable by grep, but whether each is a forward-looking placeholder (safe to keep) or dead code left over from a removed feature (safe to delete) cannot be determined from code alone — this needs the design owner's input, and scattering the question across 4 separate files makes it hard to track and resolve.

## Implementation Intent
Consult the implementation/design owner for each unused DTO's status (future-planned vs. leftover), and consolidate the findings into a single Needs Confirmation / Known Issues entry rather than leaving the question scattered across 4 files.

## Target Files or Areas
`docs/03_rag_04_01_dto-models_data.md`, `docs/03_rag_04_03_dto-models_audit.md` (or equivalent), `docs/03_rag_04_04_dto-models_config.md` (or equivalent), `docs/03_rag_04_05_dto-models-pipeline-run-result.md` (or equivalent); consolidated into `docs/03_rag_90_inconsistencies_and_known_issues.md`

## Required Changes
- Confirm with the design/implementation owner whether `RegisteredDocument`, `AuditLogRecord`/`ApprovalDecision`, the `04_04` config dataclasses (including whether `models_config.py`'s ingestion-config dataclasses are planned for future TOML schema validation), and `PipelineRunResult.result_source` are each intentional forward-looking placeholders or removable dead code.
- Add a single consolidated entry (or one entry per DTO, cross-referenced) to `docs/03_rag_90_inconsistencies_and_known_issues.md` recording each DTO's confirmed status.
- Remove the scattered individual mentions of "possibly unused" from the 4 source files, replacing them with a reference to the consolidated `03_rag_90` entry.

## Acceptance Criteria
Each unused DTO's status (planned vs. dead code) is confirmed and recorded in a single consolidated location in `docs/03_rag_90`; the 4 source files reference that consolidated entry instead of repeating the open question individually.

## Testing Expectations
Not required (documentation-only); the investigation is a combination of grep confirmation (already done by this review) and a design-owner consultation.

## Documentation Impact
4 DTO documentation files updated to reference the consolidated entry; `docs/03_rag_90` gains new entries (coordinate with the broader Known-Issues-population issue).

## Out of Scope
Do not delete any of these DTOs in this issue, even if confirmed unused — that would be a separate implementation issue following this confirmation.

## AI Implementation Instruction
This requires a human design-owner decision for each DTO — if unconfirmable through available context, register each as an explicit open Needs Confirmation item in `docs/03_rag_90` rather than guessing at intent.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §6B (未使用の疑いがあるDTO群, ingestion設定dataclass(models_config.py)の将来的な検証計画)
- Generated at: 2026-08-02
