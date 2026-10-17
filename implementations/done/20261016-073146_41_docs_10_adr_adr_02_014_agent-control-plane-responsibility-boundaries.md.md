## Goal

State in ADR-014 that MCP server processes own their security-configuration validation and posture publication,
and that the Agent's only MCP-security responsibility is validating the common posture contract (`REQ-022`).

## Scope

- One modified document `docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md` (15157 bytes):
  the MCP Server responsibility bullet, one new Decision item, one `### Automated Tests` row, one
  `### Manual Review` bullet, and one `## Review Triggers` line.
- No code is edited in this row; rows `07`-`16` land server-side validation and rows `17`-`19` land the Agent-side
  contract gate.

## Assumptions

- Current file verified: `## Decision` `:50`, `### Decision Details` `:52-64` (the MCP Server responsibility bullet
  at `:60` reads "responsible for the technical safety of external operations (allowlist validation, path
  validation, sandboxed execution, resource limits, argument validation). These safety judgments are not taken over
  by the Orchestrator/ToolExecutor layers."; item 3 at `:64` states the ADR extends ADR-001's scope),
  `### Out of Scope` `:74-80` (item at `:79` excludes "Details of the safety policy of each individual MCP Server
  (allowlist contents, sandbox types, and so on)"), `## Rationale` `:81-94` (`:89` states the inconsistency risk
  when two layers judge the same safety question), `## Consequences` `:111-122`, `## Invariants` `:123-127`
  (INV-03 at `:127`), `## Verification` `:129`, `### Automated Tests` table `:131-135`, `### Startup Validation`
  `:137-139` ("Not applicable (this ADR is a static design discipline ...)"), `### Manual Review` `:152-156`
  (bullet at `:154`, closing note at `:156` states INV-01 and INV-03 have no automated tests), `## Implementation
  Notes` `:158-162`, `## Known Deviations` `:164-166` ("Not applicable"), `## Review Triggers` `:168-176`,
  `## Approval` `:177-191`, `## Related ADRs` `:193-195`, `## Implementation References` `:197-206`.
- `## Implementation References` `:197-206` names `scripts/mcp_servers/tool_validators.py` and
  `scripts/mcp_servers/shell/shell_service.py` but not `scripts/agent/security_audit_config.py`, so deleting the
  audit loaders requires no change there, and the section may not gain items
  (`tools/check_adr_preservation.py:148-154`).
- `tools/check_adr_structure.py` check (b) warns when a `scripts/` or `tests/` path cited under
  `## Implementation Notes` is absent from `## Implementation References`; this row adds no path to
  Implementation Notes.
- `tools/check_adr_structure.py` check (d) forbids a global `INV-NNN` id; invariant ids are ADR-local `INV-NN`.
- This file contains zero `MUST`/`MUST NOT`/`SHOULD`/`MAY` tokens, so the normative-count WARNING cannot fire.
- `docs/10_adr/adr_01_index.md:151` records ADR-014 INV-01 and INV-03 as Manual Review (code review), and
  `docs/10_adr/adr_02_014_*:156` states INV-01 and INV-03 have no automated tests.

## Design decisions

- Extend the existing MCP Server responsibility bullet at `:60` rather than adding a parallel bullet. The bullet
  already names the exact judgments the posture contract moves server-side (allowlist validation, path validation,
  sandboxed execution, resource limits, argument validation); adding self-validation and posture publication to the
  same bullet keeps one statement per component, which is this ADR's stated purpose at `:30`.
- Add one Decision item for the Agent side: the Agent validates only the common posture contract (contract
  version, check set, and result shape) and gates registration on it. It does not re-derive a server's allowlist,
  path, or sandbox decisions. This is the positive statement of what INV-03 already forbids duplicating.
- Keep INV-03 byte-identical. Its text already prohibits the duplication this Plan removes, and `INV-NN` text
  change is an ERROR finding (`tools/check_adr_preservation.py:143-145`).
- Keep `### Startup Validation` as "Not applicable". This ADR is a design discipline, and the startup gates it
  implies are owned by ADR-002, ADR-003, and ADR-004 (rows `37`-`39`). Claiming startup validation here would
  duplicate another ADR's verification authority.
