## Goal

Update `docs/23_agent/agent_09_01_data-layer-session-db.md` to document the fail-closed persistence policy (`REQ-005`), the stored-format states and distinct retrieval (`REQ-006`), and the resolved production-encryption decision, consistent with `REQ-001` (injected config, no per-op read).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The doc is prose documentation; this workflow writes only the procedure below. `code-implementation` performs the actual edit to `docs/23_agent/agent_09_01_data-layer-session-db.md`.
- Per `skills/DESIGN.md` (No concrete configuration values), the updated doc must not embed concrete config values such as the encryption key or its empty default.
- The resolved 2026-10-25 Option B decision (redacted plaintext when no key) is preserved; only the fail-closed and stored-format details are added.

## Design decisions
- **Edit the two existing sections** rather than add a new one: the "Role of `session_diagnostics`" block (header line 61) and the "Accepted storage posture" block (line 70), so the change stays co-located with the behavior it describes.

## Alternatives considered
- **Add a new subsection.** Rejected: the behavior already has a home in the existing `session_diagnostics` sections; folding in keeps the doc navigable.

## Implementation
### Target file
`docs/23_agent/agent_09_01_data-layer-session-db.md`
### Procedure
- Revise the fail-closed policy and the stored-format/retrieval description; preserve the production-encryption decision.
### Method
- **"Role of `session_diagnostics`" (lines 61-68)**:
  - Note `save()` consumes the injected, validated `DiagnosticsConfig` snapshot (`REQ-001`); it performs no `agent.toml` read per operation.
  - Replace the sentence stating encryption happens with `encrypt=True` with the by-policy rule: a record is encrypted when a key is configured, otherwise filtered and secret-checked.
  - State the fail-closed rule (`REQ-005`): on filter failure the write is rejected or the content is replaced with a fixed marker; the original content is never persisted.
- **"Accepted storage posture" (lines 70-76)**:
  - Update the carve-out bullet (current line 73): the filter-failure path no longer persists the (unfiltered) original — it rejects the write or stores the fixed marker instead.
  - Add the three stored-format states recorded in the `session_diagnostics.storage_format` column: `encrypted`, `redacted_plaintext`, `decrypt_failed`.
  - State that `fetch()` classifies each row by `storage_format` and never returns ciphertext as ordinary `content` (`REQ-006`); a `decrypt_failed` row is reported distinctly.
  - Preserve the resolved Option B decision and note `retention_days` validates a positive-int type while keeping the documented "0 or less disables purge" runtime semantic.
- Do not introduce concrete config values (e.g. the key or its empty default).

### Companion test files
N/A.

## Compatibility considerations
The change is documentation-only; it mirrors the runtime behavior implemented in `scripts/agent/diagnostic_store.py` (its own rows) and the DDL change in `scripts/db/schema_sql.py`. Keep the prose consistent with those once they land.

## Security considerations
The fail-closed policy and the stored-format classification are the documented expression of the data-protection fix (`AC-1`, `AC-4`); document them accurately so operators understand that a decrypt-failed row is surfaced distinctly rather than leaked as content.

## Rollback considerations
Revert the commit.

## Validation plan
- Doc consistency: `uv run python tools/check_docs_consistency.py --domain agent`.
- Human review against `AC-1`/`AC-4`: the doc states fail-closed persistence and distinct decrypt-failed reporting.

## Completion criteria
- The "Role of `session_diagnostics`" section documents fail-closed persistence (`REQ-005`) and by-policy encryption.
- The "Accepted storage posture" section records the `encrypted` / `redacted_plaintext` / `decrypt_failed` stored-format states and that `fetch()` never returns ciphertext as `content` (`REQ-006`).
- `check_docs_consistency.py --domain agent` passes.

## Out of Scope
- Concrete configuration values.
- Changing the retention runtime semantic ("0 or less disables purge").

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Edit the two existing sections; no concrete config values |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs consistency check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row |

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
- **Requirement ID**: `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261111-163701_diagstore002_diagnostic-store-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261114-161816_diagstore002_diagnostic-store-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-170132
- **Related target files**: `docs/23_agent/agent_09_01_data-layer-session-db.md`
