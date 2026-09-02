## Goal

Satisfy `REQ-001`/`REQ-002`: fix the stale module-path reference in
`docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`'s "Enforcement Point" sentence, and
reword the four passages that still describe `shell_sandbox_backend == "none"` as
warning-only outside production, now that the sibling Plan's REQ-001 code fix has landed.

## Scope

Modify exactly `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`: the "Enforcement
Point" sentence (line 44), the `# Development:` code-block comment (line 72), the
"Sandbox Backend" table's `none` row (line 80), and the "Startup Enforcement" bullet
list's third bullet (line 88). No other content in this file, and no other file, is
touched.

## Assumptions

- Re-verified 2026-09-02 (this cycle): `scripts/agent/services/security_audit.py` lines
  111-119 confirm the `if shell_cfg.sandbox_backend == "none":` `RuntimeError` is no
  longer gated by `if production_mode:` — the message is
  `"shell_sandbox_backend=none is not permitted regardless of environment"`. The sibling
  Plan's REQ-001 has landed exactly as the source Plan's Background describes.
- Re-verified 2026-09-02: `scripts/agent/repl_health.py` still only re-exports
  `audit_security_defaults` (lines 7, 45) — it is a re-export shim, not the real
  implementation, confirming REQ-001's module-path correction target.
- Re-verified 2026-09-02: all four target passages in
  `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` are present verbatim at their
  Plan-cited line numbers (44, 72, 80, 88) — no drift since the Plan's last correction.

## Design decisions

Reword each passage to describe the enforcement as unconditional and generic (a
`RuntimeError` regardless of environment) rather than quoting
`security_audit.py`'s exact message string verbatim — per the source Plan's Risks
section, the sibling Plan's REQ-001 landed with different wording than originally
anticipated, so this document should not hard-couple its prose to that exact string.

## Alternatives considered

Quoting the sibling Plan's originally-anticipated message text verbatim — rejected: the
Plan's own Risks section already identified this as a risk (message wording differs from
what was originally assumed) and mitigates it by requiring generic, unconditional
phrasing instead.

## Implementation

### Target file

docs/04_mcp_05_02_auth-profiles-and-sandboxing.md

### Procedure

Apply five localized edits to the target document: one module-path correction and four
passage rewordings.

### Method

1. Line 44 (Enforcement Point sentence) — replace:
   ```
   **Enforcement Point:** `agent/repl_health.py::audit_security_defaults()` raises an exception at startup if `security_profile == "production"` and an HTTP server has an empty `auth_token`. It also warns about `shell_sandbox_backend == "none"` and empty `tool.allowed_tools`.
   ```
   with:
   ```
   **Enforcement Point:** `agent/services/security_audit.py::audit_security_defaults()` raises an exception at startup if `security_profile == "production"` and an HTTP server has an empty `auth_token`. It also raises an exception, regardless of environment, if `shell_sandbox_backend == "none"`; it separately warns about empty `tool.allowed_tools`.
   ```
2. Line 72 (`# Development:` code-block comment) — replace:
   ```
   shell_sandbox_backend = "none"    # WARNING at startup; no isolation
   ```
   with:
   ```
   shell_sandbox_backend = "none"    # RuntimeError at startup (regardless of environment); no isolation
   ```
3. Line 80 (Sandbox Backend table, `none` row, "Startup Behavior" column) — replace:
   ```
   | `none` | Development only — no isolation | No | Logs a WARNING; `RuntimeError` in production mode |
   ```
   with:
   ```
   | `none` | Not permitted in any environment — no isolation | No | `RuntimeError` at startup, regardless of environment |
   ```
4. Line 88 (Startup Enforcement bullet list, third bullet) — replace:
   ```
   - If `backend == "none"` in production mode $\rightarrow$ `RuntimeError`.
   ```
   with:
   ```
   - If `backend == "none"` $\rightarrow$ `RuntimeError`, regardless of environment.
   ```

### Details

Edit 1 resolves REQ-001 (module path) and part of REQ-002 (the "It also warns about..."
clause). Edits 2-4 resolve the remainder of REQ-002. None of the five edits touch the
`auth_token` HTTP-enforcement clause in the same Enforcement Point sentence — its
production-conditional behavior is unaffected and remains accurately described, per the
source Plan's Out-of-Scope.

## Compatibility considerations

Documentation-only change; no code, schema, or runtime behavior affected. Brings the
document into agreement with already-landed code behavior — no compatibility risk.

## Security considerations

N/A: this is a documentation accuracy fix. Not fixing it would leave a document that
misleads a reader into believing `shell_sandbox_backend = "none"` is safely usable
outside production, which is itself the security-relevant risk this Plan addresses.

## Rollback considerations

Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan

- `uv run python tools/check_docs_quality.py` — no new structural/formatting issues.
- `uv run python tools/check_docs_structure.py docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` — passes.
- `uv run python tools/check_docs_consistency.py --domain mcp` — no drift reported
  between the reworded passages and `scripts/agent/services/security_audit.py`'s actual
  (now-unconditional) behavior.

## Completion criteria

All four identified passages in `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` no
longer state or imply that `shell_sandbox_backend == "none"` is warning-only outside
production, and the Enforcement Point sentence names the correct module path.

## Out of scope

The `auth_token` HTTP-enforcement clause in the same Enforcement Point sentence (Plan
Out-of-Scope). `docs/04_mcp_04_02_file-write-file-delete-shell.md` (Plan Out-of-Scope,
covered by the sibling Plan's own REQ-003). Any other content in the target file
unrelated to the shell-sandbox-backend passages.

## Documentation

`docs/00_index.md`'s "Document References by Task" table has no row naming
`docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` specifically (per the source Plan's
own Documentation Impact section) — no `docs/00_index.md` update is in scope. This
procedure's own target file IS the documentation being corrected.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the five edits described in Implementation > Method | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | Already implemented — all four passages updated per procedure specification |
| 2 | N/A: no automated test to add (documentation-only change; validation is via doc checkers, see Validation plan) | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | N/A |
| 3 | Run the validation sequence (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_consistency.py --domain mcp`) | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | All checks passed |
| 4 | N/A: no further documentation update needed — this document IS the target of the update, and no `docs/00_index.md` task-scope row names it | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | N/A |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/20260901-104253_risks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260902-103821_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183233
- **Related target files**: `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`
