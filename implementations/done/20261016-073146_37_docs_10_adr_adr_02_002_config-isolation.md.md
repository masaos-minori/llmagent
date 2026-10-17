## Goal

Remove the cross-config-read exception from ADR-002 and record per-server self-validation plus the posture
contract as the decision that replaced it (`REQ-018`).

## Scope

- One modified document `docs/10_adr/adr_02_002_config-isolation.md` (20582 bytes): the `## Exceptions` audit
  bullet, Decision item 7, the `## Verification` rows that describe the audit, `## Security Consequences`, and
  `## Review Triggers`.
- No code or test file is edited in this row; rows `20`-`21`, `25`, `27` land the code side.

## Assumptions

- Current file verified: `## Decision` `:57`, `### Decision Details` `:59-77` (item 7 at `:67` reads "The Agent
  does not interpret MCP-server-internal configuration, except for the read-only startup security audit listed in
  Exceptions."), `## Invariants` `:174-180` (INV-01 at `:176` reads "Each process reads only its permitted
  configuration files, except as listed in Exceptions."), `## Exceptions` `:181-190` (EventBus bullet at `:183`,
  audit bullet at `:184-188` with four sub-bullets, closing paragraph at `:190`), `## Verification` `:224`,
  `### Automated Tests` `:226-234` (audit row at `:231`), `### Startup Validation` `:236-239`,
  `## Implementation Notes` `:256-260`, `## Known Deviations` `:262-264` ("Not applicable"),
  `## Review Triggers` `:266-282` (audit-related triggers at `:272-274`), `## Approval` `:284-303`,
  `## Related ADRs` `:305-308`, `## Implementation References` `:310-326`.
- `docs/10_adr/adr_02_002_config-isolation.md:231` cites
  `tests/agent/test_security_audit_config_isolation.py::test_only_audit_module_imports_security_server_config`
  and `tests/agent/test_security_audit_config_isolation.py::test_audit_dtos_hold_no_secret_fields`, plus the
  `agent-mcp-config-models` contract. Row `27` keeps that file and both test names, and row `25` keeps the
  contract id, so both citations stay resolvable.
- `tools/check_adr_preservation.py` rules that bind this file: front matter and H2 sequence ERROR (`:131-136`);
  `INV-NN` add/remove/reword ERROR (`:138-145`); `Related ADRs` and `Implementation References` item add/remove
  ERROR (`:148-154`); `` `path.py::name` `` citation add or remove ERROR (`:156-161`); `Known Deviations` and
  `Approval` change ERROR (`:163-165`); `Decision`, `Failure Policy`, `Data Ownership and Persistence`,
  `Invariants` text change WARNING (`:166-172`); normative keyword decrease WARNING (`:174-180`) — this file
  contains zero such keywords, so it cannot fire; backtick path/symbol token removal WARNING (`:181-185`).
- `## Exceptions`, `## Consequences` and its subsections, `## Verification` and its subsections,
  `## Implementation Notes`, and `## Review Triggers` are in neither monitored list, so their text may change
  freely apart from the citation rules.
- INV-01's phrase "except as listed in Exceptions" stays accurate after the audit bullet is deleted, because the
  EventBus exception remains in `## Exceptions`. No INV text needs to change.
- `## Implementation References` at `:310-326` does not name `scripts/agent/security_audit_config.py` or
  `scripts/agent/services/security_audit.py`, so deleting those modules requires no change to that list.
- `tools/check_adr_structure.py` check (b) warns when a `scripts/` or `tests/` path cited under
  `## Implementation Notes` is absent from `## Implementation References`, and `## Implementation References` may
  not gain items. New evidence therefore goes into `## Verification` tables, not into Implementation Notes.
- `docs/10_adr/adr_02_002_config-isolation.md:274` already lists "Each MCP server can enforce the audited
  settings itself at its own startup (the audit can then move out of the Agent)" as a Review Trigger; this Plan
  is that trigger firing.

## Design decisions

- Delete the audit exception bullet rather than narrow it. Rows `20`-`21` remove the audit and its loaders, so
  no Agent entry point reads another process's configuration file; an exception for a module that no longer
  exists would make the ADR claim a permission the code cannot exercise.
