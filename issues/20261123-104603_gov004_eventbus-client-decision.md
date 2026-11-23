# Decide the fate of the unused EventBus client modules and the producer/consumer model

## Priority
Medium

## Summary
Two agent-side EventBus client modules have no runtime importer while documents present them as current libraries, and the EventBus producer/consumer model is undefined. Record the maintainer's keep-or-retire and integration decisions and align the documents.

## Background
Source: governance Known Issue AGENT-001 (Low), Needs Confirmation NC-003 (Medium), and the pending ledger entries AAL-006 to AAL-010 and AAL-029. Evidence (`Explicit in code`, by `rg` over `scripts/`, `tools/`, `deploy/`, `config/`, `.github/`): `scripts/agent/eventbus_subscriber.py` and `scripts/agent/eventbus_topic_admin_client.py` exist and no other file in those directories references them. The inventory states that only their unit tests import them, that `docs/23_agent/agent_02_runtime-architecture.md` and the generated `agent_13` block describe them as current client libraries, and that `registry/manifests/agent_api.yaml` lists their classes. ADR-006 Decision item 14 and the ADR-013 Caller model status state that no producer or consumer is named and the integration timing is undecided; the first publisher or consumer client activates ADR-013 `Review Triggers` item 1.

## Problem
The modules read as a supported API with no recorded keep-versus-retire decision, and the model they would serve is undefined.

## Reason for Change
Unused code presented as a current API misleads readers and the manifest.

## Implementation Intent
The maintainer decides whether the modules are retained for the planned integration or retired, and which component defines producers and consumers and when. The documents and, if retired, the code follow the decision (retirement through a follow-up Plan).

## Target Files or Areas
- `docs/23_agent/agent_02_runtime-architecture.md`
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` and `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
- If retired: `scripts/agent/eventbus_subscriber.py`, `scripts/agent/eventbus_topic_admin_client.py`, their two tests, `registry/manifests/agent_api.yaml`, and the generated reference docs
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (AGENT-001, NC-003)

## Required Changes
- Re-run the import scan, including `tests/`, before any change.
- Record the maintainer decision in AGENT-001 and in ADR-006 item 14.
- If retired, remove the modules, tests, manifest and generated entries through a Plan; if retained, state in the documents that they are not wired into the runtime yet.
- Remove AGENT-001 and NC-003 from the inventory with evidence.

## Constraints
- Retirement runs through a Plan; the decision and every approval are the maintainer's.

## Acceptance Criteria
- [ ] The keep-versus-retire decision and the producer/consumer decision are recorded.
- [ ] The documents match the decision and the manifest lists no retired class.
- [ ] AGENT-001 and NC-003 are removed from the inventory.

## Testing Expectations
`rg` shows no remaining importer of a retired module; manifest and docs checkers pass; the full test suite passes if code is removed.

## Documentation Impact
Yes: `agent_02`, ADR-006, ADR-013, and the governance inventory.

## Out of Scope
- Implementing the EventBus integration itself.

## Dependencies
- N/A: none open. The ledger entries for ADR-006 and ADR-008 are handled in `issues/20261123-104604_gov005_adr-approval-ledger.md`.

## Unresolved Questions
- `不明`: retain or retire the two modules.
- `不明`: the component that defines producers and consumers, and the integration timing.

## AI Implementation Instruction
Re-run the import scan first and stop for the decision. Do not write approval text, and do not retire code without a Plan.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-104603
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `scripts/agent/eventbus_subscriber.py`, `scripts/agent/eventbus_topic_admin_client.py`, `registry/manifests/agent_api.yaml`
