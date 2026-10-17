## Goal

Classify a server-side security posture `FAILED` result as a safety/integrity failure under ADR-004, so that a
`required = false` server cannot turn it into partial availability (`REQ-020`).

## Scope

- One modified document `docs/10_adr/adr_02_004_environment-failure-handling-policy.md` (29632 bytes): Group 2
  item 5, one unnumbered Decision paragraph, one `## Verification` row, one `### Startup Validation` bullet, one
  `### Negative Consequences` bullet, and one `## Review Triggers` line.
- No code is edited in this row; rows `18` and `22` land the mechanism this row classifies.

## Assumptions

- Current file verified: `## Decision` `:60`, `### Group 2: Failure Classification` `:67-73` (item 4 at `:69`
  defines the two failure kinds; item 5 at `:70` lists safety/integrity failures including "invalid
  auth/authz/Allowlist/Safety Tier config" and "missing Secrets"; item 6 at `:71` forbids converting them to
  partial availability; item 8 at `:73` lists the four conditions that permit continuation),
  `### Group 3: Component Mandatoriness Classification` `:74-80` (item 13 at `:79` records approved per-server
  classification in `agent_08_04` and requires `config/agent.toml`'s `required` to match it),
  `### Group 9: Tool Visibility and Execution Boundary` `:98-103` (item 21 at `:100`, item 24 at `:103` keeps
  ADR-003's static-availability/Dynamic-Health separation), `### Negative Consequences` `:204-212`,
  `## Invariants` `:213-231` (INV-07 at `:221`, INV-09 at `:223`, INV-10 at `:224`, INV-11 and INV-12 at
  `:225-226`), `## Exceptions` `:239-241` (spawn-failure exception only), `## Verification` `:243`,
  `### Automated Tests` table `:245-257`, `### Startup Validation` `:259-263`, `## Implementation Notes`
  `:295-299`, `## Known Deviations` `:301-303` ("Not applicable"), `## Review Triggers` `:305-318`,
  `## Approval` `:320-337`, `## Related ADRs` `:339-344`, `## Implementation References` `:346-358`.
- `docs/10_adr/adr_02_004_environment-failure-handling-policy.md:358` is the bullet
  `- Tests — \`tests/agent/shared/test_startup_validation_pipeline.py\`, \`tests/agent/test_startup.py\``.
  `tools/check_adr_preservation.py:148-154` compares `Implementation References` items as whole list items, so
  this bullet must stay byte-identical. Rows `35` and `30` keep both files.
- `## Implementation Notes` `:296-298` cites `scripts/agent/services/mcp_tool_discovery.py::fetch_tools()` and
  `scripts/agent/startup_mcp_starter.py::McpServerStarter`, both matched by `_TEST_REF_RE` and therefore
  ERROR-monitored for add or remove, and both already present in `## Implementation References` at `:353` and
  `:356`.
- `tools/check_adr_structure.py` check (b) warns when a `scripts/` or `tests/` path cited under
  `## Implementation Notes` is absent from `## Implementation References`, and `## Implementation References` may
  not gain items. This row therefore adds no path to Implementation Notes.
- This file contains zero `MUST`/`MUST NOT`/`SHOULD`/`MAY` tokens, so the normative-count WARNING cannot fire.
- INV-07 already names Allowlist and auth failures as Fail-Closed at startup, and INV-09 already limits
  non-mandatory continuation to availability failures. The alignment is therefore a clarification of existing
  invariants, not a new one.

## Design decisions

- Add the posture result to Group 2 item 5's list rather than creating a new failure kind. Item 4 at `:69` fixes
  the taxonomy at two kinds, and a posture `FAILED` result is an invalid Allowlist/auth/Safety-Tier configuration
  reported by the owning server. A third kind would break the taxonomy the whole Failure Policy depends on.
- State the non-required rule as unnumbered Decision prose instead of a new numbered item. The Decision items are
  numbered 1-27 across ten groups; inserting a numbered item inside Group 2 or Group 3 would renumber every
  later item and produce a diff that touches items this row has no reason to change.
- Keep `## Exceptions` unchanged. A posture failure aborting startup regardless of `required` is the rule that
  follows from INV-07 and INV-09, not an exception to it. The only exception in this ADR is the spawn-failure
  exception at `:241`, which concerns a server that never started.
- Do not reword INV-07, INV-09, or INV-10. Their text already produces the required behavior; `INV-NN` text change
  is an ERROR finding (`tools/check_adr_preservation.py:143-145`).
- Record the verification as a new `### Automated Tests` row citing bare paths, because adding a
  `path.py::name` citation is an ERROR finding (`:159-161`).

## Alternatives considered

- Add `INV-17: A server posture failure is a safety/integrity failure` — rejected: `INV-NN` addition is an ERROR
  finding with no override flag; the guarantee already follows from INV-07 and INV-09.
- Extend the `## Exceptions` section with a posture clause — rejected: it would read as permitting continuation in
  some posture cases, which is the opposite of this row's intent.
- Reword INV-09 to name posture failures explicitly — rejected: ERROR-level `INV-NN` text change.
- Add a `### Posture Failures` H2 under Verification — rejected: `check_adr_structure.py` check (c) restricts ADR
  headings to the standardized list and order, and `check_adr_preservation.py:131-136` reports H2 sequence changes
  as ERROR. H3 subsections are not compared, but adding one here duplicates `### Automated Tests`.
- Document the rule only in `docs/23_agent/agent_08_04_*`'s classification table — rejected: that table records
  per-server classification, and ADR-004 Group 3 item 13 at `:79` makes the ADR the authority for the criteria the
  table must follow.

## Implementation
### Target file

`docs/10_adr/adr_02_004_environment-failure-handling-policy.md` (modify)

### Procedure

1. Extend Group 2 item 5 at `:70` with "a server security-posture `FAILED` result reported by the owning MCP
   server" inside the existing list, keeping the rest of the item unchanged.
2. Add one unnumbered paragraph after Group 3 item 13 at `:79`: a posture failure is a safety/integrity failure,
   not an availability failure, so the four conditions of item 8 are not met and `required = false` does not
   permit continuation; the server is not "disabled", startup aborts.
3. Add one `### Automated Tests` row after `:257`: "A server posture `FAILED` result aborts startup even when the
   server is `required = false`", Verifies `INV-07, INV-09, INV-10`, Type `Integration`, Blocking `Yes`,
   Implementation citing bare paths (`tests/agent/test_mcp_health_posture.py`,
   `tests/mcp_servers/test_mcp_server_base.py`).
4. Add one `### Startup Validation` bullet after `:263`: posture results are read from each server's `/health`
   before the Registry is built, and a `FAILED` result is classified as safety/integrity.
5. Add one `### Negative Consequences` bullet after `:212`: a misconfigured non-required server now blocks
   startup, so operators must fix server configuration rather than rely on `required = false`.
6. Add one `## Review Triggers` line after `:316` recording that per-server self-validation and the posture
   contract were introduced on 2026-10-16 (linked with ADR-002 and ADR-003).
7. Keep `:1-69`, `:71-78`, `:80-212`, `:213-257`, `:259-263`, `:265-318`, `:320-358` unchanged, including
   `## Exceptions` at `:239-241`, `## Known Deviations` at `:301-303`, the whole `## Approval` section, and the
   `## Implementation References` bullet at `:358`.

### Method

- Land this row after rows `18` and `22` are merged, so the classification describes behavior that startup
  actually performs.
- Run `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_004_environment-failure-handling-policy.md`
  before and after. The only expected WARNING is the `## Decision` text change; map it in the commit message as
  "Group 2 item 5 list extended by one entry; one unnumbered paragraph added after Group 3 item 13; items 1-27
  otherwise unchanged".

### Details

- The file grows by roughly six lines; nothing is removed.
- The new Decision paragraph must not use `MUST`, `MUST NOT`, `SHOULD`, or `MAY`; this file's count for all four
  keywords is zero in both versions.
- The new Verification row uses the same five-column shape as `:245-257`
  (`| Test | Verifies | Type | Blocking | Status |`).

## Compatibility considerations

- `docs/10_adr/adr_01_index.md:115` (row `36`) reports ADR-004 INV-07/INV-10 as Partial; its wording must match
  this classification.
- `docs/23_agent/agent_08_04_*`'s per-server classification table is named by Group 3 item 13 at `:79`; it must
  record that posture failures are outside the non-required relaxation path. That document is a follow-up.
- `docs/10_adr/adr_02_004_*:241`'s spawn-failure exception stays intact; row `33` and row `35` keep the tests that
  the Verification table already cites.
- `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` describes Fail-Open/Fail-Closed tiers and is a
  follow-up document for this classification.

## Security considerations

- The failure class is what decides whether a security failure can be tolerated. Classifying posture failures as
  safety/integrity is what prevents `required = false` from becoming a way to run with an unvalidated server.
- Keeping the spawn-failure exception unchanged preserves the existing guarantee that a server that never started
  also aborts startup, so neither path leaves a partially validated Agent running.

## Rollback considerations

- Restore with `git checkout -- docs/10_adr/adr_02_004_environment-failure-handling-policy.md`. Revert it together
  with rows `18` and `22`; reverting the code rows alone would leave the ADR classifying a mechanism that does not
  exist.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| ADR content preserved | `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_004_environment-failure-handling-policy.md` | no ERROR; one mapped `## Decision` WARNING |
| Matrix citations resolve | `uv run python tools/check_adr_invariant_matrix.py` | no finding |
| ADR structure | `uv run python tools/check_adr_structure.py` | no ERROR, no Notes/References drift WARNING |
| Docs structure | `uv run python tools/check_docs_structure.py` | clean |
| Docs content policy | `uv run python tools/check_docs_content_policy.py --strict` | clean |
| Classification is real | `uv run pytest tests/agent/test_mcp_health_posture.py` | posture failure aborts startup even with `required = false` (row `18`) |

## Completion criteria

- Group 2 item 5 names a posture `FAILED` result as a safety/integrity failure.
- Decision prose states that `required = false` does not permit continuation on a posture failure.
- `## Exceptions`, `## Known Deviations`, `## Approval`, and the `## Implementation References` bullet at `:358`
  are byte-identical to before the edit.
- `check_adr_preservation.py` reports no ERROR and `check_adr_structure.py` reports no drift WARNING.

## Out of scope

- Implementing posture gating in `check_readiness()` (row `18`).
- Removing the audit step from the pipeline (row `22`).
- Updating `docs/23_agent/agent_08_04_*`'s classification table (follow-up).
- ADR-003's Registry gating wording (row `38`).

## Confirmation outcomes

- Resolved 2026-10-17: `agent_08_04`'s classification table is not edited. The Plan's frozen target-file table
  does not list that document, so a posture-failure column stays a follow-up.
- Resolved 2026-10-17: the row `18` implementation routed a posture failure by `required`, which contradicted Plan
  `REQ-013` and `AC-007` ("a non-required server never converts a Safety/Integrity failure into partial
  availability"). The Plan was amended by appending row 59 for `scripts/agent/services/mcp_health.py`, and
  `check_service_health()` now routes a Safety or Integrity gate failure to the fatal path whatever `required`
  says; only an Availability failure of a `required = false` server degrades to a non-fatal warning.
- Resolved 2026-10-17: the new Verification row cites `tests/agent/test_mcp_health_posture.py` and
  `tests/agent/test_failure_handling_policy_cross_cutting.py` rather than
  `tests/mcp_servers/test_mcp_server_base.py`, because the startup-abort assertion lives in the Agent-side tests.
- Resolved 2026-10-17: the new paragraph names "the conditions of item 8" without a count, because item 8 lists
  five conditions, not the four this document's step 2 stated.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the current gate results before editing | Completed | 2026-10-17 | 2026-10-17 | ADR preservation structure reference matrix docs structure content policy and agent consistency gates all clean before editing, 42 posture tests passing |
| 2 | Extend Group 2 item 5 with the posture failure class | Completed | 2026-10-17 | 2026-10-17 | item 5 list extended by one entry naming a server security posture FAILED result, rest of the item unchanged |
| 3 | Add the non-required continuation paragraph | Completed | 2026-10-17 | 2026-10-17 | unnumbered paragraph added after item 13, no MUST SHOULD or MAY used, the item 8 condition count omitted because item 8 lists five conditions, written only after the appended Plan row 59 fixed check_service_health routing |
| 4 | Add the Verification row and Startup Validation bullet | Completed | 2026-10-17 | 2026-10-17 | row added after the fallback row citing the two agent-side test files because the server-side base test does not assert a startup abort, plus one startup validation bullet, bare paths only |
| 5 | Add the Negative Consequences and Review Trigger lines | Completed | 2026-10-17 | 2026-10-17 | negative consequences and review trigger lines appended, nothing removed, Exceptions Known Deviations Approval and Implementation References byte-identical |
| 6 | Run the ADR and docs gates | Completed | 2026-10-17 | 2026-10-17 | only the mapped Decision WARNING remains, size 30903 under the 31037 cap, all gates clean, 42 passed in the posture test file, agent suite shows only the 9 known rollback failures, 114 passed in tests/integration |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | The row `18` implementation routed a posture failure by `required`, contradicting frozen Plan `REQ-013`/`AC-007`; resolved by user decision to append Plan row 59 and fix `check_service_health()` before writing the Decision paragraph | Yes | 2026-10-17 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-020` (align posture failures with ADR-004 safety/integrity classification)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `docs/10_adr/adr_02_004_environment-failure-handling-policy.md`, `scripts/agent/services/mcp_health.py` (appended Plan row 59)
