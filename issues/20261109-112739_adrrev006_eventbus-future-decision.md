# Record the EventBus keep decision and its producer/consumer model, and decide ADR-004 Decision Group 7

## Priority
High

## Summary
Record in the ADRs the maintainer's decision that the EventBus service is kept (it is planned to be integrated into the system, so it is not retired), document its intended producers and consumers, and obtain a decision on whether ADR-004 Decision Group 7 (partial availability of non-mandatory components) stays applicable.

## Background
- Source: `memo-issue.md` item H-08, re-checked against current source on 2026-11-09.
- `Explicit in code`: the only EventBus publisher in the repository, `scripts/agent/eventbus_client.py`, has no production importer (see the Agent-side coupling issue in this batch). `Documentation only`: `docs/24_eventbus/eventbus_01_system-overview.md` states that the Agent runtime neither publishes to nor subscribes from the EventBus. The service still maintains Bearer authentication with several roles, topic-authorization generations with TTL, an outbox, DLQ sweeps, and replay.
- `Documentation only`: ADR-004 Group 7 and INV-09 allow a non-mandatory component to be disabled on an availability failure. The memo states that every MCP server is mandatory today, so Group 7 applies to nothing. `Needs confirmation`: the current mandatoriness value for each server. `Explicit in code`: the registry is `scripts/shared/component_mandatoriness.py` (also read by `scripts/shared/mcp_config.py`); `agent_08_04_configuration-mcp-approval-obs.md` is documented as generated from it.
- Memo claim not confirmed: "the EventBus is missing from the `security_01` threat model". `docs/91_security/security_01_architecture-and-trust-boundaries.md` mentions the EventBus; `Needs confirmation` whether it appears in the trust-boundary diagram and threat table.
- Related archived issues under `issues/done/`: `agent001_agent-startup-graceful-disable-path-for-non-required-subprocess-mcp-servers`, `nc041_resolve-the-github-mcp-server-required-classification-disagreement`.

## Problem
- Every EventBus feature must be secured, documented, and reviewed, yet no component in the repository uses it; effort spent on EventBus hardening may be wasted, and a review cannot tell whether "unused" is intentional.
- Group 7 and INV-09 describe behavior that no current configuration triggers, so the specification cannot be verified in practice and may drift silently.

## Reason for Change
- Two EventBus hardening issues in this batch (authorization hardening and configuration/observability specs) are substantial and are conditional on the decision here; deciding first avoids rework.
- This is a maintainer decision, not an implementation task; it is time-sensitive only because it gates that work.

## Implementation Intent
Record an explicit, approved decision for both topics in the ADRs, with approvers and dates, so that later work either strengthens features with a real purpose or removes them entirely. This issue produces decisions and follow-up issues, not code.

## Target Files or Areas
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_01_index.md`
- `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/24_eventbus/eventbus_01_system-overview.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
- Follow-up issues under `issues/` for the chosen options

## Required Changes
- Decide the EventBus:
  - Decided by the maintainer on 2026-11-09: keep the service (planned future integration). Document in ADR-006 and ADR-013 the intended producers and consumers, or state explicitly that they are not yet defined and which component will define them, and add the EventBus to the `security_01` threat model and trust-boundary diagram if absent. Retirement is closed.
- Decide Group 7:
  - Option A, evaluate the mandatoriness of each server (for example, make `web_search` non-required) and add tests for partial availability.
  - Option B, declare Group 7 inapplicable in ADR-004 until a non-required server exists.
- Record each decision with approvers and dates, per the ADR process and `rules/coding.md` "Explicit sign-off gates" (the sign-off record is a maintainer statement).

## Constraints
- The EventBus keep decision is given by the maintainer (instruction of 2026-11-09). The Group 7 decision must still be made by a maintainer; the implementer must not choose it or write an approval record on their behalf.
- Any decision touching ADR-004 follows the ADR amendment process and the authority model (`check_adr_authority.py`).
- A non-mandatory server decision interacts with the posture-failure issue in this batch (a non-required server must still abort on a posture failure).

## Acceptance Criteria
- Both decisions are recorded in ADRs with approval records (approver, date, scope).
- Follow-up issues exist for the chosen options, and dependent issues in this batch are updated or closed.
- `check_adr_authority.py`, `check_adr_structure.py`, and `check_docs_consistency.py --domain eventbus` pass.

## Testing Expectations
- Documentation-only unless Group 7 option A is chosen; in that case the follow-up issue defines the partial-availability tests. Run the documentation checkers listed above.

## Documentation Impact
- ADR-006, ADR-013, ADR-004 (Group 7 outcome), the ADR index, and `security_01` change: state intent, the producer/consumer model (or its explicit absence), and failure behavior.

## Out of Scope
- Implementing deletion, hardening, or partial-availability tests (follow-up issues).
- Changing EventBus runtime behavior in this issue.

## Dependencies
- Depends on: a maintainer decision on Group 7 (external); the EventBus keep decision is already given.
- Blocks: `issues/20261109-112952_adrrev010_eventbus-authz-harden.md` (EventBus authorization hardening) and `issues/20261109-113152_adrrev014_eventbus-spec-gaps.md` (EventBus specification gaps).
- Related: the Agent-side EventBus coupling issue `issues/20261109-112538_adrrev002_agent-eventbus-coupling.md` (the caller model documented here must be consistent with its outcome).

## Unresolved Questions
- Group 7 is still undecided: option A (evaluate the mandatoriness of each server and add partial-availability tests) or option B (declare Group 7 inapplicable until a non-required server exists) (maintainer decision; `不明`). Current fact (`Explicit in code`): every server in `registry/component_mandatoriness.yaml` is classified `required`, so Group 7 applies to no component today.
- `Needs confirmation`: does the `security_01` threat model already cover the EventBus adequately?
- `Needs confirmation`: the planned producers and consumers of the EventBus and the timing of the integration; the ADRs need either the model or an explicit "not yet defined" statement.

## AI Implementation Instruction
- Do not pick an option, write an approval record, or delete the service on the maintainer's behalf; prepare the options and wait.
- After a decision is recorded, create the follow-up issues via `issue-creator`; do not implement them here.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112739
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_01_index.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/24_eventbus/eventbus_01_system-overview.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
