## Goal
- Remove or rewrite the module docstrings and comments in `scripts/` and `config/` that describe where code came from or which plan created it ("Extracted from", "Refactored:", `RAGCORPUS001`, `EBAUTHGEN001`, `crawl003`, and `REQ-<number>` identifiers), so comments describe only current responsibility and behavior. This is a comment-only sweep done last, after the other compatibility-removal Plans.

## Priority
Low

## Scope
- **In-Scope**: the 136 files under `scripts/` and `config/` that match the patterns today (listed in `Implementation Target Files`), swept in phases by directory (`scripts/agent/`, `scripts/mcp_servers/`, `scripts/eventbus/`, `scripts/rag/`, then `scripts/shared/`, `scripts/db/`, and `config/`); the regeneration of two generated reference files that quote one rewritten docstring; one SQL comment inside the canonical DDL.
- **Out-of-Scope**: `tests/` and `docs/` (except the generated reference block named above); any code, logic, or test behavior change; the compatibility-pattern checker (rmcompat008); history wording in documents (adrrev017); identifiers a checker requires (the `# ADR-NNN` markers verified by `tools/check_adr_reference.py`); `scripts/rag/corpus_identity.py` and `scripts/rag/identity_gate.py` (deleted by rmcompat003).
- **Dependencies**: Depends on every other Plan of the rmcompat batch so that their edits land first; also schedule after the open procedures of the adrrev004 Plan (archived in `plans/done/`) and after the adrrev005 Plan (its code steps are `Completed`), which edit many of the same files. Blocks the compatibility-pattern checker Issue (rmcompat008).
  - **Depends on**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md | phase all | its edits to `ingester.py`, `startup_validation.py`, and RAG config files land first
  - **Depends on**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md | phase all | its edits to `diagnostics.py`, `models_result.py`, `pipeline.py`, and `stages/search.py` land first
  - **Depends on**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md | phase all | it deletes `corpus_identity.py` and `identity_gate.py` and edits many RAG, DB, and MCP files
  - **Depends on**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md | phase all | its edits to the EventBus config, auth, audit, admin route, and `eventbus.toml` land first
  - **Depends on**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md | phase all | its edits to the EventBus DLQ, schema, and constants land first
  - **Depends on**: plans/20261112-121532_rmcompat006_rag-ingestion-cleanup.md | phase all | its edits to the ingestion modules land first

## Background
Measured 2026-11-12 (Step 2 and Step 3) by `rg -l "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts config` and a token-level classification of each match (comment, docstring, TOML comment, or inside a string literal): 138 files, 429 matching lines before the two files deleted by rmcompat003 are removed; after excluding those two, 136 files and 423 lines remain. Per pattern (lines): `REQ-<n>` 375, "Extracted from" 44, "Refactored:" 2, `RAGCORPUS001` 8, `EBAUTHGEN001` 5, `crawl003` 1. By directory: 55 files in agent, 24 files in mcp_servers, 22 files in shared, db, config, 19 files in rag, 16 files in eventbus. `user-approved` no longer appears (already removed).

Corrections found against the Issue's claims:
- The comment-only constraint has four exceptions in string literals, none of which is a comment in the Python sense: the two warning messages in `scripts/agent/startup_validation.py` (`REQ-007`, removed by rmcompat001), the pydantic field description in `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` (`RAGCORPUS001`, removed with the field by rmcompat003), and an SQL comment line in `scripts/db/schema_sql.py` (line 223, before a `CREATE TABLE`). The schema fingerprint strips comments before comparing (`_normalize_ddl` in `scripts/shared/schema_fingerprint.py`), so the SQL comment edit is safe; the procedure verifies it with the fingerprint tests.
- A docstring rewrite can change generated documents: `tools/generate_reference_table.py` copies the first docstring line of each public top-level class and function in `scripts/agent/*.py`, `scripts/eventbus/*.py`, and `scripts/agent/memory/*.py` into `registry/manifests/*.yaml` and the guarded blocks of the reference documents. A check of all 136 files found exactly one match on such a line: `AuthzGeneration` in `scripts/eventbus/auth.py` ("Immutable authorization generation snapshot (EBAUTHGEN001)."). The manifest `registry/manifests/eventbus_api.yaml` and `docs/24_eventbus/eventbus_08_reference_api.md` are therefore regenerated (the Issue says not to touch `docs/`; the guarded block is generated, not hand-edited, and `generate_reference_table.py --check` runs in CI).
- Eight matching lines sit on suppression comments (`# noqa`, `# type: ignore`, `# nosec`); each keeps its error code and its justification text (`tools/check_suppression_justification.py`).
- `tools/_docs_consistency_lib.py` mentions two of the patterns; it is a checker for documents, not a source of these comments, and is untouched.
- The counts fall as the six earlier Plans land; the procedure re-runs the searches first and closes any row whose matches are already gone, recording the search.

## Problem
Notes about where code came from, or which plan created it, go stale after later changes, are meaningless without the plan documents, and hide the few comments that point at real compatibility code.

## Reason for Change
Git history and the Issue and Plan documents already keep this information; the current-only policy (`compatrm001`) wants current-behavior comments. Low urgency: nothing is failing, and many of the comments disappear as the other Plans land.

## Implementation Intent
- Comments and docstrings describe only current responsibility and behavior; a non-obvious constraint is rewritten in current tense, not deleted.
- The sweep is done last and by directory, so each directory ends free of matches and files are not edited twice.