- Reword Decision item 7 to the unconditional rule ("The Agent does not interpret MCP-server-internal
  configuration.") and state the replacement mechanism in the same subsection as a new numbered item: each MCP
  server validates its own security configuration at its own startup and publishes a posture result the Agent
  consumes through `/health`. `## Decision` is WARNING-monitored, so the change is allowed with a sentence-level
  mapping in the commit message.
- Keep INV-01 through INV-04 byte-identical. The new self-validation rule is a consequence and a verification
  fact, not a new invariant id, because `check_adr_preservation.py:141-142` makes adding an `INV-NN` bullet an
  ERROR. Recorded as Needs confirmation.
- Re-base the `:231` Verification row's subject to "No Agent module imports MCP server configuration models, and
  the posture DTOs hold no secret fields" while keeping both citations and the contract name unchanged. The row
  keeps asserting the same structural property against the mechanism that now enforces it (the contract with its
  ignore_imports grant removed, per row `25`).
- Record the fired Review Trigger inside `## Review Triggers` instead of touching `## Approval`. The Approval
  section is ERROR-monitored, including its "as of 2026-10-13" decision-approval line, so the revision evidence
  must live in an unmonitored section.
- Add the posture facts to `## Security Consequences` and `### Startup Validation`, both unmonitored, rather
  than to `## Failure Policy`. Fail-closed classification is ADR-004's ownership (row `39`), and keeping it there
  preserves the ADR-002/ADR-004 boundary the index records at `docs/10_adr/adr_01_index.md:89`.

## Alternatives considered

- Keep the audit exception as a historical note — rejected: `## Exceptions` states live permissions, and a stale
  permission is the exact drift `tools/check_docs_consistency.py` and `tools/check_adr_preservation.py` exist to
  prevent.
- Add `INV-05: Each MCP server validates its own security configuration at its own startup` — rejected: ERROR
  under `check_adr_preservation.py:141-142` with no override flag; amending the checker is out of this Plan's
  scope.
- Move the audit exception text into `## Known Deviations` as a historical record — rejected: `Known Deviations`
  is an ERROR-monitored section (`:163-165`), and a deleted control is not a deviation.
- Rewrite `## Failure Policy` to describe posture failures — rejected: ADR-004 owns failure classification
  (`docs/10_adr/adr_01_index.md:89`), and editing two ADRs for one rule splits the authority.
- Delete the whole `## Verification` audit row — rejected: it is the only row that documents the import-direction
  guarantee, and deleting it would remove two ADR-cited test names, which is an ERROR finding.

## Implementation
### Target file

`docs/10_adr/adr_02_002_config-isolation.md` (modify)

### Procedure

1. Delete the audit exception bullet at `:184-188`. Keep the EventBus bullet at `:183` and the closing paragraph
   at `:190` unchanged.
2. Reword Decision item 7 at `:67` so it states the rule without the exception clause.
3. Add one Decision Details item after item 11 stating: each MCP server validates its own security configuration
   at its own startup and publishes the result as a security posture on `GET /health`; the Agent reads the
   posture and does not read server configuration files.
4. Re-base the `:231` Verification row subject to the no-Agent-import wording, keeping both
   `tests/agent/test_security_audit_config_isolation.py::...` citations and the `agent-mcp-config-models`
   contract name byte-identical.
5. Add one `### Automated Tests` row for per-server self-validation citing bare paths only
   (`tests/mcp_servers/`), and one `### Startup Validation` bullet for posture consumption through
   `check_readiness()`.
6. Add one `### Security Consequences` bullet: the trust boundary now includes the posture contract, and the
   Agent holds no copy of server security settings.
7. Update `## Review Triggers` at `:272-274`: delete the two audit-specific triggers and add one line recording
   that the "each MCP server can enforce the audited settings itself" trigger fired on 2026-10-16 and produced
   this revision.
8. Keep `:1-66`, `:174-183`, `:190-230`, `:232-271`, `:275-326` unchanged, including `## Known Deviations` at
   `:262-264` and the whole `## Approval` section.

### Method

- Land this row in the same commit as rows `20`, `21`, `25`, and `27`, so the ADR text describes code that
  already exists. Landing it earlier makes the ADR deny a module that is still imported.
- Run `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_002_config-isolation.md` before and
  after, and write the WARNING mapping into the commit message: Decision item 7 loses its exception clause; the
  removed backtick tokens `agent/services/security_audit.py::audit_security_defaults()` and
  `agent/security_audit_config.py` name modules deleted by rows `20`-`21`.

### Details

- The file shrinks by roughly 14 lines (five exception lines and two trigger lines removed) and grows by roughly
  six (one Decision item, two Verification rows, one Startup Validation bullet, one Security Consequences bullet,
  one trigger line).
- The `## Exceptions` section keeps its EventBus bullet and its closing "restriction is otherwise unconditional"
  paragraph, so the section still reads as a complete statement rather than an empty one.
- No H2 heading is added, removed, or reordered.

## Compatibility considerations

- `docs/10_adr/adr_01_index.md:111` (row `36`) and `docs/10_adr/adr_02_004_*` (row `39`) reference ADR-002's
  isolation guarantee; their wording must match the re-based `:231` row.
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` and `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`
  describe the audit as an Agent-side control; they are follow-up documents, not this row's edit.
- `tests/agent/test_security_audit_config_isolation.py` (row `27`) keeps the two cited test names, which is what
  keeps `:231` resolvable for `tools/check_adr_invariant_matrix.py`.

## Security considerations

- Removing the exception closes a documented permission for cross-process configuration reads. After this row
  the ADR grants no such permission, and row `25` removes the enforcement grant that made it possible.
- The Decision text is what a reviewer reads to decide whether a new Agent-side config read is acceptable;
  leaving the audit exception in place would invite a new cross-config reader to cite it.

## Rollback considerations

- Restore with `git checkout -- docs/10_adr/adr_02_002_config-isolation.md`. Reverting this row alone leaves the
  ADR describing a deleted module; revert it together with rows `20`, `21`, `25`, `27`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| ADR content preserved | `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_002_config-isolation.md` | no ERROR; WARNING limited to the mapped Decision text change and the two deleted module tokens |
| Cited tests exist | `uv run python tools/check_adr_invariant_matrix.py` | no finding |
| ADR structure | `uv run python tools/check_adr_structure.py` | no ERROR, no Implementation Notes drift WARNING |
| Docs structure | `uv run python tools/check_docs_structure.py` | clean |
| Docs content policy | `uv run python tools/check_docs_content_policy.py --strict` | clean |
| Claim consistency | `uv run python tools/check_docs_consistency.py --domain agent` | clean |
| Isolation gate | `PYTHONPATH=scripts uv run lint-imports` | `agent-mcp-config-models` contract passes with no ignore_imports grant |

## Completion criteria

- `## Exceptions` no longer grants the Agent a cross-config read, and the EventBus exception remains.
- Decision item 7 states the unconditional rule, and a Decision item states per-server self-validation plus the
  posture contract.
- Both `:231` citations and the `agent-mcp-config-models` contract name are unchanged and still resolve.
- `## Known Deviations` and `## Approval` are byte-identical to before the edit.
- `check_adr_preservation.py` reports no ERROR.

## Out of scope

- Deleting `scripts/agent/security_audit.py` and `scripts/agent/security_audit_config.py` (rows `20`-`21`).
- Removing the ignore_imports grant (row `25`).
- Retargeting the isolation tests (row `27`).
- ADR-004 failure-classification wording (row `39`).
- `docs/22_mcp/*` updates (follow-up).

## Confirmation outcomes

- Resolved 2026-10-16 (Plan `UNK-05`): no dedicated `INV-05` is created for per-server self-validation. No
  `INV-NN` bullet is added, removed, or reworded, and `tools/check_adr_preservation.py` is not amended; the new
  rules live in `## Decision`, `## Verification`, `## Review Triggers`, and `## Consequences` prose.
- Resolved 2026-10-17: `## Approval` is not re-dated. The section is ERROR-monitored, its "as of 2026-10-13"
  line records who approved the decision rather than when this ADR was last read, and re-dating it would require
  amending `tools/check_adr_preservation.py`, which is out of this Plan's scope. The revision evidence is recorded
  in `## Review Triggers` instead.
- Resolved 2026-10-17: removing the backticked `agent/services/security_audit.py::audit_security_defaults()`
  citation is an ERROR-level finding under `tools/check_adr_preservation.py:156-161`, not the WARNING this
  document's `Method` anticipated, and the tool has no override flag. Both deleted-module tokens are therefore
  kept in `## Review Triggers` as a historical record of the fired trigger, while `## Exceptions` no longer
  grants a cross-config read.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the current gate results before editing | Completed | 2026-10-17 | 2026-10-17 | ADR preservation gate run before editing, clean baseline |
| 2 | Delete the audit exception bullet | Completed | 2026-10-17 | 2026-10-17 | audit exception bullet deleted, the EventBus bullet and the closing unconditional paragraph unchanged |
| 3 | Reword Decision item 7 and add the self-validation item | Completed | 2026-10-17 | 2026-10-17 | item 7 states the rule without the exception clause, the self-validation rule is appended as item 16 rather than inserted after item 11 so items 12 to 15 keep their numbers |
| 4 | Re-base the `:231` Verification row and add posture rows | Completed | 2026-10-17 | 2026-10-17 | verification row re-based to the no-Agent-import wording with both citations and the contract name unchanged, one self-validation row citing a bare test directory added, one startup validation bullet added |
| 5 | Update Security Consequences and Review Triggers | Completed | 2026-10-17 | 2026-10-17 | security consequences bullet added, the two audit triggers replaced by one fired trigger line that keeps both deleted module tokens because removing the audit citation is an ERROR-level finding not the anticipated WARNING |
| 6 | Run the ADR and docs gates | Completed | 2026-10-17 | 2026-10-17 | only the mapped Decision WARNING remains, all ADR and docs gates clean, the stale detector needed the import-linter config key written without backticks because it is not a source symbol |

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
- **Requirement ID**: `REQ-018` (align ADR-002 with per-server self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `docs/10_adr/adr_02_002_config-isolation.md`