- Add an `### Automated Tests` row citing bare paths only, and keep the note at `:156` that INV-01 and INV-03 have
  no automated tests. The new row verifies the contract gate, not INV-03 itself, so the note stays accurate;
  adding a `path.py::name` citation would be an ERROR finding (`:159-161`).

## Alternatives considered

- Reword INV-03 to name posture validation explicitly — rejected: ERROR-level `INV-NN` text change, and the
  invariant's wording is already general enough to cover it.
- Add `INV-04: The Agent validates only the common posture contract` — rejected: `INV-NN` addition is an ERROR
  finding with no override flag; the rule is a Decision, not a new invariant.
- Move the Agent-side rule into `## Implementation Notes` — rejected: `check_adr_structure.py` check (b) flags any
  path named there that `## Implementation References` does not list, and that list cannot gain items.
- Change `### Startup Validation` from "Not applicable" to a posture-gate description — rejected: it would make
  two ADRs claim verification authority for the same gate, against the boundary
  `docs/10_adr/adr_01_index.md:89` records.
- Delete the Out of Scope item at `:79` because server safety policy is now validated server-side — rejected: that
  item excludes server safety *details* from this ADR's scope, which remains true; the Agent still does not see
  them.

## Implementation
### Target file

`docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md` (modify)

### Procedure

1. Extend the MCP Server responsibility bullet at `:60` with: each MCP server validates its own security
   configuration at its own startup and publishes the result as a security posture on `GET /health`.
2. Add one `### Decision Details` item after item 3 at `:64`: the Agent's MCP-security responsibility is limited
   to validating the common posture contract (contract version, check set, result shape) and gating Tool
   registration on it; the Agent does not re-derive allowlist, path, sandbox, resource-limit, or argument
   validation decisions.
3. Add one `### Automated Tests` row after `:135` for the contract gate, citing bare paths
   (`tests/agent/test_mcp_health_posture.py`, `tests/shared/test_runtime_tool_registry.py`), Verifies `INV-03`,
   Type `Unit`, Blocking `No`.
4. Add one `### Manual Review` bullet after `:154`: when new Agent-side code inspects MCP server configuration or
   re-implements a server-side safety decision, review it against INV-03.
5. Add one `## Review Triggers` line after `:176` recording that per-server self-validation and the posture
   contract were introduced on 2026-10-16 (linked with ADR-002, ADR-003, ADR-004).
6. Keep `:1-59`, `:61-63`, `:65-135`, `:137-153`, `:155-176`, `:177-206` unchanged, including `## Invariants` at
   `:123-127`, `### Startup Validation` at `:137-139`, the closing note at `:156`, `## Known Deviations` at
   `:164-166`, the whole `## Approval` section, `## Related ADRs` at `:193-195`, and `## Implementation References`
   at `:197-206`.

### Method

- Land this row after rows `07`-`16` and `17`-`19` are merged, so the boundary text describes code that exists.
- Run `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md`
  before and after. The only expected WARNING is the `## Decision` text change; map it in the commit message as
  "MCP Server bullet extended with self-validation and posture publication; one Decision item added; items 1-3
  otherwise unchanged".

### Details

- The file grows by roughly five lines; nothing is removed.
- The new `### Automated Tests` row must match this table's separator style at `:133`
  (`| --- | --- | --- | --- | --- |`), which differs from the style other ADRs use.
- The new text must not use `MUST`, `MUST NOT`, `SHOULD`, or `MAY`, keeping all four counts at zero.

## Compatibility considerations

- `docs/10_adr/adr_01_index.md:151` (row `36`) lists ADR-014 INV-01 and INV-03 under Manual Review; the new
  Automated Tests row must not be described as covering INV-03 fully, or that index row becomes stale.
- `docs/10_adr/adr_02_014_*:156`'s statement that INV-01 and INV-03 have no automated tests must stay consistent
  with the new row; the row verifies the contract gate, and the note is kept unchanged.
- `docs/23_agent/agent_06_*` tool-routing documents and `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`
  describe where safety decisions are made and are follow-up documents.

## Security considerations

