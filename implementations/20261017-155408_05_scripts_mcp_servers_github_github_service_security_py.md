# Implementation Procedure — `scripts/mcp_servers/github/github_service_security.py`

## Goal

Extend `github-mcp`'s audit log to include before/after state and approval correlation
(`REQ-004`), and assess whether its existing command-specific guards are sufficient
(`REQ-002`).

## Scope

Modify only `scripts/mcp_servers/github/github_service_security.py`. Extend
`_write_github_audit_log` to add before/after + correlation fields; assess the existing
guards (`_clamp_per_page`, `_assert_allowed_repo`, `_assert_allowed_path`,
`_assert_allowed_branch`) and close any remaining gap or document it.

## Assumptions

- `_write_github_audit_log(self, op, **kwargs)` is at line 107; format is
  `{ts} op={op} {fields}`.
- Unlike the file servers, this helper raises `GitHubAuditError` on write failure (empty
  path → skip silently). Preserve that contract unless the schema requires otherwise.
- Guards already exist and were confirmed present during plan verification.

## Design decisions

- Extend the `fields` portion of the record with before/after identifiers and an
  approval-correlation field; keep the leading `{ts} op=` prefix.
- Assess each existing guard against REQ-002; only add guards where a genuine gap is
  found, otherwise document as implemented.

## Alternatives considered

- Rewriting the audit format: rejected — extend in place to preserve consumers.
- Moving audit to a shared base: out of scope for this row (other servers are separate rows).

## Implementation

### Target file

`scripts/mcp_servers/github/github_service_security.py`

### Procedure

1. Read `_write_github_audit_log` (107–128) and its callers to learn available kwargs.
2. Before/after + approval-correlation fields: pass them from callers (or derive inside
   the helper) and include them in the `fields` join.
3. Assess guards `_clamp_per_page` (57), `_assert_allowed_repo` (62), `_assert_allowed_path`
   (80), `_assert_allowed_branch` (130) for completeness; add a guard only if a concrete
   gap exists, else mark implemented in the tool doc (separate row).

### Method

- Modify the `record` f-string at line 121 to append the new fields.
- Do not change the raise/skip behavior unless the schema doc (separate row) dictates it.

### Details

- Before/after: e.g. target repo/path identity before vs. after the operation.
- Do not log sensitive payloads (issue/pr/body contents).

## Compatibility considerations

Trailing fields added to the audit line; leading prefix preserved. Confirm consumers of
the `{ts} op={op} {fields}` shape tolerate extra fields.

## Security considerations

Before/after are identifiers only. Preserve the existing raise-on-failure contract
(unless the shared schema changes it in its own row); audit failures currently propagate
for github, which is a deliberate, separate design.

## Rollback considerations

Revert the commit to `github_service_security.py`.

## Validation plan

- Assert the github audit record contains before/after + correlation fields.
- Guard-sufficiency: negative tests exercising existing guards still reject disallowed
  repo/path/branch.
- Command: `uv run pytest tests/mcp_servers/github/ -q`.

## Completion criteria

github audit records carry before/after + correlation; existing command guards cover the
required surface (gaps closed or documented).

## Out of scope

Other servers' guards, the audit schema doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend github audit log; assess guards | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: tool doc is a separate row |

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
- **Requirement ID**: `REQ-004` (audit before/after + correlation); `REQ-002` (command-guard
  sufficiency)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `scripts/mcp_servers/github/github_service_security.py`
