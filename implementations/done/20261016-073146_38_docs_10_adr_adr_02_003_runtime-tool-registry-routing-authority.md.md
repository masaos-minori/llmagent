## Goal

Record posture-gated Registry construction in ADR-003 as a startup-time static-availability decision, and confirm
that it does not introduce Hot Rediscovery or any runtime change to LLM visibility (`REQ-019`).

## Scope

- One modified document `docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md` (25463 bytes): one
  new `### Decision Details` item, two `## Verification` rows, and one `## Review Triggers` line.
- No code is edited in this row; row `19` adds `allowed_servers` to `RuntimeToolRegistry` and row `50` (planned
  amendment) wires it at the Discovery call site.

## Assumptions

- Current file verified: `## Decision` `:67`, `### Decision Details` `:69-93` (item 11 at `:88` separates Static
  Availability from Dynamic Health; item 12 at `:89`; item 14 at `:91` states that reflecting Discovery-derived
  definitions requires a full restart; item 15 at `:92` limits the static `ToolRegistry` to Drift validation),
  `### Responsibility Boundaries` `:95-101`, `## Invariants` `:203-213`, `## Failure Policy` `:215-233`,
  `## Data Ownership and Persistence` `:235-243`, `## Verification` `:245-277`, `### Automated Tests` table
  `:249-259` (Drift row at `:254` cites
  `tests/agent/shared/test_startup_validation_pipeline.py`), `## Implementation Notes` `:279-285`,
  `## Known Deviations` `:287-289` ("Not applicable"), `## Review Triggers` `:291-303` (last line at `:303`
  reads "Changes to per-MCP-server mandatoriness and failure policy (linked with ADR-004)"), `## Approval`
  `:305-327`, `## Related ADRs` `:329-333`, `## Implementation References` `:335-348`.
- `## Implementation References` `:337` cites `scripts/shared/runtime_tool_registry.py::RuntimeToolRegistry`,
  which matches `_TEST_REF_RE` (`` `([^`\s]+\.py::[^`\s]+)` ``) and is therefore ERROR-monitored for add or
  remove (`tools/check_adr_preservation.py:156-161`).
- `docs/10_adr/adr_01_index.md:113` cites
  `tests/agent/test_tool_policy_comprehensive.py::TestClassifyOperationType` and
  `tests/agent/services/test_mcp_tool_discovery.py::TestWriteClassificationFinding`; both survive this Plan.
- `tools/check_adr_structure.py` check (b) warns when a `scripts/` or `tests/` path cited under
  `## Implementation Notes` is absent from `## Implementation References`, and `## Implementation References` may
  not gain items (`tools/check_adr_preservation.py:148-154`). New evidence therefore goes into `## Verification`.
- This file contains zero `MUST`/`MUST NOT`/`SHOULD`/`MAY` tokens, so the normative-count WARNING cannot fire.
- INV-06 already states that a statically disabled Tool must not be exposed to the LLM as executable, and INV-07
  states that Dynamic Health state must not change LLM visibility. Posture gating is a startup-time decision made
  once, so it aligns with INV-06 and does not touch INV-07.

## Design decisions

- Describe posture gating as Static Availability, not as a new subsystem. `### Decision Details` item 11 at `:88`
  already defines Static Availability as "a value based on configuration, computed by each MCP server at Discovery
  time and taken in once at startup". A server-side posture result is exactly that shape: computed by the server,
  read once at startup, and it decides exposure. Framing it this way keeps INV-06/INV-07 intact and avoids
  rewriting Decision item 11.
- Add one new Decision Details item instead of editing items 11, 12, or 14. Editing item 11 would read as a
  reversal of the Static/Dynamic separation the ADR exists to establish, and editing item 14 would weaken the
  no-Hot-Rediscovery rule this row is meant to reaffirm.
- State explicitly that posture exclusion is applied at `RuntimeToolRegistry` construction and is not re-evaluated
  at runtime. A server that repairs its posture needs a restart, which is the same rule item 14 already states for
  Discovery-derived definitions.
