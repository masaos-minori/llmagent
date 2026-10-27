## Goal

Replace the stale reference to the removed diff command in ADR-001 Negative Consequences with wording that names only the audit log (`REQ-001`: remove the phrase and state the limit; `REQ-002`: change nothing else in the ADR).

## Scope

- Edit the single Negative Consequences bullet that ends "reviewing a turn relies on the diff command and the audit log".
- Leave every Decision, Invariant, Gate, Approval record and other section unchanged.

## Assumptions

- The audit log is the only review source for a turn (UNK-01, non-blocking); confirm with the repository owner while reviewing the edit. If another mechanism exists, cite it by its formal name instead.
- Step 3a evidence: the phrase occurs once under `docs/`; commit `43cc7c3f1` removed the `/diff` handler; neither `scripts/agent/commands/command_defs_list.py` nor the command registry document has a diff command; the audit-log document defines the per-turn `turn_end` event and the `tool_approval` event.
- Overlap with `plans/20261027-104705_govrev004_adr-verification-evidence-sync.md` (same file, `### Automated Tests` table): compatible, no required order. After either change is applied, re-run `check_adr_preservation.py` against the other.

## Design decisions

- Cite the audit log only, not `/history` (messages only) and not the Git MCP `git_diff` tool (a model-invoked tool, not an operator review command).
- Proposed wording: `There is no human checkpoint for the combined result of a turn; reviewing a turn relies on the audit log, and no command presents the combined result of a turn`.

## Alternatives considered

N/A: the Plan (Design section) already rejected restoring a diff command (out of scope, contradicts the removal).

## Implementation
### Target file

`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure

1. Locate the bullet (`rg -n "reviewing a turn relies on" <target>`).
2. Replace only the clause after the semicolon with the proposed wording; keep the bullet's first clause as it is.

### Method

One exact-string edit.

### Details

- Do not name `/audit` or any removed command: `GV-017` guards removed command names, and the audit log here is the event record, not a command.

## Compatibility considerations

N/A: documentation only; no Decision, Invariant, Gate or Approval text changes, so no Approval Record update is needed.

## Security considerations

N/A: no secret or credential is involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_preservation.py` (expect no ERROR for ADR-001) and `uv run python tools/check_adr_structure.py`.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.
- `uv run python tools/check_docs_consistency.py --domain agent`.

## Completion criteria

- ADR-001 no longer contains "the diff command", and every review mechanism named in Negative Consequences is defined in a current document.
- No Decision, Invariant, Gate or Approval text changed, and the checkers above report no finding.

## Out of Scope

- Adding a diff or review command to the Agent.
- Extending `GV-017` or `tools/check_compat_shims.py` to natural-language mentions.
- ADR-001 verification evidence (`plans/20261027-104705_govrev004_adr-verification-evidence-sync.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the stale clause in Negative Consequences | Pending | — | — | |
| 2 | Run the ADR and documentation checkers named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (replace the stale phrase), `REQ-002` (no other ADR-001 change)
- **Source issue**: issues/20261027-101809_govrev002_adr-001-diff-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-104127_govrev002_adr-001-diff-command.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111358
- **Related target files**: docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md
