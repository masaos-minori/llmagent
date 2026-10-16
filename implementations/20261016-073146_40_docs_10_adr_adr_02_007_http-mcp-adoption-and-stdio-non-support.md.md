## Goal

Record the security posture contract as part of `GET /health` in ADR-007, and state that the Agent consumes that
result instead of pre-validating MCP server configuration (`REQ-021`).

## Scope

- One modified document `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md` (23717 bytes): one
  new `### Decision Details` item, two `## Failure Policy` lines, one `### Startup Validation` bullet, one
  `### Security Consequences` bullet, one `## Implementation Notes` sentence, and one `## Review Triggers` line.
- No code is edited in this row; rows `42`-`46` and `12`-`14` land the `/health` posture payloads.

## Assumptions

- Current file verified: `## Decision` `:65`, `### Decision Details` `:67-79` (item 9 at `:75` covers loopback
  bind and non-empty tokens, item 10 at `:76` states that neither process reads the other's configuration file),
  `### Scope` `:81-88` (`Target APIs or processing paths` at `:86` names `POST /v1/call_tool`, `GET /v1/tools`,
  `GET /health`), `### Security Consequences` `:187-190`, `## Invariants` `:192-206` (INV-09 at `:200`, INV-11 at
  `:204`, INV-12 at `:205`), `## Exceptions` `:207-209` ("Not applicable"), `## Failure Policy` `:211`,
  `### Fail-Fast Conditions` `:213-222`, `### Fail-Open or Degraded Conditions` `:223-226`, `### Retry Policy`
  `:227-233`, `### Fallback Policy` `:234-237`, `## Data Ownership and Persistence` `:238-247`, `## Verification`
  `:248`, `### Automated Tests` table `:250-263`, `### Startup Validation` `:265-267`, `### Runtime Monitoring`
  `:273-277`, `### Manual Review` `:278-282`, `## Implementation Notes` `:283-289`, `## Known Deviations`
  `:291-293` ("Not applicable"), `## Review Triggers` `:295-311`, `## Approval` `:312-330`, `## Related ADRs`
  `:331-335`, `## Implementation References` `:336-347`.
- `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md:261` cites
  `tests/agent/test_startup_severity_classification.py::TestCheckServicesSeverityClassification::test_mcp_auth_fatal_when_any_server_missing_token`.
  `tools/check_adr_preservation.py:156-161` makes removing it an ERROR with no override flag, so row `33` keeps
  that class and test name unchanged.
- `### Automated Tests` `:255-263` cites eight `path.py::name` node ids and four bare paths; all must stay
  byte-identical.
- `## Implementation References` `:338` names `scripts/mcp_servers/server.py` — `MCPServer.run_http()`,
  `attach_auth_middleware()` — and `:345` names the three HTTP endpoints, so the posture contract needs no new
  entry there, and `## Implementation References` may not gain items (`:148-154`).
- `tools/check_adr_structure.py` check (b) warns when a `scripts/` or `tests/` path cited under
  `## Implementation Notes` is absent from `## Implementation References`; this row therefore adds no new path to
  Implementation Notes.
- This file contains zero `MUST`/`MUST NOT`/`SHOULD`/`MAY` tokens, so the normative-count WARNING cannot fire.
- `### Fail-Open or Degraded Conditions` `:225-226` currently permits partial-availability continuation for an
  unavailable non-mandatory server, which is ADR-004's availability path.

## Design decisions

- Add one Decision Details item rather than editing item 9 or 10. Item 9 owns authentication and binding, and item
  10 owns the "neither process reads the other's file" rule that the posture contract replaces the audit with.
  Editing either would blur two rules that already read correctly; a new item states the new mechanism and cites
  item 10 as its basis.
- Put the posture `FAILED` condition in `### Fail-Fast Conditions` and add one clarifying sentence to
  `### Fail-Open or Degraded Conditions`. This ADR already lists every MCP-server-side Fail-Fast condition, and
  the clarification is needed because a posture failure looks superficially like the degraded case at `:225-226`
  but must not be treated as one. `## Failure Policy` is WARNING-monitored, so both edits are allowed with a
  sentence-level mapping.
- Describe the posture payload as data on the existing `GET /health` endpoint, not as a new endpoint. `### Scope`
  `:86` and `## Implementation References` `:345` already name `GET /health`, and adding an endpoint would require
  changing `## Implementation References`, which is ERROR-monitored.
- State the no-pre-validation rule as: the Agent validates the posture contract's shape and version, not the
  server's configuration contents. This is the ADR-007 side of the ADR-002 rule at item 10, and it is what keeps
  the two ADRs from describing two different boundaries.
- Cite new verification as bare paths (`tests/agent/test_mcp_health_posture.py`, `tests/mcp_servers/`), because
  adding a `path.py::name` citation is an ERROR finding (`:159-161`).

## Alternatives considered

- Extend INV-09 to name the posture contract — rejected: `INV-NN` text change is an ERROR finding
  (`:143-145`), and INV-09's subject is authentication and binding, which the posture contract consumes rather
  than redefines.
- Add a `## Posture Contract` H2 — rejected: H2 sequence change is an ERROR finding (`:131-136`), and
  `check_adr_structure.py` check (c) restricts ADR headings to the standardized list and order.
- Record the contract only in `## Implementation Notes` — rejected: Implementation Notes is a pointer section here
  (it ends with "See Implementation References for the current file/symbol list"), and `check_adr_structure.py`
  check (b) would flag any new path it names.
- Treat a posture failure as a degraded condition for a non-required server — rejected: it contradicts ADR-004
  Group 2 and INV-10, and row `39` classifies it as a safety/integrity failure.
- Add a new `GET /v1/security_posture` endpoint — rejected: it would require adding an `## Implementation
  References` item (ERROR) and would split one server's security state across two endpoints that the Agent must
  then correlate.

## Implementation
### Target file

`docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md` (modify)

### Procedure

1. Add one `### Decision Details` item after item 11 at `:79`: each MCP server validates its own security
   configuration at its own startup and publishes the result as a security posture on `GET /health`; the Agent
   validates the posture contract's version, check set, and shape, and does not read or interpret the server's
   configuration file. A server whose posture reports `FAILED` is not registered and startup aborts.
2. Add one `### Fail-Fast Conditions` bullet after `:221`: an MCP server reports a posture check as `FAILED` on
   `GET /health` (Safety/Integrity failure, not an availability failure).
3. Add one clarifying sentence to `### Fail-Open or Degraded Conditions` after `:226`: partial availability applies
   to availability failures only, and a posture `FAILED` result is not an availability failure.
4. Add one `### Startup Validation` bullet after `:267`: posture results are read from `GET /health` before Tool
   definitions are registered.
5. Add one `### Security Consequences` bullet after `:190`: the Agent holds no copy of server security settings,
   and a server's security state is observable through the same authenticated endpoint as its liveness.
6. Add one sentence to `## Implementation Notes` after `:288` naming the posture payload as part of the existing
   authenticated `/health` response, without naming a new file path.
7. Add one `## Review Triggers` line after `:311` recording that per-server self-validation and the posture
   contract were introduced on 2026-10-16 (linked with ADR-002 and ADR-004).
8. Keep `:1-79`, `:81-186`, `:192-221`, `:223-263`, `:265-267`, `:269-311`, `:312-347` unchanged, including the
   whole `## Invariants` section, `## Exceptions` at `:207-209`, `## Known Deviations` at `:291-293`, the whole
   `## Approval` section, and every citation in `### Automated Tests` `:255-263`.

### Method

- Land this row after rows `42`-`46` (server `/health` wiring) and row `18` (Agent-side consumption) are merged,
  so the ADR describes an endpoint payload that exists.
- Run `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md`
  before and after. The expected WARNINGs are the `## Decision` and `## Failure Policy` text changes; map both in
  the commit message as "one Decision item added, items 1-11 unchanged; one Fail-Fast bullet added, one
  Fail-Open clarification sentence added, existing bullets unchanged".

### Details

- The file grows by roughly seven lines; nothing is removed.
- The new text must not use `MUST`, `MUST NOT`, `SHOULD`, or `MAY`, keeping all four counts at zero.
- The new Decision item must reference item 10 at `:76` so the ADR-002 boundary is cited rather than restated.

## Compatibility considerations

- `docs/10_adr/adr_02_007_*:261`'s citation is the test row `33` must preserve; this row does not touch it.
- `docs/10_adr/adr_01_index.md:125` (row `36`) records ADR-007 INV-09 verification; its wording must stay
  consistent with the new Fail-Fast bullet.
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` documents the `/health` response shape and is the follow-up
  document that must describe the posture payload fields.
- `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` and
  `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` describe the checks the posture reports and are
  follow-up documents.

## Security considerations

- `/health` is authenticated by the same middleware as the tool endpoints, so publishing posture there does not
  create an unauthenticated disclosure path; the ADR text must keep that fact visible, because a future change
  that exempted `/health` from authentication would leak each server's security configuration state.
- Stating that a posture `FAILED` result is not an availability failure is what prevents a future change from
  routing it into the degraded path.

## Rollback considerations

- Restore with `git checkout -- docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md`. Revert it
  together with rows `18` and `42`-`46`; reverting the code rows alone would leave the ADR describing a posture
  payload no server publishes.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| ADR content preserved | `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md` | no ERROR; two mapped WARNINGs (`Decision`, `Failure Policy`) |
| Cited test still exists | `uv run pytest "tests/agent/test_startup_severity_classification.py::TestCheckServicesSeverityClassification::test_mcp_auth_fatal_when_any_server_missing_token"` | passes (row `33`) |
| Matrix citations resolve | `uv run python tools/check_adr_invariant_matrix.py` | no finding |
| ADR structure | `uv run python tools/check_adr_structure.py` | no ERROR, no Notes/References drift WARNING |
| Docs structure | `uv run python tools/check_docs_structure.py` | clean |
| Docs content policy | `uv run python tools/check_docs_content_policy.py --strict` | clean |
| Posture is on `/health` | `uv run pytest tests/mcp_servers/shell/test_shell_server_health_posture.py` | passes (row `42`) |

## Completion criteria

- A Decision Details item states the posture contract on `GET /health` and the Agent's no-pre-validation boundary.
- `### Fail-Fast Conditions` names a posture `FAILED` result, and `### Fail-Open or Degraded Conditions` states
  that it is not an availability failure.
- `## Invariants`, `## Exceptions`, `## Known Deviations`, `## Approval`, `## Implementation References`, and every
  `### Automated Tests` citation are byte-identical to before the edit.
- `check_adr_preservation.py` reports no ERROR and `check_adr_structure.py` reports no drift WARNING.

## Out of scope

- Implementing the `/health` posture payload (rows `42`-`46`).
- Agent-side posture consumption (row `18`).
- ADR-004 failure classification (row `39`).
- `docs/22_mcp/mcp_02_02_*` and `docs/22_mcp/mcp_05_*` updates (follow-up).

## Needs confirmation

- Whether the posture payload's field names should be listed in this ADR. This row keeps field names out of the
  ADR because `## Implementation References` cannot gain items and field-level detail belongs to
  `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the current gate results before editing | Pending | — | — | baseline |
| 2 | Add the posture-contract Decision item | Pending | — | — | cites Decision item 10 |
| 3 | Add the Fail-Fast bullet and Fail-Open clarification | Pending | — | — | WARNING, needs mapping |
| 4 | Add Startup Validation, Security Consequences, Implementation Notes lines | Pending | — | — | no new paths |
| 5 | Add the Review Trigger line | Pending | — | — | |
| 6 | Run the ADR and docs gates | Pending | — | — | |

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
- **Requirement ID**: `REQ-021` (align ADR-007 with the posture contract on `/health`)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md`
