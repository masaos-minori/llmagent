## Goal
- Register one `design-gap` Known Issue entry (`AGENT-001` (new)) in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 `### Active Items` for the two unused agent-side EventBus client modules, per the Plan's REQ-001 (register the governance decision for the unused modules).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The ID `AGENT-001` is available: Part 1 currently holds only `MCP-001`–`MCP-005` and `SHARED-002`, and no `AGENT-*` or `EVENTBUS-*` heading exists anywhere in the document (verified 20261120). If a sibling adrchk item inserts an `AGENT-*` or `EVENTBUS-*` entry before this procedure runs, re-run Step 1's searches and take the next free number in the `AGENT-*` group instead.
- The recorded decision is retention pending a maintainer keep-versus-remove decision; this procedure writes no approval statement (Plan Assumptions; the source Issue forbids fabricating one).
- Part 1 has no closing-summary sentence (`rg "No other active"` is zero-hit), and `tools/check_issue_inventory_conformance.py` skips its closing-summary check when none exists — adding an entry does not require creating one.

## Design decisions
- One entry covers both modules: the `### Unused Features` rule states closely related items share one entry, and both modules share one layer, one unused status, and one adrrev002 UNK-02 question.
- Area `Agent` (code ownership and describing docs are Agent-side) gives the ID `AGENT-001`; the Active Items ordering convention puts the `AGENT-*` group before `MCP-*`, so the entry is inserted directly before `#### MCP-001`.

## Alternatives considered
- Area `EventBus` / `EVENTBUS-001`: rejected in the Plan's Design section — the modules live under `scripts/agent/` and are described by the Agent docs.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Re-run the pre-edit searches and record their zero-hit output: `rg -n "^#### (AGENT|EVENTBUS)-" docs/00_governance/governance_03_issue-and-uncertainty-management.md` and `rg -n "eventbus_subscriber|eventbus_topic_admin_client" docs/00_governance/governance_03_issue-and-uncertainty-management.md` (both MUST be zero-hit; a hit means an intervening sibling entry exists — re-derive the ID per Assumptions).
2. Insert the `#### AGENT-001` entry (the 17-field block in Details) after the `### Active Items` ordering-convention paragraph and before the `#### MCP-001` heading. No other Part 1 or Part 2-4 content changes.

### Method
- Plain text edit of the Markdown file; no generated or guarded block is touched (the entry is hand-maintained inventory content). Entry field labels, the `#### <ID>` heading form, and the mixed `- **Status**:` style follow the neighboring `MCP-001` entry so `tools/check_issue_inventory_conformance.py`'s field-count (17 per Part 1 entry) and vocabulary checks hold. All entry prose is present-tense (Current-Specification-Only policy).

### Details
Insert exactly this block (17 fields):

```markdown
#### AGENT-001

- **ID:** AGENT-001
- **Title:** Two unused agent-side EventBus client modules are listed as current libraries without a recorded keep-versus-retire decision
- **Status**: open
- **Severity:** Low
- **Area:** Agent
- **Type:** design-gap
- **Source:** adrchk023 EventBus client modules verification, import scan over `scripts/`, `tools/`, `deploy/`, `config/`, `.github/`
- **Owner:** Repository owner
- **First Found:** adrchk023 EventBus client modules verification
- **Target:** `docs/23_agent/agent_02_runtime-architecture.md`
- **Related:** None
- **Summary:** `scripts/agent/eventbus_subscriber.py` and `scripts/agent/eventbus_topic_admin_client.py` are imported only by their own unit tests while documents present them as current client libraries; the Unused Features rule requires the keep-versus-retire decision to be registered.
- **Current Description:** `docs/23_agent/agent_02_runtime-architecture.md` `EventBus Client Modules` and the `docs/23_agent/agent_13_reference-api-generated.md` AUTO-GENERATED block describe `EventBusSubscriber` and `EventBusTopicAdminClient` as current client-side libraries for the Event Bus HTTP API.
- **Observed Implementation:** Only `tests/agent/test_eventbus_subscriber.py` and `tests/agent/test_eventbus_topic_admin_client.py` import the modules; no `scripts/` runtime component imports them; `registry/manifests/agent_api.yaml` lists their public classes.
- **Impact:** The modules read as a supported API, and the governance decision to keep or retire them is unrecorded.
- **Recommended Action:** The maintainer decides whether the modules are retained for the planned future EventBus integration or retired through a follow-up Plan. Recorded pending that decision; no approval is written here.
- **Resolution Target:** maintainer decision recorded in this entry; retention closes with the future EventBus integration Plan, retirement runs through a follow-up Plan
```

## Compatibility considerations
- Follows the open-pending-decision entry pattern of `SHARED-002` and `MCP-005` (`Recorded pending that decision … no approval is written here`); no ADR decision, invariant, Blocking value, or authority edge changes, so no governance_01/governance_05 approval record is triggered.

## Security considerations
- N/A: documentation-only inventory entry; no secrets, code, or config touched.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_issue_inventory_conformance.py` — vocabulary, 17-field count, and reference integrity pass for the new entry.
- `uv run python tools/check_known_deviation_sync.py` — the new `AGENT-001` ID resolves to its one heading; no dangling citation.
- `uv run python tools/check_needs_confirmation_inventory.py`; `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py` — no findings.
- `git diff --name-only` — this procedure touches exactly the target file.

## Completion criteria
- Part 1 contains exactly one `#### AGENT-001` entry, ahead of `#### MCP-001`, with all 17 fields, Type `design-gap`, Status `open`, naming both modules; all named checkers pass; no other file changed.

## Out of Scope
- Deleting or editing the modules or their tests; edits to `docs/23_agent/agent_02_runtime-architecture.md`, `docs/23_agent/agent_13_reference-api-generated.md`, `registry/manifests/agent_api.yaml`; any other governance_03 Part or entry; any approval statement.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in the Validation plan (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (register the design-gap entry in the governance inventory)
- **Source issue**: issues/20261117-123023_adrchk023_eventbus-client-modules.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-212359_adrchk023_eventbus-client-modules.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-213832
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
