## Goal

Remove the stale numeric sub-config count ("7") from `docs/agent_01_system-overview.md` line 52, per `skills/DESIGN.md` "No implementation counts" — replace with prose that does not drift when a sub-config is added or removed.

## Scope

- Correct the table cell on line 52 in `docs/agent_01_system-overview.md`
- No other files are modified in this row

## Assumptions

- The current wording on line 52 is: `\| \`AgentConfig\` \| 7 sub-configs, hot-reload \|`
- This is a prose-only change — no structural or functional change.
- Per `skills/DESIGN.md` "No implementation counts", removing the numeric count rather than replacing it with another number is the more durable fix.

## Design decisions

- Removing the numeric count entirely rather than replacing it with "9": these locations are further from the actual field list and have already drifted independently to three different wrong values (7, 7, 8-per-the-Issue), so removing the countable claim is the more durable fix.

## Alternatives considered

- Replacing "7" with "9" — rejected: the count will drift again the next time a sub-config is added or removed; per `skills/DESIGN.md` "No implementation counts", dropping the countable claim is the more durable fix.

## Implementation

### Target file

`docs/agent_01_system-overview.md`

### Procedure

Remove the stale numeric sub-config count from the AgentConfig table cell.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `docs/agent_01_system-overview.md` line 52.
2. Correct the table cell on line 52:
   - Change: `\| \`AgentConfig\` \| 7 sub-configs, hot-reload \|`
   - To: `\| \`AgentConfig\` \| Composite sub-configs, hot-reload \|`

### Details

```markdown
# Line 52: correct the table cell:
# Before:
| `AgentConfig` | 7 sub-configs, hot-reload |

# After:
| `AgentConfig` | Composite sub-configs, hot-reload |
```

## Compatibility considerations

- No production code depends on the specific prose text being changed.
- `tools/check_docs_consistency.py --domain agent` must continue to pass unmodified.

## Security considerations

- No security impact. This is a documentation correction, not a security boundary change.

## Rollback considerations

- Reverting this change restores the original table cell. If needed later, the table cell should be corrected again to match the current state of the referenced dataclass.

## Validation plan

- Documentation consistency: run `uv run python tools/check_docs_consistency.py --domain agent` against the three modified `docs/05_agent_*.md` files.
- Manual proofreading: verify the edited sentence reads correctly and does not introduce broken English or orphaned punctuation.

## Completion criteria

- Line 52 no longer states a numeric sub-config count.
- All existing documentation consistency checks pass without modification.
- No new broken-link/drift findings introduced.

## Out of scope

- Changes to `scripts/*.py` — covered by separate rows (REQ-001, REQ-002, REQ-003).
- Modifying any other file — covered by separate rows (REQ-001, REQ-002, REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove stale numeric sub-config count from docs/agent_01_system-overview.md | Completed | 20260917-202150 | 20260917-202150 |  |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-202150 | 20260917-202150 |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-103349_mcpagent09_routing-discovery-test-config-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-131528_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-231122
- **Related target files**: docs/agent_01_system-overview.md