- The responsibility boundary is the reason the Agent-side audit existed at all in some reviewers' minds; stating
  the new boundary explicitly is what stops a future change from re-adding an Agent-side cross-config check "for
  defense in depth" without an architecture decision.
- Keeping the Agent's role to contract validation limits the Agent's exposure to server configuration contents,
  which is the ADR-002 trust boundary.

## Rollback considerations

- Restore with `git checkout -- docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md`. Revert
  it together with rows `07`-`16` and `17`-`19`; reverting the code rows alone would leave the ADR describing a
  boundary the code does not implement.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| ADR content preserved | `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md` | no ERROR; one mapped `## Decision` WARNING |
| Matrix citations resolve | `uv run python tools/check_adr_invariant_matrix.py` | no finding |
| ADR structure | `uv run python tools/check_adr_structure.py` | no ERROR, no Notes/References drift WARNING |
| Docs structure | `uv run python tools/check_docs_structure.py` | clean |
| Docs content policy | `uv run python tools/check_docs_content_policy.py --strict` | clean |
| Boundary holds in code | `PYTHONPATH=scripts uv run lint-imports` | no Agent module imports MCP server config models (row `25`) |

## Completion criteria

- The MCP Server responsibility bullet names self-validation and posture publication.
- A Decision item states the Agent validates only the common posture contract.
- `## Invariants`, `### Startup Validation`, `## Known Deviations`, `## Approval`, `## Related ADRs`, and
  `## Implementation References` are byte-identical to before the edit.
- `check_adr_preservation.py` reports no ERROR and `check_adr_structure.py` reports no drift WARNING.

## Out of scope

- Implementing server-side validation (rows `07`-`16`).
- Implementing the Agent-side contract gate (rows `17`-`19`).
- Rewording INV-03.
- `docs/23_agent/agent_06_*` and `docs/22_mcp/mcp_05_*` updates (follow-up).

## Confirmation outcomes

- Resolved 2026-10-17: the new `### Automated Tests` row stays Blocking `No`, matching the existing row and the
  note that INV-01 and INV-03 are review-verified. The blocking enforcement of the same gate lives in ADR-003
  Decision Detail 16 (row `38`) and ADR-004 (row `39`).
- Resolved 2026-10-17: the row's Test cell carries the parenthetical "contract gate only; the INV-03 duplication
  rule itself stays review-verified". Step 3 sets `Verifies INV-03` while this document's Design decisions keep the
  closing note that INV-03 has no automated tests; the parenthetical states which part the row covers, so that note
  and `docs/10_adr/adr_01_index.md`'s Manual Review entry for ADR-014 INV-03 stay accurate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the current gate results before editing | Completed | 2026-10-17 | 2026-10-17 | ADR preservation structure reference matrix docs structure content policy and agent consistency gates all clean before editing, file 15157 bytes |
| 2 | Extend the MCP Server responsibility bullet | Completed | 2026-10-17 | 2026-10-17 | MCP Server bullet extended with self-validation and posture publication on GET /health, the rest of the bullet unchanged |
| 3 | Add the Agent-side contract Decision item | Completed | 2026-10-17 | 2026-10-17 | Decision item 4 added after item 3, items 1 to 3 unchanged, no MUST SHOULD or MAY used, INV-03 byte-identical |
| 4 | Add the Automated Tests row and Manual Review bullet | Completed | 2026-10-17 | 2026-10-17 | automated tests row added in the table spaced separator style with bare test paths and a parenthetical scoping it to the contract gate so the closing note and the index Manual Review entry stay accurate, plus one manual review bullet |
| 5 | Add the Review Trigger line | Completed | 2026-10-17 | 2026-10-17 | review trigger line appended after the Known Deviations scale trigger, nothing removed |
| 6 | Run the ADR and docs gates | Completed | 2026-10-17 | 2026-10-17 | only the mapped Decision WARNING remains, all gates clean, lint-imports reports 6 contracts kept 0 broken, file 16339 bytes under the 24576 cap |

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
- **Requirement ID**: `REQ-022` (align ADR-014 with server-owned validation and Agent-side contract validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `docs/10_adr/adr_02_014_agent-control-plane-responsibility-boundaries.md`
