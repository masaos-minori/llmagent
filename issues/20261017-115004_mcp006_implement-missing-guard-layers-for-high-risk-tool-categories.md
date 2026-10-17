# Implement missing guard layers for high-risk tool categories

## Priority
Medium

## Summary
Resolve Known Issue MCP-006 by bringing every high-risk MCP server's protection
layers into conformance with the Layered protection model defined in
`security_02_high-risk-tool-common-policy.md`: either implement the missing
command-specific guards, postcondition verification, and audit correlation, or
record in each tool's own document that a given layer is not applicable — then
remove the MCP-006 entry from `governance_03_issue-and-uncertainty-management.md`.

## Background
The Layered protection model (`docs/91_security/security_02_high-risk-tool-common-policy.md`)
defines five protection layers. Every high-risk server implements the common
guard layer (allowlist plus read-only/write gating), but coverage of the
remaining layers is uneven. This discrepancy is already registered as Known
Issue MCP-006 in `governance_03_issue-and-uncertainty-management.md` Part 1
(Area: MCP, Status: open, Severity: Medium). The Known Issue Registration Rule
in `governance_01_documentation-policy.md` requires that such a discrepancy
remain tracked until resolved, so this issue exists to close that ledger entry.

**Source snapshot is historical, not current.** MCP-006's implementation
description was captured at the V22-01 documentation review and reflects the
code state then, not now. Coverage has evolved since: for example,
`scripts/mcp_servers/github/github_service_security.py` now ships command-specific
guards (`_assert_allowed_repo`/`_assert_allowed_path`/`_assert_allowed_branch`,
`_clamp_per_page`) and a configurable audit log (`_write_github_audit_log`) that
post-date the ledger entry. Treat MCP-006 as a starting point to re-audit against
live source, not as a current inventory.

## Problem
High-risk tool categories have uneven protection-layer coverage, and the
implementation state recorded in MCP-006 is a point-in-time snapshot from the
V22-01 review — not current fact (see the staleness note in Background). The
residual problems are:

- Audit correlation is missing or incomplete everywhere: `file-write-mcp`
  writes no audit record, and audit records that exist (including github's, whose
  log line is `{ts} op={op} {fields}`) appear to carry no before/after state or
  approval correlation.
- Postcondition verification is not consistently present or complete: git's
  `repository_state.py` only verifies `git_pull` (checkout is handled elsewhere
  and its Stage 5b TOCTOU re-check is a documented no-op), and other categories
  lack a comparable postcondition check.
- Because MCP-006 is historical, the exact per-category gaps must be re-derived
  from live source rather than trusted from the ledger.

## Reason for Change
MCP-006 was surfaced in the V22-01 documentation review (memo1 review) and remains
open without a resolution owner action. Leaving it open means the policy document continues to describe an
unimplemented gap, and the affected tool categories keep a real defense-in-depth
hole: unintended writes/deletes/executions are neither post-verified nor
correlated to their approving call. Resolving it either restores the missing
protection or formally documents why a layer does not apply, which is the exact
resolution path the Known Issue template prescribes.

## Implementation Intent
Work per tool category. For each of git, mdq, file-write, file-delete, shell,
github, and any other high-risk server, decide for every Layered protection
layer whether to (a) implement the missing layer, or (b) record in that tool's
own document that the layer is not applicable. Prefer the minimal change that
achieves conformance: reuse the existing git postcondition-verification pattern
only where it generalizes (it does not verify checkout and its TOCTOU re-check
is a no-op, so fill those gaps rather than copying it wholesale); add audit
before/after state plus approval correlation where a server currently omits them. Do not redesign the common guard or the
five-layer model; only close the per-category gaps. Once every category is
either implemented or documented-as-not-applicable, remove the MCP-006 entry
from the active inventory.

## Target Files or Areas
- `scripts/mcp_servers/{git,file,shell,github,mdq}/` (high-risk servers; `file-write-mcp` and `file-delete-mcp` both live under `scripts/mcp_servers/file/`)
- `scripts/mcp_servers/git/repository_state.py` (existing postcondition-verification reference)
- Each high-risk tool's own document under `docs/22_mcp/` describing its current layer coverage
- `docs/91_security/security_02_high-risk-tool-common-policy.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1, MCP-006 removal)
- Related: `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`, `docs/22_mcp/mcp_04_05_git.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

## Required Changes
- For each high-risk tool category, enumerate which of the five Layered
  protection layers are implemented, missing, or not applicable.
- For missing command-specific guards, implement them or document them as not
  applicable, consistent with the model's intent. github already ships guards
  (`github_service_security.py`); assess whether they are sufficient rather than
  assuming they are absent, and focus on categories the re-audit finds lacking
  (e.g. file-write).
