## Goal
- Restructure `docs/06_eventbus_01_system-overview.md` to remove implementation details like Event Broker internal data structures and queue maxsize values while explicitly preserving the security model (no-auth premise, network-boundary protection judgment, Agent-integration-unimplemented status).

## Scope
- **In-Scope**: `docs/06_eventbus_01_system-overview.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` exists and its guidance is valid (independently verified)
- Security model statements must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove Event Broker internal data structures that duplicate what readers can derive from code inspection
- Remove fine-grained implementation values like queue maxsize parameters
- Remove shutdown sentinel internal mechanics
- Simplify future auth option enumeration (but keep the fact that auth is currently unimplemented and adding it would require threat-model evaluation)
- Preserve: Event Bus purpose, pub/sub/replay/ack/nack/DLQ overview, independence from Agent runtime, security model, no-auth premise and operational risk, network-boundary protection judgment, SQLite vs in-memory broker role division

## Alternatives considered
- Keeping detailed data structure descriptions but adding a note pointing to source code as canonical
- Converting implementation details to prose descriptions instead of removing them
- Moving detailed broker internals to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_01_system-overview.md`

### Procedure
#### Phase 1: Preparation
1. Read `memo-doc-eventbus-review.md` §「06_eventbus_01_system-overview」keep/remove guidance
2. Analyze current document structure to identify where security-related information is distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove Event Broker internal data structures
   - Replace with high-level description of message flow
2. Remove fine-grained implementation values
   - Delete queue maxsize parameters
   - Delete buffer size specifications
3. Remove shutdown sentinel internal mechanics
   - Delete shutdown signal propagation details
4. Simplify future auth option enumeration
   - Keep: auth is currently unimplemented
   - Keep: adding auth would require threat-model evaluation
5. Preserve security-critical information:
   - Event Bus purpose statement
   - pub/sub/replay/ack/nack/DLQ overview
   - Independence from Agent runtime
   - Security model (no-auth premise)
   - Operational risk of no-auth deployment
   - Network-boundary protection judgment
   - SQLite vs in-memory broker role division

#### Phase 3: Deployment & Verification
1. Confirm security model statements were not silently dropped or weakened
2. Validate internal Markdown links and cross-references
3. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve security model statements during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Security model preservation is critical — this is the single most important constraint in the whole doc set
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Security model statements must survive unchanged

## Security considerations
- Critical: Security model statements must not be weakened during cleanup
- The no-auth premise is the single most important security constraint in the whole doc set
- Network-boundary protection judgment must survive intact
- Agent-integration-unimplemented status must be explicit

## Rollback considerations
- Preserve pre-edit backup of security model sections
- If security statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Security Statements | Manual | All security-model statements preserved |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No exhaustive data structures or queue parameter values remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-172906_require.md
- Source plan: plans/20260807-203426_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-081153
- Related target files: docs/06_eventbus_01_system-overview.md
