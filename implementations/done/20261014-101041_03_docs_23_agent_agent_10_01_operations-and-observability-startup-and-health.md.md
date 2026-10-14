## Goal

Rewrite the "Secret Masking in MCP Subprocess Failure Reports" chapter of `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` to state the final set of masked secret forms (REQ-007) and remove the "only `key=value` is recognized" limitation note.

## Scope

**In:**
- Edit the chapter at lines 96–98 of `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`: replace the sentence stating only `key=value` is recognized with an accurate description of the final masked set, and remove the clause that other shapes (e.g. `Authorization: Bearer ...`) are not masked.

**Out:**
- No source-code change (`scripts/agent/secrets_masker.py`) — owned by the paired doc.
- No test authoring.
- No changes to any other chapter.

## Assumptions

1. The final masked set is exactly the three families defined in the Plan's Design section: `key=value` (unchanged), `Authorization: <scheme> <token>`, and standalone `Bearer <token>` — once the paired source doc is executed.
2. The chapter currently (line 98) states only `key=value` is recognized and that an `Authorization: Bearer ...` header is "not masked" — this is the limitation note to remove.
3. The doc must not claim the masked set is complete until the source change (paired doc `20261014-101041_01_scripts_agent_secrets_masker.py.md`) is implemented; word the chapter to describe the implemented set without overclaiming beyond the scoped shapes.

## Design decisions

- Replace the single limitation sentence with a concise enumeration of the three masked forms, keeping the surrounding context (stderr tail passing through `agent/secrets_masker.py`) intact.
- Keep the chapter's tone and structure consistent with neighboring chapters; do not add new subsections.

## Alternatives considered

N/A: documentation-only, single-chapter edit.

## Implementation

### Target file

`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

Edit the "Secret Masking in MCP Subprocess Failure Reports" chapter (currently line 96–98). Replace the limitation sentence with an accurate statement of the final masked set. Do not touch other chapters.

### Method

Locate the chapter heading `### Secret Masking in MCP Subprocess Failure Reports` and its body paragraph. Replace the existing paragraph (which ends with "...other shapes (for example an `Authorization: Bearer ...` header) are not masked.") with a paragraph that enumerates the three masked forms and omits any "not masked" limitation.

### Details

Before (current, line 98):
> When an MCP subprocess fails to start, the tail of its stderr is included in the startup failure report, and a failed first start attempt is logged. Both pass through `agent/secrets_masker.py`, which replaces values written as `key=value` for key names such as `password`, `api_key`, `secret` and `token` (case-insensitive) with a masked form. Only that `key=value` form is recognized; other shapes (for example an `Authorization: Bearer ...` header) are not masked.

After:
> When an MCP subprocess fails to start, the tail of its stderr is included in the startup failure report, and a failed first start attempt is logged. Both pass through `agent/secrets_masker.py`, which masks three shapes (case-insensitive): `key=value` values for key names such as `password`, `passwd`, `pwd`, `api_key`, `apikey`, `secret` and `token`; `Authorization:` header lines such as `Authorization: Bearer <token>` or `Authorization: Basic <token>` (the token is masked, the scheme keyword is preserved); and standalone `Bearer <token>` tokens that appear without an `Authorization:` prefix.

The after-text must match the behavior implemented by the paired source doc; if the executed masked set differs, align the chapter to the code rather than to this placeholder wording.

## Compatibility considerations

This doc is the canonical source for the secret-masking description in the Agent operations domain; updating it keeps operator-facing documentation aligned with the expanded masking behavior. No cross-document references to the old limitation note were found that would need updating.

## Security considerations

An inaccurate "not masked" note misleads operators into thinking bearer headers are unprotected when they now are (or vice versa); the rewrite must state exactly what is masked so operators are not given a false sense of either over- or under-protection.

## Rollback considerations

N/A: revert the commit to restore the prior chapter text.

## Validation plan

- Run the documentation quality checker named in `routing.md`: `uv run python tools/check_docs_quality.py` — confirm it passes (structural/formatting rules: headings, tables, code fences, Migration Notes placement).
- Manual review: confirm the chapter enumerates the three masked forms and no "not masked" limitation remains.

## Completion criteria

- The "Secret Masking in MCP Subprocess Failure Reports" chapter states the final masked set (`key=value`, `Authorization: <scheme> <token>`, standalone `Bearer <token>`).
- The "only `key=value` is recognized / other shapes not masked" limitation note is removed.
- `uv run python tools/check_docs_quality.py` passes.

## Out of scope

- Source-code changes — owned by the paired doc.
- Test authoring.
- Other chapters of the document.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-14 | 2026-10-14 | REQ-007: rewrote the secret-masking chapter with the three masked forms |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only change; no tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-14 | 2026-10-14 | `uv run python tools/check_docs_quality.py` passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document is the documentation change |

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
- **Requirement ID**: `REQ-007` — the chosen masked shapes are documented in `agent_10_01` and the limitation note is removed
- **Source issue**: issues/20261013-162325_agmask01_mask-alternate-secret-shapes-in-the-agent-secret-masker.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-093347_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-101041
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md