- Add postcondition verification to categories that lack it, reusing the git
  `repository_state.py` pattern where it applies.
- Ensure every high-risk server's audit record captures before/after state and
  correlates to the approving call; add an audit record to `file-write-mcp` if
  it currently writes none.
- Update each tool's own document to reflect its current layer coverage so the
  policy no longer needs to defer to "see each tool's own document".
- Remove the MCP-006 entry from `governance_03_issue-and-uncertainty-management.md`
  Part 1 once every category is resolved.

## Constraints
- Preserve the common guard layer (allowlist + read-only/write gating) exactly as
  defined; do not weaken or remove any existing guard.
- Do not change the five-layer model or its layer definitions.
- Where approval is an Agent-side (client) concern rather than a server-checked
  gate (Git MCP is documented this way in
  `security_02_high-risk-tool-common-policy.md`), approval correlation cannot be
  produced server-side; document that layer as not applicable instead of forcing
  a server-side audit field.
- Postcondition verification and audit additions must not change the allowed
  operations' observable success/failure semantics for legitimate calls.
- Keep changes scoped to high-risk servers and their docs; do not touch
  unrelated servers.

## Acceptance Criteria
- Every high-risk tool category has each of the five Layered protection layers
  either implemented or explicitly documented as not applicable in that tool's
  own document.
- file-write has command-specific guards implemented or documented as not
  applicable; github's existing guards are assessed and any remaining gaps are
  closed or documented as not applicable.
- Every high-risk server's audit record captures before/after state where the
  server can produce it, and correlates to approval where approval is a
  server-checked gate; where approval is Agent-side (e.g. Git MCP) that aspect is
  documented as not applicable. `file-write-mcp` writes an audit record.
- `docs/91_security/security_02_high-risk-tool-common-policy.md` no longer
  describes an open coverage gap.
- The MCP-006 entry is removed from `governance_03_issue-and-uncertainty-management.md`.

## Testing Expectations
- Unit tests for any newly implemented command-specific guards and postcondition
  verification (including negative cases that exercise the guard).
- Tests asserting audit records contain before/after state and approval
  correlation for the affected servers.
- Regression tests confirming legitimate calls still succeed with unchanged
  success/failure semantics.
- Documentation-consistency check (`governance_04_documentation-checks.md`,
  rule GV-022 family where applicable) passes.

## Documentation Impact
Documentation must be updated: each high-risk tool's own document must state its
current Layered protection layer coverage (implemented vs. not applicable), and
`security_02_high-risk-tool-common-policy.md` must no longer describe an open
gap. Remove the MCP-006 ledger entry on resolution.

## Out of Scope
- Redesigning the Layered protection model or its five layers.
- Adding new high-risk tool categories beyond those already in scope.
- Changes to the common guard layer, allowlists, or denylists.
- Non-high-risk MCP servers.

## Dependencies
- `docs/91_security/security_02_high-risk-tool-common-policy.md` defines the
  five-layer model this issue conforms to; read it before implementing.

## Unresolved Questions
- MCP-006's implementation description is a V22-01 snapshot; code has evolved
  (github added command-specific guards and a configurable audit log). Re-audit
  current coverage against live `scripts/` before deciding implemented vs.
  not-applicable per category.
- Which specific layers are genuinely not applicable per category versus merely
  unimplemented? This requires reading each tool's current implementation and
  deciding per the model's intent.
- Whether `file-write-mcp` should share the audit-record schema of the other
  servers or define its own; confirm against `mcp_02_03_audit-logging-and-errors.md`.

## AI Implementation Instruction
Re-derive each category's actual current coverage from live code first; do NOT
treat MCP-006's implementation description as current. github-mcp already ships a
security module (`scripts/mcp_servers/github/github_service_security.py`) with
command-specific guards and a configurable audit log that post-date the ledger
entry, so assume coverage has changed since V22-01. For each category, implement
the missing layer or document it as not applicable — never both, and never leave
a layer unaddressed. Reuse the git postcondition-verification pattern only where
it generalizes, filling its known gaps (no checkout verification, no-op TOCTOU
re-check) rather than copying it. Keep changes minimal and scoped to high-risk
servers and their docs. Do not modify the common guard, the five-layer model, or
non-high-risk servers. After every category is resolved, remove the MCP-006
entry from `governance_03_issue-and-uncertainty-management.md` and report which
layers were implemented versus documented-as-not-applicable per category.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261017-115004
- **Related target files**: `scripts/mcp_servers/{git,file,shell,github,mdq}/` (file-write-mcp and file-delete-mcp both under `scripts/mcp_servers/file/`), `docs/91_security/security_02_high-risk-tool-common-policy.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
