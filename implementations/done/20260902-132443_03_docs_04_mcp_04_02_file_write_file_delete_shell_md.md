## Goal

Reword the `> **Enforcement in Production:**` passage and its nested `> > **Note**` (both under the "Sandbox Backend" section) to state the `RuntimeError` enforcement applies regardless of `security_profile`/environment, removing all production-only framing. (REQ-003; AC-3)

## Scope

- Modify exactly one passage in `docs/04_mcp_04_02_file-write-file-delete-shell.md`:
  - Line 106: `> **Enforcement in Production:** In production mode (...)` — reword to remove "in production mode" framing
  - Line 108: `> > **Note**: Enforcement in production is handled by...` — reword similarly
- Change the heading from "Enforcement in Production" to something environment-neutral (e.g., "Enforcement")

## Assumptions

- The passage structure (blockquote with nested Note) is preserved — only the text content changes
- The reference to `scripts/agent/services/security_audit.py::audit_security_defaults()` remains accurate after REQ-001 is applied
- No other passages in this file describe the same conditional behavior (confirmed: line 106 is the sole occurrence)

## Design decisions

- Rename the heading from "Enforcement in Production" to "Enforcement" since the enforcement is no longer production-specific
- Reword the body text to state that `sandbox_backend = "none"` raises `RuntimeError` unconditionally
- Reword the nested Note to remove "in production" framing while preserving the operational detail about Agent startup enforcement

## Alternatives considered

- Keeping the "Enforcement in Production" heading but adding a qualifier like "(or equivalent)" — rejected because it preserves misleading production-only framing
- Splitting the passage into two (one for production, one for general) — rejected because there is no longer a distinction to make

## Compatibility considerations

- This is a documentation-only change — no behavioral impact
- The reworded passage must remain consistent with the corrected code behavior from REQ-001

## Security considerations

- No security impact — this is a documentation update reflecting the corrected behavior

## Rollback considerations

- To roll back: restore the original "Enforcement in Production" heading and text on lines 106 and 108

## Validation plan

### Documentation structure/formatting check
- `uv run python tools/check_docs_quality.py` — no new structural/formatting violations
- `uv run python tools/check_docs_structure.py docs/04_mcp_04_02_file-write-file-delete-shell.md` — passes: Front Matter, headings, Related Documents/Keywords, internal link reachability

### Cross-check doc claims against source code
- `uv run python tools/check_docs_consistency.py --domain mcp` — no new drift reported between the reworded passage and the corrected code behavior

## Completion criteria

- [ ] The heading `> **Enforcement in Production:**` is replaced with an environment-neutral heading (e.g., `> **Enforcement:**`)
- [ ] The body text no longer states or implies that a non-production environment relaxes the `RuntimeError` enforcement
- [ ] The nested `> > **Note**` no longer uses "in production" framing
- [ ] `uv run python tools/check_docs_quality.py` reports no new violations
- [ ] `uv run python tools/check_docs_structure.py docs/04_mcp_04_02_file-write-file-delete-shell.md` passes
- [ ] `uv run python tools/check_docs_consistency.py --domain mcp` reports no new drift

## Out of scope

- Updating `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` (out of this Plan's scope, tracked separately)
- Modifying any other content in this file unrelated to the named passage
- Changing the sandbox backend configuration table (lines 100-104)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the "Enforcement in Production" passage and its nested Note to describe unconditional enforcement | Done | 2026-09-02 | 2026-09-02 | Replaced heading and body text per REQ-003 |
| 2 | Run documentation validation commands (check_docs_quality, check_docs_structure, check_docs_consistency) | Done | 2026-09-02 | 2026-09-02 | No new violations from this change |

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
- **Requirement ID**: REQ-003; AC-3
- **Source issue**: issues/20260831-192510_adr004_07_shell_mcp_sandbox_production_only_enforcement.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-104253_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-132443
- **Related target files**: docs/04_mcp_04_02_file-write-file-delete-shell.md
