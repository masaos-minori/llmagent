## Goal

Author the evidence-cited classification of the six `memo2.md` config-facade items
(P1-1 providers normalization, P1-2 MCP timeout keys, P1-3 result-token cap, P1-4
providers facade delegation, P2-1 unified validation, P2-2 config consistency) into this
Plan and record the conclusion that no implementation code is required (`REQ-001`-`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

Document-only (Path A). The only file modified is this Plan; no source, test, config,
schema, or deployment file is touched.

## Assumptions

- The six items to classify are those enumerated in the source issue's Required Changes;
  the issue's framing that `memo2.md` itself enumerates them is treated as framing, not as
  `memo2.md` content (the current `memo2.md` holds no such list).
- The real config architecture described in the plan's Background fully covers the six
  items; every verdict below is backed by a live citation, so nothing here is assumed
  implemented.

## Design decisions

- Verdicts are assigned by citing the mechanism that already covers each item, not by
  inventing a new one: already-implemented where a shared module exists, rejected where no
  corresponding construct exists.
- The deliverable is the classification table plus a superseded pointer for `memo2.md`; no
  facade, settings module, or config-loading code is created.

## Alternatives considered

- Creating a separate `docs/` page for the classification: rejected; the authoritative
  classification lives in this Plan, and `memo2.md` is an intentionally-untracked local
  memo, so committing a separate page would contradict its status.

## Implementation
### Target file
`plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md`

### Procedure
1. Write the evidence-cited classification table (six rows) into this Plan's `## Design`
   section with file/line citations (`REQ-001`-`REQ-006`).
2. Record the conclusion (all items already-implemented or rejected; no confirmed gap) and
   the operational `UNK-01` needs-confirmation note.
3. Record the superseded pointer for `memo2.md` in this Plan's `## Traceability` so the
   memo is not re-executed.

### Method
Verify each verdict against the current tree before recording it (`rg`/Read), per the plan's
Step 3a adversarial verification:

- P1-1 providers normalization: `rg -n "providers"` in `scripts/` and `config/` yields no
  comma-separated providers handling or normalization target → Rejected.
- P1-2 MCP timeout keys: `scripts/shared/mcp_config.py` `McpServerConfig` carries
  `call_timeout_sec`, `health_timeout`, `startup_timeout_sec` and validates them in
  `_validate_timeouts` (`:156-168`) → Already-implemented.
- P1-3 result-token cap: no `mcp_max_result_tokens` or result-token cap; only unrelated
  server result-count caps (`ins_limit`, `default_ins`) → Rejected.
- P1-4 providers facade delegation: per-domain loaders keep their own allowed files; a
  single facade weakens `ConfigLoader.restrict_to` isolation → Rejected.
- P2-1 unified validation: `scripts/agent/production_config_validator.py`
  `ProductionConfigValidator` → Already-implemented.
- P2-2 config consistency: shared `ConfigLoader` base; per-domain separation is by design →
  Already-implemented.

### Details
- The classification table already present in the plan's `## Design` section was verified
  against the current tree during this cycle (phantom files absent, claimed config keys have
  zero occurrences); no correction to the Plan was required.
- `memo2.md` is an intentionally-untracked local memo (commit `5a9fd2920`); the superseded
  marker is recorded in this Plan's Traceability rather than committed to the memo.

## Compatibility considerations

N/A: no code change; no runtime, API, or config-key compatibility surface.

## Security considerations

N/A: no code change.

## Rollback considerations

N/A: revert the Plan edit (single commit); no deployed artifact affected.

## Validation plan

- Structure: `uv run python tools/check_workitem_structure.py --file plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md` — all required `## ` sections present.
- Evidence review: grep/file citations against `scripts/`, `config/` — every verdict backed by a citation.

## Completion criteria

- Each of the six items has a recorded verdict (already-implemented / rejected) with a
  file/line citation.
- No confirmed implementation gap; if one existed it would be filed as a separate follow-up
  issue.
- No new config-loading code, facade, or settings module created; no `config/agent.toml`
  key changed.

## Out of Scope

- Implementing any facade, settings module, or providers normalization.
- Creating or reviving `agent/settings.py`, `agent/providers.py`, `mcp/config.py`,
  `mcp/toll_gate.py`, or `mcp_settings.py`.
- Adding config-loading code while an existing mechanism covers the same responsibility.
- Changing any `config/agent.toml` key.
- Modifying `memo2.md` itself during this phase.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-16 | 2026-11-16 | Evidence-cited classification verified against current tree; no correction needed |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-16 | 2026-11-16 | N/A: Path A, no code changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-16 | 2026-11-16 | Structure check + evidence review passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-16 | 2026-11-16 | N/A: no doc change in scope |

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
- **Requirement ID**: `REQ-001`-`REQ-006`
- **Source issue**: `issues/20261115-165529_cfgfacade001_config-facade-intent-rebaseline.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-092800
- **Related target files**: `plans/20261115-195055_cfgfacade001_config-facade-intent-rebaseline.md`