## Requirements
- `REQ-001`: `scripts/agent/` has no match for any of the patterns.
- `REQ-002`: `scripts/mcp_servers/` has no match.
- `REQ-003`: `scripts/eventbus/` and `config/eventbus.toml` have no match, and the generated manifest and reference block match the rewritten docstring.
- `REQ-004`: `scripts/rag/` has no match.
- `REQ-005`: `scripts/shared/`, `scripts/db/`, `config/agent.toml`, and `config/mcp_dedup.toml` have no match.
- `REQ-006`: The change is comments and docstrings only (plus the single SQL comment and the two generated files): `git diff` shows no other changed line, suppression justifications keep their error code and text, ADR markers are untouched, and the validation sequence passes unchanged.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/audit_event_emitter.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 6) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/bg_task_monitor.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 7) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/commands/memory_data_ops.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 2 docstring (lines 173,187) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/commands/memory_rebuild_ops.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 2 docstring, 1 comment (lines 52,94,148) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/context.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring, 4 comment (lines 205,254,256,340,386) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/conversation_state_manager.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 7) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/history_selection_policy.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 10) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/http_lifecycle.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/Refactored:: 2 docstring (lines 5,8) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/http_lifecycle_errors.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/http_lifecycle_health_checker.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring (lines 73) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/lifecycle.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 comment (lines 45) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/lifecycle_router.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 8) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/llm_turn_executor.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 1 docstring, 1 comment (lines 7,90) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/llm_turn_runner.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 1 docstring, 1 comment (lines 5,147) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/memory/import_ops.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring, 1 comment (lines 39,82) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/memory/pin_ops.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 2 docstring (lines 42,55) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/memory/write_ops.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring (lines 118) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/orchestrator.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 2 comment (lines 187,188) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/production_config_validator.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 comment (lines 171) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/context_view.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/db_maintenance_service.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/export_formatter.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/mcp_status.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/models.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring (lines 141) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/posture_validator.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 2 docstring (lines 122,192) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/rag_maintenance_service.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | RAGCORPUS001: 1 comment (lines 60) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/session_restore.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 5 docstring, 3 comment (lines 5,46,50,51,117,123...) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/session_title.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/tool_validation.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/undo_service.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 4 docstring, 1 comment (lines 5,8,12,41,97) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/services/workflow_schema.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 1 docstring, 1 comment (lines 5,81) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/session.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 2 docstring (lines 139,240) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/session_message_repo.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 6 docstring, 2 comment (lines 35,181,223,244,274,316...) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/shared/retry_helper.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring (lines 3) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/startup.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/startup_component_init.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 2 docstring, 1 comment (lines 6,87,101) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/startup_mcp_starter.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/startup_prompt_setup.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/startup_reporter.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/startup_validation.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 3 docstring, 3 comment, 2 in a string literal (lines 8,11,79,136,195,250...); the two string-literal lines are removed by rmcompat001 (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/tool_approval.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 comment (lines 52) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/tool_audit.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 2 docstring (lines 217,219) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/tool_loop_guard.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 1 docstring, 2 comment (lines 6,119,120) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/tool_policy.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 8 docstring, 7 comment (lines 48,55,149,163,167,181...) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/tool_preparation.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring (lines 153) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/tool_round_completion.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring, 1 comment (lines 65,114) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/tool_run_recorder.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from: 1 docstring (lines 11) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/tool_runner.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 13 docstring, 4 comment (lines 79,80,81,85,93,154...) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/turn_persistence.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 17 docstring (lines 5,11,13,22,48,103...) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/workflow/idempotency_ops.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring (lines 39) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/workflow/state_store.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 9 docstring, 5 comment (lines 36,231,235,241,245,249...) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/workflow/tool_call_state_ops.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring (lines 5) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/workflow/workflow_engine.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 4 docstring, 5 comment (lines 28,36,101,143,166,175...) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/workflow/workflow_loader.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | REQ-N: 1 docstring (lines 27) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/agent/workflow_engine_adapter.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-001 / AC-1 | Extracted from/REQ-N: 5 docstring, 6 comment (lines 7,65,153,167,174,195...) (checked in Step 2) | `tests/agent` | Verified |
| `scripts/mcp_servers/cicd/cicd_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 3 docstring (lines 73,227,232) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/dispatch.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 4 docstring, 14 comment (lines 70,86,148,163,167,198...) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/file/delete_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 3 docstring (lines 80,305,310) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/file/delete_service.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 1 comment (lines 223) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/file/read_security.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | Extracted from: 1 docstring (lines 6) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/file/read_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 3 docstring (lines 90,373,378) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/file/write_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 3 docstring (lines 79,337,342) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/git/format_output.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 2 docstring (lines 167,169) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/git/git_models.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 1 comment (lines 60) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/git/git_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 3 docstring, 1 comment (lines 77,306,421,426) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/git/git_service.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 1 docstring, 2 comment (lines 157,160,196) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/git/repository_state.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 3 docstring, 1 comment (lines 140,187,305,324) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/git/write_protection_pipeline.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | Extracted from/REQ-N: 1 docstring, 7 comment (lines 9,28,31,168,189,194...) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/github/github_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 3 docstring (lines 86,271,276) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/github/github_service_security.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 1 comment (lines 121) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/github/mapper.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | Extracted from: 1 docstring (lines 5) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/mdq/mdq_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 1 docstring, 1 comment (lines 90,489) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | RAGCORPUS001/REQ-N: 1 docstring, 1 in a string literal (lines 120,261); the string-literal line is removed by rmcompat003 (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 1 docstring (lines 41) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | RAGCORPUS001/REQ-N: 4 docstring (lines 74,122,367,373) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/shell/shell_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 2 docstring (lines 70,252) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/web_search/web_search_models.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 1 docstring, 1 comment (lines 64,143) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/web_search/web_search_security_checks.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | Extracted from/REQ-N: 2 docstring (lines 4,12) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `scripts/mcp_servers/web_search/web_search_server.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-002 / AC-2 | REQ-N: 2 docstring (lines 341,346) (checked in Step 2) | `tests/mcp_servers` | Verified |
| `config/eventbus.toml` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 2 TOML comment (lines 47,53) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/ack_route.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 1 docstring, 10 comment (lines 58,67,126,141,151,173...) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/admin_route.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | EBAUTHGEN001/REQ-N: 2 docstring, 3 comment (lines 108,114,143,171,238) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/app.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 2 docstring, 5 comment (lines 20,21,75,114,115,119...) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/audit.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | EBAUTHGEN001: 1 docstring (lines 155) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/auth.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | EBAUTHGEN001/REQ-N: 1 docstring, 1 comment (lines 56,144) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/authz_ttl.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | EBAUTHGEN001/REQ-N: 1 docstring (lines 4) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/config.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | EBAUTHGEN001/REQ-N: 1 docstring, 1 comment (lines 79,382) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/db_conn.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 1 docstring (lines 39) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/delivery_repo.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 4 comment (lines 41,177,186,202) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/dlq.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 14 docstring, 2 comment (lines 66,116,118,168,210,216...) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/dlq_repo.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 2 docstring (lines 136,150) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/health_route.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 1 comment (lines 107) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/route_helpers.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 1 comment (lines 164) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/schema.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 1 docstring (lines 34) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/eventbus/subscribe_route.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-003 / AC-3 | REQ-N: 13 comment (lines 82,91,106,120,174,189...) (checked in Step 2) | `tests/eventbus` | Verified |
| `scripts/rag/config_resolution.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 3) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/db_connection.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 3) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/diagnostics.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 3) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/content_extractor.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 6) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/crawl_persister.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 6) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/crawler.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Refactored:/crawl003: 2 docstring (lines 12,156) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/crawler_utils.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from/REQ-N: 2 docstring (lines 6,8) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/document_manager.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | REQ-N: 1 comment (lines 106) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/http_fetcher.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from/REQ-N: 3 docstring, 1 comment (lines 6,33,87,163) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/ingester.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | RAGCORPUS001/REQ-N: 1 comment (lines 184) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/language_resolver.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 6) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/link_discovery.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 6) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/orchestrator.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from/REQ-N: 2 docstring (lines 6,264) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/ingestion/robots.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | REQ-N: 4 docstring, 1 comment (lines 7,12,25,45,48) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/llm_client.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | REQ-N: 1 comment (lines 148) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/models_result.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | RAGCORPUS001/REQ-N: 1 comment (lines 90) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/pipeline.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | RAGCORPUS001/REQ-N: 3 comment (lines 90,200,257) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/repository.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 6) (checked in Step 2) | `tests/rag` | Verified |
| `scripts/rag/stage_lifecycle.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-004 / AC-4 | Extracted from: 1 docstring (lines 3) (checked in Step 2) | `tests/rag` | Verified |
| `config/agent.toml` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 TOML comment (lines 20) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `config/mcp_dedup.toml` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 10 TOML comment (lines 4,7,18,23,26,32...) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/create_schema.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 docstring (lines 48) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/rag_consistency_queries.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | Extracted from/RAGCORPUS001/REQ-N: 3 docstring (lines 12,14,266) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/recovery.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 2 docstring (lines 291,345) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/recovery_drill.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 2 docstring, 3 comment (lines 15,72,214,226,232) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/recovery_restore.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 5 docstring, 1 comment (lines 6,25,27,44,85,103) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/recovery_verification.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 4 docstring, 1 comment (lines 6,34,68,128,147) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/rotation.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 docstring (lines 36) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/schema_sql.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 in a string literal (lines 223); the string-literal line is an SQL comment before a `CREATE TABLE` (fingerprint normalization strips comments) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/db/session_consistency.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 docstring, 1 comment (lines 80,107) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/component_mandatoriness.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 docstring (lines 3) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/execution_snapshot.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 docstring (lines 5) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/http_transport.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 2 docstring, 3 comment (lines 65,154,211,235,294) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/mcp_config.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 comment (lines 189) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/mcp_dedup.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 3 docstring, 1 comment (lines 68,272,304,434) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/runtime_paths.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 docstring (lines 9) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/runtime_tool_registry.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 docstring (lines 110) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/security/shadow_validation.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 2 docstring (lines 22,70) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/security/startup_flow.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 4 docstring, 1 comment (lines 42,67,164,186,238) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/tool_constants.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 8 comment (lines 179,185,189,194,197,203...) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `scripts/shared/tool_transport_invoker.py` | Comment and docstring cleanup | Rewrite the history or plan-identifier text as current-tense behavior, or remove it | REQ-005 / AC-5 | REQ-N: 1 comment (lines 304) (checked in Step 2) | `tests/shared tests/db` | Verified |
| `registry/manifests/eventbus_api.yaml` | Generated manifest | Regenerate: the summary of `AuthzGeneration` in `scripts/eventbus/auth.py` (first docstring line) names `EBAUTHGEN001` | REQ-003 / AC-3 | `AuthzGeneration` summary "Immutable authorization generation snapshot (EBAUTHGEN001)." is the first docstring line the generator copies (checked in Step 2) | `generate_reference_table.py --check` | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Generated reference block | Regenerate the guarded block from the manifest after the `AuthzGeneration` docstring changes | REQ-003 / AC-3 | guarded block rows are generated from `eventbus_api.yaml` (checked in Step 2) | `generate_reference_table.py --check` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/generate_reference_table.py` | `_first_docstring_line` shows which docstring text reaches generated documents | REQ-003 |
| `scripts/shared/schema_fingerprint.py` | `_normalize_ddl` strips SQL comments, so the `schema_sql.py` comment edit is safe | REQ-005 |
| `tools/check_adr_reference.py` | Verifies the `# ADR-NNN` markers the sweep must not remove | REQ-006 |
| `tools/check_suppression_justification.py` | Requires an error code and a justification on suppression comments that carry identifiers | REQ-006 |
| `rules/coding.md` | Comment language and suppression governance | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001): `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/agent` returns nothing after phase 1.
- AC-2 (REQ-002): the same search over `scripts/mcp_servers` returns nothing after phase 2.
- AC-3 (REQ-003): the same search over `scripts/eventbus` and `config/eventbus.toml` returns nothing after phase 3, and `uv run python tools/generate_reference_table.py --check` passes.
- AC-4 (REQ-004): the same search over `scripts/rag` returns nothing after phase 4.
- AC-5 (REQ-005): the same search over `scripts/shared`, `scripts/db`, `config/agent.toml`, and `config/mcp_dedup.toml` returns nothing after phase 5.
- AC-6 (REQ-006): `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003" scripts config` and `rg -n "REQ-[0-9]+" scripts config` return nothing; `git diff` shows comment, docstring, TOML comment, the one SQL comment, and the two generated files only; the validation sequence passes unchanged.

