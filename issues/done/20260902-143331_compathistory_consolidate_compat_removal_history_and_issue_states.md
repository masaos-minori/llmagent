# Consolidate compatibility-removal history and issue-state updates

## Priority
Medium

## Summary
Current specifications must stop describing removed compatibility paths (the legacy RAG
reader, the ETag Null Fill Mode, the removed `ToolRouteResolver.server_configs` argument) as
active behavior, while still preserving why each path was removed and what replaced it.
Confirmed documentation mismatches and separate unresolved design questions also risk being
duplicated across area-specific Known Issues / Needs Confirmation inventories.

## Background
This issue depends on `ragcontract`, `ragfreshness`, and `toolroutedoc` (filed alongside this
issue) landing first, since it consolidates the migration-history and issue-state bookkeeping
those three produce, rather than restating their content.

## Problem
Current behavior, migration history, Known Issues, and Needs Confirmation serve different
purposes. Mixing them causes obsolete behavior to remain visible as an active option, resolved
work to remain open, and unresolved design choices to be documented as facts.

## Reason for Change
A single coordinated update is more reliable than changing migration history and issue
inventories separately, because both depend on the same final classification of each
compatibility path.

## Implementation Intent
Separate the records: current specifications contain only active behavior; Migration History
or Change History records removed paths and their replacements; Known Issues track confirmed
documentation mismatches until correction; Needs Confirmation tracks unresolved design
decisions only; resolved and duplicate entries are archived or consolidated.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md`
- `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`
- `docs/03_rag_02_08_ingestion_pipeline-shared.md`
- `docs/03_rag_90_inconsistencies_and_known_issues.md`
- `docs/04_mcp_03_01_dispatch-and-routing.md`
- `docs/04_mcp_90_inconsistencies_and_known_issues.md`
- `docs/05_agent_13_reference-api.md`
- `docs/05_agent_90_inconsistencies_and_known_issues.md`
- `docs/90_shared_90_inconsistencies_and_known_issues.md`
- `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`

## Required Changes
- Select one canonical history location for each removed compatibility path; record why each was removed and its replacement path (`read_json_file()` → `read_crawl_json()`/`read_chunk_json()`; ETag Null Fill Mode removal; `fetched_at` requirement migration completion; `ToolRouteResolver.server_configs` removal).
- Mark historical entries so they cannot be interpreted as active behavior; record the removal date or target release for each path; link every removed path to its replacement, related ADR, and related issue.
- Remove duplicate migration-history descriptions from non-canonical documents.
- Register or update the Known Issue for each of: obsolete `read_json_file()` documentation, inconsistent `fetched_at` documentation, the Null Fill Mode description, and the obsolete `ToolRouteResolver.server_configs` description.
- Correct any issue that misclassifies static `ToolRegistry` as an obsolete routing layer.
- Register artifact-versioning and unresolved `artifact_type`/`created_by`/`source_file`/`chunk_type` contract questions as Needs Confirmation only if they remain unresolved after the above issues land.
- Mark completed mismatch entries `fixed`; move resolved entries to the archived section; consolidate duplicate cross-area entries under one canonical issue.

## Constraints
Documentation and governance only. Do not change source code as part of this issue.

## Acceptance Criteria
- Current specifications contain only active behavior.
- Removal reasons and replacement paths remain traceable from a single canonical source per path.
- Confirmed mismatches are tracked as Known Issues; unresolved design decisions are tracked as Needs Confirmation.
- Resolved entries no longer appear in active inventories.
- The same underlying issue is not maintained independently in multiple areas.

## Testing Expectations
Not required — documentation and governance only. Verify with
`uv run python tools/check_needs_confirmation_inventory.py` and
`uv run python tools/check_known_deviation_sync.py`.

## Documentation Impact
Yes — this issue's entire scope is governance/Known-Issues bookkeeping across the files listed
above, consolidating the migration-history and issue-state consequences of `ragcontract`,
`ragfreshness`, and `toolroutedoc`.

## Out of Scope
- Source-code changes.
- Resolving artifact-versioning design decisions.
- Changing the common Known Issue schema.
- Publishing release notes outside the repository.

## Dependencies
Depends on `ragcontract` (RAG artifact contract), `ragfreshness` (fetched_at/ETag freshness),
and `toolroutedoc` (tool-routing documentation) landing first, since this issue consolidates
their resulting Known Issue and migration-history entries rather than re-deriving them.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Do not begin this issue until `ragcontract`, `ragfreshness`, and `toolroutedoc` have landed —
their final documentation state determines which Known Issue entries to register or close.
Consolidate by reference (link to the canonical source), not by duplicating content across
area-specific documents.
