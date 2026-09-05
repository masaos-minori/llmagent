## Goal
Once Phase 0 clears: remove the profile-based framing from
`docs/00_security_01_architecture-and-trust-boundaries.md`'s
"Local-vs-production behavior" and "Fail-open-vs-fail-closed behavior"
sections, replacing it with the single unconditional Production-grade
policy, while preserving unrelated uses of "local" (filesystem, Git, RAG,
database, process, localhost) (`REQ-004`).

## Scope
- **In-Scope**: `docs/00_security_01_architecture-and-trust-boundaries.md`
  only — the two named sections' tables.
- **Out-of-Scope**: the other 5 target files; unrelated sections of this
  same document (e.g. Audit Logging, Prompt-injection responsibility
  boundaries); `localremoval`'s/`loopbackonly`'s/`mcpauth`'s/`localcleanup`'s
  own implementations.

## Assumptions
- Phase 0 is **not** cleared as of 2026-09-03 (re-confirmed, same status as
  seq 01/02: `localremoval`/`loopbackonly`/`mcpauth` under `plans/`;
  `localcleanup` in `plans/done/` but unexecuted). This document's Procedure
  is Blocked until all four land.
- Re-confirmed 2026-09-03: the "## Local-vs-production behavior" heading
  (originally cited at line 123) is at line 121, and "## Fail-open-vs-
  fail-closed behavior" (originally cited at line 138) is at line 138 — a
  2-line drift on the first, none on the second, both within normal citation
  tolerance and not requiring a Plan correction. Both tables' content
  (`allow_public_bind`, Bearer token requirement, tool safety tiers,
  `approval_github_allowed_repos`, `gitops_push_blocked`, audit redaction,
  approval dry-run; and the fail-open/fail-closed component table) is
  unchanged from the Plan's description.

## Design decisions
- Replace each two-column (Local/Production) table with a single-column
  description of the unconditional Production policy, rather than deleting
  the tables outright — preserves the per-control detail (e.g.
  `allow_public_bind` behavior) as historical/reference detail, now
  described as the system's only behavior.
- Preserve every unrelated "local" mention verbatim (filesystem paths, Git
  operations, RAG local fallback, local database access, local process
  boundaries, `127.0.0.1`/loopback networking) — only the
  Local-vs-Production *runtime security profile* framing is in scope.

## Alternatives considered
- Deleting the two sections entirely instead of rewriting them — rejected:
  the per-control detail they contain (which controls exist, what they
  enforce) remains valuable as a reference of the final, unconditional
  policy; only the profile-based *framing* is obsolete.

## Implementation
### Target file
`docs/00_security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Confirm Phase 0's precondition is met. As of 2026-09-03 it is not — do
   not proceed past this step until it is.
2. Once cleared, rewrite "## Local-vs-production behavior" (~line 121) as a
   single-column description of the final Production-only policy for each
   row currently in the Local/Production table (`allow_public_bind`, Bearer
   token, tool safety tiers, `approval_github_allowed_repos`,
   `gitops_push_blocked`, audit log redaction, approval dry-run) — retitle
   the section to drop the "Local-vs-" framing (e.g. "Production Security
   Policy") once no comparison remains.
3. Rewrite "## Fail-open-vs-fail-closed behavior" (~line 138) similarly: the
   table's "Default"/"Production" columns collapse into the actual final
   behavior per component (`tool_safety_tiers`, `approval_github_allowed_repos`,
   `allowed_dirs`, `allowed_repos`, `allow_public_bind`, MCP tool approval,
   shell command allowlist).
4. Grep the full document for other "local"/"Local" mentions before saving,
   and confirm each remaining one refers to filesystem, Git, RAG, database,
   process, or localhost/loopback networking, not the retired runtime
   profile — leave those untouched.

### Method
Direct `Edit` to `docs/00_security_01_architecture-and-trust-boundaries.md`,
once Phase 0's precondition is confirmed met.

### Details
- Re-verify each row's actual final behavior against `localremoval`'s,
  `loopbackonly`'s, and `mcpauth`'s landed documentation (not their Plan-time
  text) before rewriting — e.g. `allow_public_bind`'s fate depends on
  `loopbackonly`'s actual implementation.
- Preserve the `*Source: ...*` citation lines under each table, updating the
  cited document names only if those documents' own titles change as part of
  the same migration (cross-check `04_mcp_06_16_pre-production-fail-open-checklist.md`
  and `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` still exist
  under those names at execution time).

## Compatibility considerations
N/A: documentation-only, no code compatibility impact. Coordinate with seq
01/02/05's own ADR-004/`adr-index.md`/`04_mcp_06_17` updates in the same
Phase-0-cleared cycle, since all four describe the same final policy.

## Security considerations
None directly — documentation-only. Accuracy matters since this is the
canonical cross-cutting security reference (per Affected areas), but this
document does not implement any control itself.

## Rollback considerations
Single-file edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_security_01_architecture-and-trust-boundaries.md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No structural findings in the changed file |
| `docs/00_security_01_architecture-and-trust-boundaries.md` | Structure validation | `uv run python tools/check_docs_structure.py` | Internal links resolve; Front Matter intact |
| Full document | Manual repository search | Search for remaining Local-profile framing after the edit | No runtime Local-profile behavior described as supported; unrelated "local" uses remain accurate |

## Completion criteria
- Both named sections describe only the final Production-only policy, no
  Local/Production comparison remains (AC-4).
- Every unrelated "local" mention (filesystem, Git, RAG, database, process,
  localhost) remains untouched and accurate.
- Not completable until Phase 0 clears.

## Out of scope
The other 5 target files; unrelated sections of this document;
`localremoval`'s/`loopbackonly`'s/`mcpauth`'s/`localcleanup`'s own
implementations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-04 | 2026-09-04 | Target document already revised by Phase 0 implementations: "Local-vs-production behavior" section retains retired columns as historical record (lines 123-144); "Fail-open-vs-fail-closed behavior" section updated (line 158: `allow_public_bind` → N/A); note added at line 125 confirming `security_profile=local` removal |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-04 | 2026-09-04 | Validation checks passed (see ADR-004 revision record) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document's own target file is the documentation being updated; no separate doc row applies |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Phase 0 not cleared: `localremoval`, `loopbackonly`, `mcpauth` remain under `plans/`; `localcleanup` is in `plans/done/` but its own implementation-procedure document is unexecuted | Yes | 2026-09-04 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260902-143338_adrprodonly_supersede_profile_based_design_docs_sync_references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-093353_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-171632
- **Related target files**: docs/00_security_01_architecture-and-trust-boundaries.md
