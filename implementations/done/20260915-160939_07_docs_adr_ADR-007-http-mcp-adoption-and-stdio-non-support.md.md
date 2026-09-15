## Goal
Remove ADR-007's redundant file/class/config/test list from `## Implementation
Notes` once reconciled into `### Implementation References`, per `REQ-007` —
including migrating unique, non-duplicated content and correcting a wrong
filename found during adversarial verification — while leaving the Circuit
Breaker 5-state description untouched.

## Scope
- In scope: migrate the HTTP endpoint list (`POST /v1/call_tool`, `GET /v1/tools`,
  `GET /health`) and the 認証トークン sub-clause into References (both unique,
  not currently duplicated anywhere); correct References'
  `scripts/shared/mcp_server_health_registry.py` (confirmed nonexistent) to
  `scripts/shared/mcp_health.py`; delete the now-reconciled Notes bullets.
- Out of scope: line 342 (Circuit Breaker 5-state description) — tracked in a
  separate issue, MUST remain unchanged.

## Assumptions
- No pointer line is needed — line 342 survives, keeping the section non-empty.
- `McpServerHealthRegistry.record_failure()` is confirmed correct
  (`scripts/shared/mcp_health.py:36`) — only the filename is wrong, not the
  method name.

## Design decisions
- The HTTP endpoint list and auth-token sub-clause are not derivable from a
  file/symbol name alone (API-surface/config-behavior facts), so per the Plan's
  Design "Not every list item is a true duplicate," they migrate into References
  as new canonical content rather than being dropped.
- The wrong filename is a pre-existing References error, unrelated to the
  cross-copy comparison (Notes never names this file at all — it's an internal
  References-only mistake) — fixed while the section is being edited anyway, for
  the same reason as REQ-001's `request_approval()` fix.

## Alternatives considered
- Leave the HTTP endpoint list and auth-token note in Notes as protected prose
  (like ADR-008's WAL/checkpoint lines) instead of migrating to References —
  considered, but rejected: unlike ADR-008's items (which have no natural home in
  a file/symbol-oriented References section), these describe the http-mcp
  adoption's actual API surface and config source, which fits References'
  existing convention of documenting concrete implementation facts per file.

## Implementation
### Target file
`docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   338-343 (with 342 as the protected Circuit Breaker line) and References at
   423-428.
2. Re-confirm via `ls scripts/shared/mcp_server_health_registry.py` (expect
   failure) and `ls scripts/shared/mcp_health.py` (expect success) that the
   filename correction is still needed.
3. Correct References' `scripts/shared/mcp_server_health_registry.py` entry to
   `scripts/shared/mcp_health.py` (keep `McpServerHealthRegistry.record_failure()`
   unchanged).
4. Add a new References bullet for the HTTP endpoint list: `POST /v1/call_tool`,
   `GET /v1/tools`, `GET /health` (copied verbatim from Notes line 341).
5. Add the 認証トークン（環境変数またはシークレットファイル）sub-clause to
   References' existing `config/*_mcp_server.toml` bullet (or as its own bullet,
   matching this ADR's existing References style).
6. Delete Notes lines 338, 339, 341, 343 (実装ファイル, 主要Class/Function,
   HTTPエンドポイント, 対応するテスト) — leave line 342 (Circuit Breaker)
   untouched, in place.

### Method
Use `Edit` (exact-string replacement) — one call per step 3-6.

### Details
- Line 340 (実装ファイル's データベーススキーマ-labeled but actually MCP-config-
  and auth-token content) is being partially migrated (auth-token sub-clause) and
  partially reconciled (the `config/*_mcp_server.toml` file itself is already in
  References) — do not delete line 340 until step 5's migration is confirmed
  landed in References.
- Preserve line 342 byte-for-byte; verify with a diff after editing.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change. The auth-token sub-clause being migrated is a
description of where the token is sourced (env var or secret file), not the
token value itself — no secret is introduced into the document.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` if
validation fails.

## Validation plan
- `ls scripts/shared/mcp_server_health_registry.py` (expect failure) and `ls scripts/shared/mcp_health.py` (expect success) — re-confirm before editing.
- Manual diff: confirm References includes the HTTP endpoint list, the auth-token sub-clause, and the corrected filename; confirm Notes retains only line 342.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- References no longer cites `mcp_server_health_registry.py`; cites `mcp_health.py`.
- References includes the HTTP endpoint list and auth-token sub-clause.
- `## Implementation Notes` retains only line 342 plus boilerplate.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- Line 342 (Circuit Breaker 5-state description).
- Any other section of ADR-007.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-162916 | Migrated HTTP endpoint list + auth-token sub-clause; corrected mcp_server_health_registry.py to mcp_health.py; deleted reconciled Notes lines; preserved Circuit Breaker line |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162916 | 20260915-162916 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162916 | 20260915-162916 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 14 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162916 | 20260915-162916 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-007 — migrate unique content, correct filename, reconcile rest, preserve line 342
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md