## Tests
- No new tests (Issue Testing Expectations). Each phase runs the matching test directory (`tests/agent`, `tests/mcp_servers`, `tests/eventbus`, `tests/rag`, `tests/shared`, `tests/db`); phase 5 adds `uv run pytest tests/shared/test_schema_fingerprint.py` after the `schema_sql.py` edit.
- `git diff -U0` filtered to non-comment, non-docstring lines must be empty; the procedure records the check.

## Documentation Impact
- N/A except the generated block: `docs/24_eventbus/eventbus_08_reference_api.md` and `registry/manifests/eventbus_api.yaml` are regenerated by `tools/generate_reference_table.py` (REQ-003). If a comment removal leaves a non-obvious constraint undocumented, record it in the owning document only when it is intent or failure behavior (Issue); run the `routing.md` docs checkers for the regenerated document.

## Assumptions
- A comment is kept only if it states current behavior or a constraint that is not obvious from the code; the rewrite changes the tense and drops the plan identifier, not the information.
- Rows whose matches disappear before this Plan runs (because the six earlier Plans edited the file) are closed by recording the search result, not by editing.
- The search patterns are those of the Issue; the `REQ-[0-9]+` pattern also matches text such as `REQ-1` in docstrings of tests, which are out of scope (UNK-01).
- Step 8b overlap judgements (`tools/check_plan_target_overlaps.py`): every file this Plan shares with `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md`, `plans/20261112-120425_rmcompat002_rag-diagnostics-model.md`, `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md`, `plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md`, `plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md`, or `plans/20261112-121532_rmcompat006_rag-ingestion-cleanup.md` is a sequencing dependency recorded in Scope Dependencies (those Plans run first; this one re-reads each file). The two other overlaps are compatible: `scripts/agent/production_config_validator.py` and `scripts/eventbus/auth.py` with `plans/20261111-112439_adrrev019_docs-stale-statements.md` (that Plan adds one startup validation and corrects the `attach_auth_middleware` docstring; this Plan edits history comments only, so re-read both files before editing). The overlaps on `config/eventbus.toml`, `registry/manifests/eventbus_api.yaml`, and `docs/24_eventbus/eventbus_08_reference_api.md` with rmcompat004 and rmcompat005 are sequencing dependencies: those Plans run first and this Plan regenerates the two generated files again at the end.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether tests that cite the same identifiers should be swept in a later Issue | Maintainer preference | Out of scope here; file a separate Issue if wanted | False |
| UNK-02 | The final file list after rmcompat001 to rmcompat006 land (the matches shrink) | The state after those Plans | The procedure step re-runs the searches before editing; rows with no match are closed | False |
| UNK-03 | Whether the single SQL comment in `schema_sql.py` may be edited under a comment-only rule | Maintainer preference | Treated as allowed (comments are stripped by the fingerprint); the fingerprint tests verify it; keep the comment unchanged if the user objects | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/audit_event_emitter.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/bg_task_monitor.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/agent/commands/memory_data_ops.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/commands/memory_rebuild_ops.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/context.py` | Modify | Low | 14 | N/A | not applicable (rsynced) |
| `scripts/agent/conversation_state_manager.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/history_selection_policy.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/http_lifecycle.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/agent/http_lifecycle_errors.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/http_lifecycle_health_checker.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/lifecycle.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/lifecycle_router.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/agent/llm_turn_executor.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/llm_turn_runner.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/memory/import_ops.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/memory/pin_ops.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/memory/write_ops.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/agent/orchestrator.py` | Modify | Low | 11 | N/A | not applicable (rsynced) |
| `scripts/agent/production_config_validator.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/services/context_view.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/services/db_maintenance_service.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/services/export_formatter.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/agent/services/mcp_status.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/services/models.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/agent/services/posture_validator.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/services/rag_maintenance_service.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/services/session_restore.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/services/session_title.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/services/tool_validation.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/services/undo_service.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/services/workflow_schema.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/agent/session.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/session_message_repo.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/agent/shared/retry_helper.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/startup.py` | Modify | Low | 9 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_component_init.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_mcp_starter.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_prompt_setup.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_reporter.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_validation.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_approval.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_audit.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_loop_guard.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_policy.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_preparation.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_round_completion.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_run_recorder.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_runner.py` | Modify | Low | 16 | N/A | not applicable (rsynced) |
| `scripts/agent/turn_persistence.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | Modify | Low | 11 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/tool_call_state_ops.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_engine.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_loader.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow_engine_adapter.py` | Modify | Low | 13 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/dispatch.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_server.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_service.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/read_security.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/read_server.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/write_server.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/format_output.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/git_models.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/git_server.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/git_service.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/repository_state.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/write_protection_pipeline.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/github/github_server.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/github/github_service_security.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/github/mapper.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/web_search/web_search_models.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/web_search/web_search_security_checks.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/web_search/web_search_server.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `config/eventbus.toml` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/eventbus/ack_route.py` | Modify | Low | 10 | N/A | not applicable (rsynced) |
| `scripts/eventbus/admin_route.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/eventbus/app.py` | Modify | Low | 13 | N/A | not applicable (rsynced) |
| `scripts/eventbus/audit.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/eventbus/auth.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/eventbus/authz_ttl.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/eventbus/config.py` | Modify | Low | 9 | N/A | not applicable (rsynced) |
| `scripts/eventbus/db_conn.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/eventbus/delivery_repo.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/eventbus/dlq.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/eventbus/dlq_repo.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/eventbus/health_route.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/eventbus/route_helpers.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/eventbus/schema.py` | Modify | Low | 9 | N/A | not applicable (rsynced) |
| `scripts/eventbus/subscribe_route.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/config_resolution.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/rag/db_connection.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/rag/diagnostics.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/content_extractor.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/crawl_persister.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/crawler.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/crawler_utils.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/document_manager.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/ingester.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/language_resolver.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/link_discovery.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/orchestrator.py` | Modify | Low | 10 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/robots.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/llm_client.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/rag/models_result.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/pipeline.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/rag/repository.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/stage_lifecycle.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `config/agent.toml` | Modify | Low | 14 | N/A | not applicable (rsynced) |
| `config/mcp_dedup.toml` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/db/create_schema.py` | Modify | Low | 11 | N/A | not applicable (rsynced) |
| `scripts/db/rag_consistency_queries.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/db/recovery.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/db/recovery_drill.py` | Modify | Low | 10 | N/A | not applicable (rsynced) |
| `scripts/db/recovery_restore.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/db/recovery_verification.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/db/rotation.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | Modify | Low | 18 | N/A | not applicable (rsynced) |
| `scripts/db/session_consistency.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/shared/component_mandatoriness.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/shared/execution_snapshot.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/shared/http_transport.py` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/shared/mcp_config.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/shared/mcp_dedup.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/shared/runtime_paths.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/shared/runtime_tool_registry.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/shared/security/shadow_validation.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/shared/security/startup_flow.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `scripts/shared/tool_constants.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `scripts/shared/tool_transport_invoker.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `registry/manifests/eventbus_api.yaml` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Low | 23 | N/A | not applicable (rsynced) |

## Design
- Consumer scan: not a persisted schema, public API, or shared constant change; the only generated consumer of a rewritten docstring is the reference generator (one match found, see Background). A text search over `tools/` for the patterns found `tools/_docs_consistency_lib.py`, a document checker unrelated to these comments.
- Rewrite rules: delete a pure provenance note ("Extracted from X", "Refactored: ..."); replace a plan or requirement identifier with a statement of the rule it justified; keep the error code and justification of any suppression comment; keep a module docstring's first line (the path header that `tools/check_docstrings.py` and `tools/fix_docstring_paths.py` verify).
- Order: agent, mcp_servers, eventbus, rag, then shared, db, and config, following the Issue's decision; each phase leaves its directory free of matches and runs that directory's tests.
- Architecture, complexity, security, and persisted-schema checks: not applicable to a comment-only change (`lint-imports`, `radon`, `vulture`, and `bandit` baselines are unchanged by construction; `rules/persisted-schema-change.md` does not apply because the DDL statements are untouched); no port, process, or dependency change (`ss`, `fuser`, `pip-audit` N/A). Churn above from `git log --since=30.days`; bus factor not measured.

## Implementation steps
1. **Phase 1: agent** (55 files)
   - [ ] Re-run the pattern searches for these files, then rewrite or remove each match (REQ-001; `scripts/agent/audit_event_emitter.py`, `scripts/agent/bg_task_monitor.py`, `scripts/agent/commands/memory_data_ops.py`, `scripts/agent/commands/memory_rebuild_ops.py`, `scripts/agent/context.py`, `scripts/agent/conversation_state_manager.py`, `scripts/agent/history_selection_policy.py`, `scripts/agent/http_lifecycle.py`, `scripts/agent/http_lifecycle_errors.py`, `scripts/agent/http_lifecycle_health_checker.py`, `scripts/agent/lifecycle.py`, `scripts/agent/lifecycle_router.py`, `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/memory/import_ops.py`, `scripts/agent/memory/pin_ops.py`, `scripts/agent/memory/write_ops.py`, `scripts/agent/orchestrator.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/services/context_view.py`, `scripts/agent/services/db_maintenance_service.py`, `scripts/agent/services/export_formatter.py`, `scripts/agent/services/mcp_status.py`, `scripts/agent/services/models.py`, `scripts/agent/services/posture_validator.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/agent/services/session_restore.py`, `scripts/agent/services/session_title.py`, `scripts/agent/services/tool_validation.py`, `scripts/agent/services/undo_service.py`, `scripts/agent/services/workflow_schema.py`, `scripts/agent/session.py`, `scripts/agent/session_message_repo.py`, `scripts/agent/shared/retry_helper.py`, `scripts/agent/startup.py`, `scripts/agent/startup_component_init.py`, `scripts/agent/startup_mcp_starter.py`, `scripts/agent/startup_prompt_setup.py`, `scripts/agent/startup_reporter.py`, `scripts/agent/startup_validation.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_loop_guard.py`, `scripts/agent/tool_policy.py`, `scripts/agent/tool_preparation.py`, `scripts/agent/tool_round_completion.py`, `scripts/agent/tool_run_recorder.py`, `scripts/agent/tool_runner.py`, `scripts/agent/turn_persistence.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow_engine_adapter.py`)
   - [ ] Run `uv run pytest tests/agent` and confirm with `git diff` that only comments and docstrings changed (REQ-001)
2. **Phase 2: mcp_servers** (24 files)
   - [ ] Re-run the pattern searches for these files, then rewrite or remove each match (REQ-002; `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/dispatch.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/file/delete_service.py`, `scripts/mcp_servers/file/read_security.py`, `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/git/format_output.py`, `scripts/mcp_servers/git/git_models.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`, `scripts/mcp_servers/git/write_protection_pipeline.py`, `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/github/github_service_security.py`, `scripts/mcp_servers/github/mapper.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/web_search/web_search_models.py`, `scripts/mcp_servers/web_search/web_search_security_checks.py`, `scripts/mcp_servers/web_search/web_search_server.py`)
   - [ ] Run `uv run pytest tests/mcp_servers` and confirm with `git diff` that only comments and docstrings changed (REQ-002)
3. **Phase 3: eventbus** (16 files)
   - [ ] Re-run the pattern searches for these files, then rewrite or remove each match (REQ-003; `config/eventbus.toml`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/audit.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/config.py`, `scripts/eventbus/db_conn.py`, `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/route_helpers.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/subscribe_route.py`) and regenerate the manifest and the reference block (REQ-003; `registry/manifests/eventbus_api.yaml`, `docs/24_eventbus/eventbus_08_reference_api.md`)
   - [ ] Run `uv run pytest tests/eventbus` and confirm with `git diff` that only comments and docstrings changed (REQ-003)