- Keep `## Failure Policy` unchanged. Whether a posture failure is Fail-Fast is ADR-004's classification (row
  `39`), and `docs/10_adr/adr_01_index.md:89` records that ADR-004 owns failure classification. Recording the
  exclusion mechanism here and the classification there keeps one authority per rule.
- Cite new evidence as bare paths (`tests/agent/test_mcp_health_posture.py`,
  `tests/shared/test_runtime_tool_registry.py`) rather than `path.py::name` node ids, because adding a
  `path.py::name` citation is an ERROR finding (`tools/check_adr_preservation.py:159-161`).

## Alternatives considered

- Reword INV-06 to "A statically disabled or posture-excluded Tool must not be exposed to the LLM as executable" —
  rejected: `INV-NN` text change is an ERROR finding (`:143-145`) with no override flag.
- Add a `## Posture Gating` H2 — rejected: H2 sequence change is an ERROR finding (`:131-136`), and
  `check_adr_structure.py` check (c) restricts ADR headings to the standardized list and order.
- Record the gate in `## Implementation Notes` — rejected: `check_adr_structure.py` check (b) would warn that the
  newly named `scripts/` path is absent from `## Implementation References`, which cannot gain items.
- Treat posture exclusion as a Dynamic Health state so the Registry can re-gate at runtime — rejected: it
  contradicts INV-07 and Decision item 12, and it would introduce Hot Rediscovery, which this Plan explicitly
  does not add.
- Leave ADR-003 unchanged and document gating only in `docs/23_agent/agent_06_*` — rejected: ADR-003 is the
  canonical authority for Registry authority and Tool exposure, so an undocumented gate would leave the ADR
  claiming that everything discovered at startup is registered.

## Implementation
### Target file

`docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md` (modify)

### Procedure

1. Add one `### Decision Details` item after item 15 at `:92`: a server whose posture contract reports `FAILED`
   is excluded from `RuntimeToolRegistry` at construction, so its Tools are neither exposed to the LLM nor
   routable; the exclusion is decided once at startup, is not a Dynamic Health state, and is not re-evaluated
   until the process restarts.
2. Add one `### Automated Tests` row after `:258` for posture-gated registration, citing bare paths
   (`tests/shared/test_runtime_tool_registry.py`, `tests/agent/test_mcp_health_posture.py`), Verifies `INV-06`.
3. Add one `### Startup Validation` bullet under `### Startup Validation` at `:260+` stating that posture results
   are evaluated before the Registry is built, and that a posture failure aborts startup rather than producing a
   partially populated Registry.
4. Add one `## Review Triggers` line after `:303` recording that per-server self-validation and the posture
   contract were introduced on 2026-10-16 (linked with ADR-002 and ADR-004).
5. Keep `:1-92`, `:95-258`, `:260-289`, `:291-303`, `:305-348` unchanged, including `## Known Deviations` at
   `:287-289`, the whole `## Approval` section, and the `scripts/shared/runtime_tool_registry.py::RuntimeToolRegistry`
   citation at `:337`.

### Method

- Land this row after rows `19` and `50` are merged, so the Decision text describes a parameter that exists.
- Run `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md`
  before and after. The only expected WARNING is the `## Decision` text change; map it in the commit message as
  "one Decision Details item added; items 11, 12, 14, 15 unchanged".

### Details

- The file grows by roughly five lines; nothing is removed.
- The new Decision item must not use the words `MUST`, `MUST NOT`, `SHOULD`, or `MAY`, so the normative-count
  check stays at zero for both versions.
- The new Verification rows use the same six-column table shape as `:249-258`.

## Compatibility considerations

- `docs/10_adr/adr_02_003_*:254`'s citation of `tests/agent/shared/test_startup_validation_pipeline.py` must stay
  present; row `35` keeps that file, and this row does not remove the token.
