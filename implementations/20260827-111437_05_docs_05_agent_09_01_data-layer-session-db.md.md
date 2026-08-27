## Goal

Correct the stale fetch()-decryption "Known Limitations"/description notes in
`docs/05_agent_09_01_data-layer-session-db.md` (REQ-006), per
`plans/20260826-120102_plan.md`.

## Scope

- In scope: the "Role of `session_diagnostics`" bullet (line 74) and the "Known
  Limitations" bullet (line 97).
- Out of scope: any other section of this document; any code change.

## Assumptions

- `scripts/agent/diagnostic_store.py`'s `fetch()` (verified 2026-08-27, lines
  174-206) already implements Fernet decryption, wrapped in a try/except that
  leaves ciphertext as-is and logs a warning on failure — this was implemented by
  the already-archived `plans/done/20260818-170728_plan.md`; the code is correct,
  only these two doc lines are stale.

## Design decisions

- Replace both stale lines with text describing the current, verified behavior:
  decryption is implemented; ciphertext is preserved and a warning is logged if
  decryption fails (e.g. wrong/rotated key) — per REQ-006's exact specification.
- Do not overstate robustness — the fallback behavior (leave ciphertext as-is on
  failure) is itself a real, still-existing limitation worth keeping in the
  document, just accurately described rather than described as "not implemented at
  all".

## Alternatives considered

- Deleting the "Known Limitations" bullet entirely (since the core decryption gap
  is fixed) was considered and rejected — the decrypt-failure fallback behavior
  (silently leaving ciphertext, logging only a warning) is still worth documenting
  as a residual limitation, just with corrected framing.

## Implementation
### Target file
`docs/05_agent_09_01_data-layer-session-db.md`

### Procedure
1. Rewrite line 74's "Can be encrypted with `encrypt=True`, but `fetch()` does not
   implement decryption." to reflect current behavior.
2. Rewrite line 97's "Encrypted rows in `session_diagnostics` are not decrypted
   during `fetch()`." to reflect current behavior, or remove it if REQ-006's
   corrected text at line 74 already fully covers it (avoid duplicating the same
   fact in two places with different wording — pick one location and
   cross-reference from the other if needed).
3. Run `uv run python tools/check_docs_consistency.py --domain agent` (or the
   applicable domain check per `rules/toolchain.md`).

### Method
Direct text edits (Edit tool) — two bullets, in two different sections of the same
document.

### Details
Current text (verified 2026-08-27):
- Line 74: `- Can be encrypted with \`encrypt=True\`, but \`fetch()\` does not
  implement decryption.`
- Line 97 (under "## Known Limitations"): `- Encrypted rows in
  \`session_diagnostics\` are not decrypted during \`fetch()\`.`

Replace line 74 with text stating: content can be encrypted with `encrypt=True`;
`fetch()` decrypts Fernet-encrypted content automatically, leaving ciphertext as-is
and logging a warning if decryption fails (e.g. wrong/rotated key).

Replace or remove line 97's "Known Limitations" bullet: if kept, narrow it to state
the actual residual limitation (decrypt failures are silently tolerated —
ciphertext is returned unchanged with only a warning logged, not raised as an
error) rather than claiming decryption is unimplemented.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is affected.

## Security considerations

- The corrected text must not claim stronger guarantees than the code provides —
  specifically, keep documenting that a decrypt failure returns ciphertext silently
  (only a warning is logged, not surfaced to the caller) since that is itself a
  real, security-relevant behavior an operator should know about.

## Rollback considerations

- Two-bullet text revert via `git diff`/`git checkout -- <path>`; no other document
  or code depends on this exact wording.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_09_01_data-layer-session-db.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain agent` | Passes; no new findings |

## Completion criteria

- Neither the "Role of `session_diagnostics`" bullet nor the "Known Limitations"
  bullet describes `fetch()` as failing to decrypt.
- The residual decrypt-failure-tolerance behavior remains documented, accurately.

## Out of scope

- Any other section of this document.
- Any code change to `DiagnosticStore`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite line 74's stale claim | Pending | — | — | |
| 2 | Rewrite or remove line 97's stale "Known Limitations" bullet | Pending | — | — | |
| 3 | Run `uv run python tools/check_docs_consistency.py --domain agent` | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20260821_06_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-120102_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-111437
- **Related target files**: `docs/05_agent_09_01_data-layer-session-db.md`