4. **Phase 4: rag** (19 files)
   - [ ] Re-run the pattern searches for these files, then rewrite or remove each match (REQ-004; `scripts/rag/config_resolution.py`, `scripts/rag/db_connection.py`, `scripts/rag/diagnostics.py`, `scripts/rag/ingestion/content_extractor.py`, `scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/document_manager.py`, `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/language_resolver.py`, `scripts/rag/ingestion/link_discovery.py`, `scripts/rag/ingestion/orchestrator.py`, `scripts/rag/ingestion/robots.py`, `scripts/rag/llm_client.py`, `scripts/rag/models_result.py`, `scripts/rag/pipeline.py`, `scripts/rag/repository.py`, `scripts/rag/stage_lifecycle.py`)
   - [ ] Run `uv run pytest tests/rag` and confirm with `git diff` that only comments and docstrings changed (REQ-004)
5. **Phase 5: shared, db, config** (22 files)
   - [ ] Re-run the pattern searches for these files, then rewrite or remove each match (REQ-005; `config/agent.toml`, `config/mcp_dedup.toml`, `scripts/db/create_schema.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/recovery.py`, `scripts/db/recovery_drill.py`, `scripts/db/recovery_restore.py`, `scripts/db/recovery_verification.py`, `scripts/db/rotation.py`, `scripts/db/schema_sql.py`, `scripts/db/session_consistency.py`, `scripts/shared/component_mandatoriness.py`, `scripts/shared/execution_snapshot.py`, `scripts/shared/http_transport.py`, `scripts/shared/mcp_config.py`, `scripts/shared/mcp_dedup.py`, `scripts/shared/runtime_paths.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/shared/security/shadow_validation.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/tool_constants.py`, `scripts/shared/tool_transport_invoker.py`)
   - [ ] Run `uv run pytest tests/shared tests/db` and confirm with `git diff` that only comments and docstrings changed (REQ-005)