- `docs/10_adr/adr_01_index.md:113` (row `36`) and `docs/10_adr/adr_02_004_*` (row `39`) describe the same gate;
  their wording must match this Decision item.
- `docs/23_agent/agent_06_*` tool-routing documents describe Registry construction; they are follow-up documents.

## Security considerations

- The ADR text is what prevents a future change from registering tools from a server that failed validation. An
  undocumented gate is a gate that can be removed by a reader who never sees it.
- Keeping posture gating out of Dynamic Health preserves the existing guarantee that a transient network failure
  cannot silently change what the LLM is allowed to call.

## Rollback considerations

- Restore with `git checkout -- docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md`. Revert it
  together with rows `19` and `50`; reverting the code rows alone would leave the ADR describing a gate that no
  longer exists.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| ADR content preserved | `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md` | no ERROR; one mapped `## Decision` WARNING |
| Matrix citations resolve | `uv run python tools/check_adr_invariant_matrix.py` | no finding |
| ADR structure | `uv run python tools/check_adr_structure.py` | no ERROR, no Notes/References drift WARNING |
| Docs structure | `uv run python tools/check_docs_structure.py` | clean |
| Docs content policy | `uv run python tools/check_docs_content_policy.py --strict` | clean |
| Gate exists in code | `uv run pytest tests/shared/test_runtime_tool_registry.py` | posture-gated cases pass (row `19`) |

## Completion criteria

- A Decision Details item states posture-gated Registry construction, its startup-only nature, and the restart
  requirement.
- Decision items 11, 12, 14, and 15 and INV-01 through INV-09 are byte-identical to before the edit.
- The `scripts/shared/runtime_tool_registry.py::RuntimeToolRegistry` citation is unchanged.
- `check_adr_preservation.py` reports no ERROR and `check_adr_structure.py` reports no drift WARNING.

## Out of scope

- Adding `allowed_servers` to `RuntimeToolRegistry` (row `19`).
- Wiring `allowed_servers` at the Discovery call site (row `50`, planned Plan amendment).
- Classifying posture failures as Fail-Fast (row `39`).
- `docs/23_agent/agent_06_*` updates (follow-up).

## Confirmation outcomes

- Resolved 2026-10-17: `## Failure Policy` is not edited. ADR-004 owns failure classification
  (`docs/10_adr/adr_01_index.md:89`), so naming posture failures there (row `39`) and naming only the exclusion
  mechanism here keeps one authority per rule and avoids mapping a second `## Failure Policy` WARNING.
- Resolved 2026-10-17: `tools/check_docs_structure.py:90` caps this file at 26592 bytes, so the four additions
  were worded to fit inside that cap. The cap was not raised, because amending that tool is outside this Plan's
  frozen target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the current gate results before editing | Completed | 2026-10-17 | 2026-10-17 | ADR preservation, structure, reference, matrix, docs structure, content policy, and agent consistency gates all clean before editing |
| 2 | Add the posture-gating Decision Details item | Completed | 2026-10-17 | 2026-10-17 | item 16 appended after item 15, items 11 12 14 and 15 byte-identical, no normative word used |
| 3 | Add the Verification rows and Startup Validation bullet | Completed | 2026-10-17 | 2026-10-17 | one automated tests row citing two bare test paths plus one startup validation bullet, the bullet names the required and non-required split because only a required server posture failure aborts startup, verified against startup_validation.py step 2 running before step 4 |
| 4 | Add the Review Trigger line | Completed | 2026-10-17 | 2026-10-17 | review trigger line appended after the central-availability trigger, that trigger left unchanged because availability is still computed per server |
| 5 | Run the ADR and docs gates | Completed | 2026-10-17 | 2026-10-17 | only the mapped Decision WARNING remains, the 26592 byte cap needed the four additions trimmed to 1077 bytes, 42 passed in the registry test file |

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
- **Requirement ID**: `REQ-019` (align ADR-003 with posture-gated discovery and no Hot Rediscovery)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md`