6. **Phase 6: Whole-tree verification and deployment**
   - [ ] Run the two whole-tree acceptance searches, `generate_reference_table.py --check`, the validation sequence, `tools/check_adr_reference.py`, and `tools/check_suppression_justification.py` (REQ-006)
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate) (REQ-006)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Each phase's directory | Unit | `uv run pytest <directory tests>` per phase | Pass |
| Changed Python files | Static | `uv run ruff format`, `ruff check`, `mypy --no-namespace-packages`, `lint-imports`, `bandit -r scripts/ -c pyproject.toml` | No new finding |
| Comment-only guarantee | Diff review | `git diff -U0` limited to non-comment lines | Empty (other than the SQL comment and generated files) |
| Suppression and ADR markers | Checkers | `uv run python tools/check_suppression_justification.py`, `uv run python tools/check_adr_reference.py` | No findings |
| Generated references | Generator | `uv run python tools/generate_reference_table.py --check` | No drift |
| Schema fingerprint | Unit | `uv run pytest tests/shared/test_schema_fingerprint.py` | Pass after the `schema_sql.py` edit |
| Docstring headers | Checker | `uv run python tools/check_docstrings.py` | No findings |
| Whole tree | Search | the AC-6 `rg` commands | Return nothing |

## Risks
- **Risk**: Deleting a comment removes a non-obvious constraint → **Mitigation**: the rewrite rule keeps the information in current tense; the procedure reviews each match before editing.
- **Risk**: A docstring edit drifts a generated reference → **Mitigation**: the one exposed docstring is a target with regeneration; `generate_reference_table.py --check` runs in every phase touching `scripts/agent`, `scripts/eventbus`, and `scripts/agent/memory`.
- **Risk**: A suppression comment loses its justification and fails the checker → **Mitigation**: eight such lines are known; `check_suppression_justification.py` runs per phase.
- **Risk**: A non-comment line changes by accident in a 136-file sweep → **Mitigation**: per-phase `git diff -U0` review and the full test directories.
- **Risk**: The six earlier Plans are not finished when this Plan is consumed → **Mitigation**: `tools/plan_dependency_order.py` reports this Plan as gated until they are `Completed`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Sweep `scripts/agent/` | Pending | — | — | |
| 2 | Sweep `scripts/mcp_servers/` | Pending | — | — | |
| 3 | Sweep `scripts/eventbus/` and `config/eventbus.toml`, regenerate references | Pending | — | — | |
| 4 | Sweep `scripts/rag/` | Pending | — | — | |
| 5 | Sweep `scripts/shared/`, `scripts/db/`, and the two other config files | Pending | — | — | |
| 6 | Whole-tree verification and deployment hand-off | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261112-122030
- **Related target files**: `scripts/agent/audit_event_emitter.py`, `scripts/agent/bg_task_monitor.py`, `scripts/agent/commands/memory_data_ops.py`, `scripts/agent/commands/memory_rebuild_ops.py`, `scripts/agent/context.py`, `scripts/agent/conversation_state_manager.py`, `scripts/agent/history_selection_policy.py`, `scripts/agent/http_lifecycle.py`, `scripts/agent/http_lifecycle_errors.py`, `scripts/agent/http_lifecycle_health_checker.py`, `scripts/agent/lifecycle.py`, `scripts/agent/lifecycle_router.py`, `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/memory/import_ops.py`, `scripts/agent/memory/pin_ops.py`, `scripts/agent/memory/write_ops.py`, `scripts/agent/orchestrator.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/services/context_view.py`, `scripts/agent/services/db_maintenance_service.py`, `scripts/agent/services/export_formatter.py`, `scripts/agent/services/mcp_status.py`, `scripts/agent/services/models.py`, `scripts/agent/services/posture_validator.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/agent/services/session_restore.py`, `scripts/agent/services/session_title.py`, `scripts/agent/services/tool_validation.py`, `scripts/agent/services/undo_service.py`, `scripts/agent/services/workflow_schema.py`, `scripts/agent/session.py`, `scripts/agent/session_message_repo.py`, `scripts/agent/shared/retry_helper.py`, `scripts/agent/startup.py`, `scripts/agent/startup_component_init.py`, `scripts/agent/startup_mcp_starter.py`, `scripts/agent/startup_prompt_setup.py`, `scripts/agent/startup_reporter.py`, `scripts/agent/startup_validation.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_loop_guard.py`, `scripts/agent/tool_policy.py`, `scripts/agent/tool_preparation.py`, `scripts/agent/tool_round_completion.py`, `scripts/agent/tool_run_recorder.py`, `scripts/agent/tool_runner.py`, `scripts/agent/turn_persistence.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/dispatch.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/file/delete_service.py`, `scripts/mcp_servers/file/read_security.py`, `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/git/format_output.py`, `scripts/mcp_servers/git/git_models.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`, `scripts/mcp_servers/git/write_protection_pipeline.py`, `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/github/github_service_security.py`, `scripts/mcp_servers/github/mapper.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/web_search/web_search_models.py`, `scripts/mcp_servers/web_search/web_search_security_checks.py`, `scripts/mcp_servers/web_search/web_search_server.py`, `config/eventbus.toml`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/audit.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/config.py`, `scripts/eventbus/db_conn.py`, `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/route_helpers.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/subscribe_route.py`, `scripts/rag/config_resolution.py`, `scripts/rag/db_connection.py`, `scripts/rag/diagnostics.py`, `scripts/rag/ingestion/content_extractor.py`, `scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/document_manager.py`, `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/language_resolver.py`, `scripts/rag/ingestion/link_discovery.py`, `scripts/rag/ingestion/orchestrator.py`, `scripts/rag/ingestion/robots.py`, `scripts/rag/llm_client.py`, `scripts/rag/models_result.py`, `scripts/rag/pipeline.py`, `scripts/rag/repository.py`, `scripts/rag/stage_lifecycle.py`, `config/agent.toml`, `config/mcp_dedup.toml`, `scripts/db/create_schema.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/recovery.py`, `scripts/db/recovery_drill.py`, `scripts/db/recovery_restore.py`, `scripts/db/recovery_verification.py`, `scripts/db/rotation.py`, `scripts/db/schema_sql.py`, `scripts/db/session_consistency.py`, `scripts/shared/component_mandatoriness.py`, `scripts/shared/execution_snapshot.py`, `scripts/shared/http_transport.py`, `scripts/shared/mcp_config.py`, `scripts/shared/mcp_dedup.py`, `scripts/shared/runtime_paths.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/shared/security/shadow_validation.py`, `scripts/shared/security/startup_flow.py`, `scripts/shared/tool_constants.py`, `scripts/shared/tool_transport_invoker.py`, `registry/manifests/eventbus_api.yaml`, `docs/24_eventbus/eventbus_08_reference_api.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/audit_event_emitter.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/bg_task_monitor.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/commands/memory_data_ops.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 3 matching line(s) | `scripts/agent/commands/memory_rebuild_ops.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 5 matching line(s) | `scripts/agent/context.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/conversation_state_manager.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/history_selection_policy.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/http_lifecycle.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/http_lifecycle_errors.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/http_lifecycle_health_checker.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/lifecycle.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/lifecycle_router.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/llm_turn_executor.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/llm_turn_runner.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/memory/import_ops.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/memory/pin_ops.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/memory/write_ops.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/orchestrator.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/production_config_validator.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/services/context_view.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/services/db_maintenance_service.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/services/export_formatter.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/services/mcp_status.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/services/models.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/services/posture_validator.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/services/rag_maintenance_service.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 8 matching line(s) | `scripts/agent/services/session_restore.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/services/session_title.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/services/tool_validation.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 5 matching line(s) | `scripts/agent/services/undo_service.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/services/workflow_schema.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/session.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 8 matching line(s) | `scripts/agent/session_message_repo.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/shared/retry_helper.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/startup.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 3 matching line(s) | `scripts/agent/startup_component_init.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/startup_mcp_starter.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/startup_prompt_setup.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/startup_reporter.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 8 matching line(s) | `scripts/agent/startup_validation.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/tool_approval.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/tool_audit.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 3 matching line(s) | `scripts/agent/tool_loop_guard.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 15 matching line(s) | `scripts/agent/tool_policy.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/tool_preparation.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 2 matching line(s) | `scripts/agent/tool_round_completion.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/tool_run_recorder.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 17 matching line(s) | `scripts/agent/tool_runner.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 17 matching line(s) | `scripts/agent/turn_persistence.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/workflow/idempotency_ops.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 14 matching line(s) | `scripts/agent/workflow/state_store.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/workflow/tool_call_state_ops.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 9 matching line(s) | `scripts/agent/workflow/workflow_engine.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 1 matching line(s) | `scripts/agent/workflow/workflow_loader.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; 11 matching line(s) | `scripts/agent/workflow_engine_adapter.py` | 1 | AC-1 | `tests/agent` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 3 matching line(s) | `scripts/mcp_servers/cicd/cicd_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 18 matching line(s) | `scripts/mcp_servers/dispatch.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 3 matching line(s) | `scripts/mcp_servers/file/delete_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 1 matching line(s) | `scripts/mcp_servers/file/delete_service.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 1 matching line(s) | `scripts/mcp_servers/file/read_security.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 3 matching line(s) | `scripts/mcp_servers/file/read_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 3 matching line(s) | `scripts/mcp_servers/file/write_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 2 matching line(s) | `scripts/mcp_servers/git/format_output.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 1 matching line(s) | `scripts/mcp_servers/git/git_models.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 4 matching line(s) | `scripts/mcp_servers/git/git_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 3 matching line(s) | `scripts/mcp_servers/git/git_service.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 4 matching line(s) | `scripts/mcp_servers/git/repository_state.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 8 matching line(s) | `scripts/mcp_servers/git/write_protection_pipeline.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 3 matching line(s) | `scripts/mcp_servers/github/github_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 1 matching line(s) | `scripts/mcp_servers/github/github_service_security.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 1 matching line(s) | `scripts/mcp_servers/github/mapper.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 2 matching line(s) | `scripts/mcp_servers/mdq/mdq_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 2 matching line(s) | `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 1 matching line(s) | `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 4 matching line(s) | `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 2 matching line(s) | `scripts/mcp_servers/shell/shell_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 2 matching line(s) | `scripts/mcp_servers/web_search/web_search_models.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 2 matching line(s) | `scripts/mcp_servers/web_search/web_search_security_checks.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-002 | Required Changes 1; 2 matching line(s) | `scripts/mcp_servers/web_search/web_search_server.py` | 2 | AC-2 | `tests/mcp_servers` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 2 matching line(s) | `config/eventbus.toml` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 11 matching line(s) | `scripts/eventbus/ack_route.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 5 matching line(s) | `scripts/eventbus/admin_route.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 7 matching line(s) | `scripts/eventbus/app.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 1 matching line(s) | `scripts/eventbus/audit.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 2 matching line(s) | `scripts/eventbus/auth.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 1 matching line(s) | `scripts/eventbus/authz_ttl.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 2 matching line(s) | `scripts/eventbus/config.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 1 matching line(s) | `scripts/eventbus/db_conn.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 4 matching line(s) | `scripts/eventbus/delivery_repo.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 16 matching line(s) | `scripts/eventbus/dlq.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 2 matching line(s) | `scripts/eventbus/dlq_repo.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 1 matching line(s) | `scripts/eventbus/health_route.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 1 matching line(s) | `scripts/eventbus/route_helpers.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 1 matching line(s) | `scripts/eventbus/schema.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; 13 matching line(s) | `scripts/eventbus/subscribe_route.py` | 3 | AC-3 | `tests/eventbus` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/config_resolution.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/db_connection.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/diagnostics.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/ingestion/content_extractor.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/ingestion/crawl_persister.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 2 matching line(s) | `scripts/rag/ingestion/crawler.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 2 matching line(s) | `scripts/rag/ingestion/crawler_utils.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/ingestion/document_manager.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 4 matching line(s) | `scripts/rag/ingestion/http_fetcher.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/ingestion/ingester.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/ingestion/language_resolver.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/ingestion/link_discovery.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 2 matching line(s) | `scripts/rag/ingestion/orchestrator.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 5 matching line(s) | `scripts/rag/ingestion/robots.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/llm_client.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/models_result.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 3 matching line(s) | `scripts/rag/pipeline.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/repository.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-004 | Required Changes 1; 1 matching line(s) | `scripts/rag/stage_lifecycle.py` | 4 | AC-4 | `tests/rag` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `config/agent.toml` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 10 matching line(s) | `config/mcp_dedup.toml` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/db/create_schema.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 3 matching line(s) | `scripts/db/rag_consistency_queries.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 2 matching line(s) | `scripts/db/recovery.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 5 matching line(s) | `scripts/db/recovery_drill.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 6 matching line(s) | `scripts/db/recovery_restore.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 5 matching line(s) | `scripts/db/recovery_verification.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/db/rotation.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/db/schema_sql.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 2 matching line(s) | `scripts/db/session_consistency.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/shared/component_mandatoriness.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/shared/execution_snapshot.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 5 matching line(s) | `scripts/shared/http_transport.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/shared/mcp_config.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 4 matching line(s) | `scripts/shared/mcp_dedup.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/shared/runtime_paths.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/shared/runtime_tool_registry.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 2 matching line(s) | `scripts/shared/security/shadow_validation.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 5 matching line(s) | `scripts/shared/security/startup_flow.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 8 matching line(s) | `scripts/shared/tool_constants.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-005 | Required Changes 1; 1 matching line(s) | `scripts/shared/tool_transport_invoker.py` | 5 | AC-5 | `tests/shared tests/db` | Confirmed by repository evidence |
| REQ-003 | Derived from `scripts/eventbus/auth.py` first docstring line | `registry/manifests/eventbus_api.yaml` | 3 | AC-3 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-003 | Derived from `scripts/eventbus/auth.py` first docstring line | `docs/24_eventbus/eventbus_08_reference_api.md` | 3 | AC-3 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-006 | Constraints and Acceptance Criteria 3-4 | `scripts/db/schema_sql.py` | 5 | AC-6 | `tests/shared/test_schema_fingerprint.py` | Confirmed by repository evidence |
