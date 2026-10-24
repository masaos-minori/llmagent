# Plan: `masked_fields` default — replace the inert `file_content` name with real file-write argument keys

## Goal
- Make the shipped `masked_fields` default redact something on a default installation by replacing
  `["file_content"]` with the argument key names the file write tools actually use
  (`["content", "old_text", "new_text"]`) in both code defaults, the repo TOML, the pinned default
  test, and the one docs bullet.

## Priority
Medium

## Scope
- **In-Scope**: the default value in `scripts/agent/config_dataclasses.py:182` and
  `scripts/agent/config_section_builders.py:204-205`; `config/agent.toml:98`; the pinned assertion in
  `tests/agent/test_config_builders.py:155`; new default-end-to-end masking tests in
  `tests/agent/test_tool_result_formatter.py` and a default-names case in
  `tests/agent/test_tool_approval_preflight.py`; the `masked_fields` bullet in
  `docs/23_agent/agent_08_03_configuration-tools-memory.md`.
- **Out-of-Scope**: `mask_args` implementation and its callers (frozen by
  `plans/done/20261023-072425_plan.md`); which sinks are masked
  (approval previews stay unmasked); `plan_blocked_tools` or any other `ToolConfig` field; masking
  tool results; pattern/glob/path-based matching; `/opt/llm/config/agent.toml` (deployed copy —
  handled as a gated deploy step, Phase 4, requiring explicit user confirmation for shared production
  config).
- **Dependencies**: the nested-masking prerequisite is already satisfied: `mask_args` masks at any
  depth today (commit `3cdacc601` "feat(agent): mask masked_fields keys at any depth in mask_args",
  verified 2026-10-24), and its procedures sit in `implementations/done/`
  (`20261024-124138_01_scripts_agent_tool_result_formatter.py.md`, `_02_...`). The Issue's ordering
  constraint ("must land after, or in the same release as, the nested-masking work") is therefore
  already met; no sequencing phase is needed.

## Background
`plans/20261023-072425_plan.md` `UNK-01` asked whether production config relies on
`masked_fields = ["file_content"]`. That Plan recorded the correction that `file_content` matches no
tool argument key, and the owner decided (2026-10-24) to route the default-value change to this
separate issue. Re-verified on 2026-10-24: `file_content` appears only as GitHub-service internal
symbols, never as an argument-key name in any registered tool schema.

## Problem
With the shipped default, `mask_args()` masks no key for any tool this project registers, because
masking compares argument keys and `file_content` is not one. The real keys are `content` for
`write_file` (`scripts/mcp_servers/file/write_tools.py:22`, required at `:31`) and `old_text` /
`new_text` inside `edit_file`'s `edits` list items (`write_tools.py:55`, `:59`, required at `:64`) —
both confirmed 2026-10-24. The three default definitions are `config_dataclasses.py:182`,
`config_section_builders.py:204-205`, and `config/agent.toml:98` (the deployed
`/opt/llm/config/agent.toml:98` was verified identical). The only masking tests today pass their own
values (`tests/agent/test_tool_approval_preflight.py:418`, `:433` use `masked_fields=["secret"]`), so
the default's inertness is untested end to end.

## Reason for Change
The closed Plan made recursive masking a documented logging/audit boundary. A default list naming no
real argument means the documented boundary protects nothing by default and the nesting feature has
no observable effect in a default deployment.

## Implementation Intent
Change only the default value (same list in all three definitions), the one pinned default assertion,
and the one docs bullet. Add default-driven regression tests. Do not touch `mask_args`, its callers,
or which sinks are masked. Apply the deployed-copy change only through the gated deploy step.

## Requirements
- `REQ-001`: The default `masked_fields` becomes `["content", "old_text", "new_text"]` in
  `config_dataclasses.py:182` (`field(default_factory=...)`) and `config_section_builders.py:204-205`
  (`_get_or_default` fallback) — both changed in lockstep so code-default and builder-default agree.
- `REQ-002`: `config/agent.toml:98` becomes `masked_fields = ["content", "old_text", "new_text"]`,
  staying in the same flat top-level region under the `# ── Security ──` comment (no section move;
  `masked_fields` currently matches nothing there — the first table is `[diagnostics]` at `:230`).
- `REQ-003`: `file_content` is replaced outright, not kept alongside the new names: it names no
  argument key in any registered tool schema (verified 2026-10-24), so retaining it protects nothing
  and only adds noise. Deployments that set `masked_fields` explicitly keep their own value.
- `REQ-004`: `tests/agent/test_config_builders.py:155` pins the new default; no other test depends
  on the old default value (verified: all other `masked_fields` test fixtures override the value
  explicitly; `tests/agent/commands/test_cmd_config_char.py` snapshot assertions are substring
  matches and pass unchanged — verified 2026-10-24).
- `REQ-005`: A default-config end-to-end regression test builds a config through the default path,
  passes `write_file`-shaped args (`{"path", "content"}`) and `edit_file`-shaped args
  (`{"path", "edits": [{"old_text", "new_text"}]}`) through `mask_args(args, cfg.tool.masked_fields)`,
  and asserts `***` at `content`, `edits[*].old_text`, and `edits[*].new_text`.
- `REQ-006`: `docs/23_agent/agent_08_03_configuration-tools-memory.md` `masked_fields` bullet states
  the new default key names, that they name file-write tool arguments, and the documented split:
  masking applies to logs/audit only — interactive approval previews stay unmasked (closed-Plan
  `REQ-001` decision).

## Implementation Target Files
**Freeze status**: Frozen (validated 2026-10-24 per `rules/workflow-lifecycle.md` Implementation
Target Files Validation (Plan Freeze) — all rows `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Change `ToolConfig.masked_fields` default factory | One of the two code defaults; pins the value used when `ToolConfig()` is constructed directly | REQ-001, REQ-003; AC-1 | `masked_fields: list[str] = field(default_factory=lambda: ["file_content"])` measured at `:182` (2026-10-24) | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/config_section_builders.py` | Change `ToolConfigBuilder.build` fallback default | The other code default; must match the dataclass default | REQ-001; AC-1 | `_get_or_default(cfg, "masked_fields", _get_list, ["file_content"])` measured at `:204-205` (2026-10-24) | `tests/agent/test_config_builders.py` | Verified |
| `config/agent.toml` | Change `masked_fields` value in place | The repo config ships the same inert default; deployments inherit it | REQ-002, REQ-003; AC-1 | `masked_fields = ["file_content"]` at `:98` in the flat `# ── Security ──` region; first table `[diagnostics]` at `:230` (read 2026-10-24) | `tests/agent/test_config_builders.py` (builder path with repo file available in tree) | Verified |
| `tests/agent/test_config_builders.py` | Update the pinned default expectation | `:155` pins `["file_content"]` in the `DEFAULTS` dict; AC-2 requires the new value asserted | REQ-004; AC-2 | `"masked_fields": ["file_content"],` measured at `:155`; the explicit-override case at `:192` is unaffected (read 2026-10-24) | this file | Verified |
| `tests/agent/test_tool_result_formatter.py` | Add default-config end-to-end masking tests | The Issue's Testing Expectations: default-built config, `write_file`/`edit_file`-shaped args, `***` at real key names; this file already tests `mask_args` | REQ-005; AC-3 | File exists and exercises `mask_args` (`test_empty_masked_fields_returns_unchanged` at `:59`, read 2026-10-24); `mask_args` masks at any depth (commit `3cdacc601`) | this file | Verified |
| `tests/agent/test_tool_approval_preflight.py` | Add a default-names audit case | The Issue's Testing Expectations: extend the masking coverage from `["secret"]` fixtures to the real default names on the audit path | REQ-005; AC-3 | `test_masked_fields_applied_to_args` (`:417`) and the nested sibling (`:432`) both use `masked_fields=["secret"]` (read 2026-10-24) | this file | Verified |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Update the `masked_fields` bullet | The only prose mention of the setting; must state the new default names and the logs/audit-only split | REQ-006; AC-5 | Bullet at `:32` "masked_fields replaces configured argument keys" (read 2026-10-24); churn measured 18 commits/30d (Issue cites 17 — re-measured) | `uv run python tools/check_docs_consistency.py --domain agent` + docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/file/write_tools.py` | Authoritative argument names: `content` (`:22`, required `:31`), `old_text`/`new_text` inside `edits` items (`:55`, `:59`, required `:64`); unmodified | REQ-001, REQ-003 |
| `scripts/mcp_servers/github/tools_file.py` | GitHub file-write tools also carry `content` (`:94`) and `content` inside `edits` items (`:138`): the new default masks those bodies in logs/audit too — consistent with the intent, must be mentioned in the docs bullet; unmodified | REQ-006 |
| `scripts/agent/tool_result_formatter.py` | `mask_args`/`_mask_value` are NOT modified (Issue's instruction); recursion at any depth verified via commit `3cdacc601`; the Issue's constraint citing "top-level-only mask_args (`:42-47`)" is disconfirmed | Dependencies |
| `scripts/agent/commands/cmd_config_display.py` (`:107-111`) | Renders `masked_fields` in `cmd_config` output; value-agnostic join rendering; unmodified | REQ-004 |
| `tests/agent/commands/test_cmd_config_char.py` | Verified non-impact: `_make_ctx` builds bare `ToolConfig()`, but the snapshot assertions (`:125-173`) are substring matches (`expected_snippets`), so the new rendered value passes unchanged | REQ-004 |
| `tests/integration/test_agent_integration.py` (`:38`) and other fixtures with explicit `"masked_fields": []` | Enumerated 2026-10-24: explicit overrides, unaffected by the default change | REQ-004 |
| `docs/23_agent/agent_13_reference-api-generated.md` (`:184`) | Second `masked_fields` mention (Issue claimed the `agent_08_03` bullet is the only one); it is a generated API table naming the `mask_args` parameter — signature unchanged, no edit needed; regeneration via `tools/generate_reference_table.py` stays consistent | Documentation Impact |
| `implementations/done/20261024-124138_01_scripts_agent_tool_result_formatter.py.md` (`_02` sibling) | Proof the nested-masking prerequisite already landed and is archived | Dependencies |
| `plans/done/20261023-072425_plan.md` | Source `UNK-01`, the frozen six rows this issue must not disturb, and the logs/audit-only boundary (`REQ-001`) | Scope, Out-of-Scope |
| `/opt/llm/config/agent.toml` (`:98`) | Deployed copy verified identical to `config/agent.toml` 2026-10-24; changed only via the gated deploy step (Phase 4), never a direct edit in this work | REQ-002 (Phase 4 gate) |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002, REQ-003): `grep -n "file_content" scripts/agent/config_dataclasses.py
  scripts/agent/config_section_builders.py config/agent.toml` reports no `masked_fields` default
  using `file_content` (the GitHub `get_file_contents` implementation symbols elsewhere in the repo
  are not `masked_fields` defaults and may remain).
- AC-2 (REQ-004): `uv run pytest tests/agent/test_config_builders.py -q` passes with the new default
  asserted.
- AC-3 (REQ-005): `write_file`-shaped and `edit_file`-shaped args under default config produce `***`
  at `content` / `old_text` / `new_text` in audit events (`scripts/agent/tool_audit.py`) and in the
  REPL tool-call line (`scripts/agent/tool_runner.py`), asserted by the new tests without explicit
  `masked_fields` configuration.
- AC-4: Issue AC-4 corrected — the named tools `tools/check_config_keys.py` and
  `tools/check_config_defaults.py` do not exist in this repository (verified 2026-10-24 by directory
  listing and repo-wide `find`). Their function is covered by the real equivalents:
  `uv run python tools/check_docs_consistency.py --domain agent` (exists) for the docs bullet, and
  the full `rules/toolchain.md` sequence.
- AC-5 (REQ-006): The docs bullet is updated and `uv run python tools/check_docs_consistency.py
  --domain agent` plus the docs gates report no findings.
- AC-6: The full `rules/toolchain.md` validation sequence passes with no new failure.

## Tests
- Unit (REQ-004): `tests/agent/test_config_builders.py` `DEFAULTS` expectation → `["content",
  "old_text", "new_text"]`; the explicit-override case (`:192`) untouched.
- Unit (REQ-005, in `tests/agent/test_tool_result_formatter.py`): config built through the default
  path; `write_file`-shaped args → `content` becomes `***`; `edit_file`-shaped args → `***` at
  `edits[0]["old_text"]` and `edits[0]["new_text"]` (nesting already works via commit `3cdacc601`).
- Unit (REQ-005, in `tests/agent/test_tool_approval_preflight.py`): sibling of
  `test_masked_fields_applied_to_args` built with the default list instead of `["secret"]`, asserting
  the sensitive value is absent from the serialized audit payload.
- Regression (REQ-004): `tests/agent/commands/test_cmd_config_char.py` snapshot substring tests pass
  unchanged (verified reasoning above); full `tests/agent` suite passes.
- Integration (AC-6): `uv run pytest tests/integration -q` unchanged (its fixture overrides
  `masked_fields=[]`).

## Documentation Impact
Required, one bullet, driven by REQ-006:
- `docs/23_agent/agent_08_03_configuration-tools-memory.md:32`: state the default key names
  `["content", "old_text", "new_text"]`, that they name `write_file`/`edit_file` (and GitHub
  file-write) argument keys, and the logs/audit-only split that keeps approval previews unmasked.
- `docs/23_agent/agent_13_reference-api-generated.md` (generated API table) needs no edit: the
  `mask_args` signature is unchanged.
- The Issue's pointer at `docs/00_index.md` "AgentConfig / config constants" indexing (for
  `agent_08_01`) applies only if a new key-name table is added; this Plan edits the existing bullet
  in place, so no new index entry is created. Verify at implementation time that no docs gate
  demands otherwise.

## Assumptions
- `file_content` is replaced outright, not kept for backward compatibility (Issue open question
  closed as this Plan's decision): the name matches no argument key, so keeping it preserves no
  behavior worth protecting; deployments relying on the shipped value gained no protection from it,
  and the change strictly increases redaction. Owner may re-add it as a no-op entry if they prefer.
- `content` is masked in logs/audit despite unmasked approval previews (Issue open question closed):
  the closed Plan fixed masking as a logs/audit-only boundary; previews and audit rows serve
  different purposes. REQ-006 makes the split explicit in the docs so the two features do not read
  as contradictory.
- New default list is exactly `["content", "old_text", "new_text"]` (the Issue's candidate), chosen
  after verifying `write_tools.py` as the Issue's instruction requires; no other registered tool
  argument names overlap harmfully (`content` also appears in GitHub file-write schemas — masking
  there is intended, not collateral).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the docs gates will demand an additional `docs/00_index.md` or `agent_08_01` cross-reference once the bullet lists key names | Gate behavior is only determinable by running the gates after the edit | Phase 3 runs `check_docs_consistency --domain agent` and the docs gates; if they flag a missing reference, add the index entry in the same phase (the Issue's Documentation Impact already prescribes this fallback) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Modify (one default) | Medium — `ToolConfig` is constructed widely, but only the default list value changes; every call site that reads `masked_fields` is a masking sink already decided by the closed Plan | — (not re-measured; hot core file) | High | rsynced (deployed) |
| `scripts/agent/config_section_builders.py` | Modify (one fallback) | Low-Medium — builder fallback only applies when the key is absent from config | — | High | rsynced (deployed) |
| `config/agent.toml` | Modify (one value) | Medium — default deployment config; deployments with explicit values unaffected | — | High | rsynced; deployed copy `/opt/llm/config/agent.toml` update is Phase 4, gated on explicit user confirmation |
| `tests/agent/test_config_builders.py` | Modify (one expectation) | Low | — | High | rsynced |
| `tests/agent/test_tool_result_formatter.py` | Modify (add tests) | Low | — | High | rsynced |
| `tests/agent/test_tool_approval_preflight.py` | Modify (add one case) | Low | — | High | rsynced |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Modify (one bullet) | Low | 18 (Issue cited 17; re-measured 2026-10-24) | High | rsynced |

## Design
- **Task size**: Path B. Seven repo target files (six from the Issue's list minus the deployed copy,
  which becomes a gated deploy step, plus the two new-test files from its Testing Expectations).
- **Architecture**: no import or signature changes. `config_dataclasses.py` and
  `config_section_builders.py` both sit in `scripts/agent` config layer; `importlinter` contracts are
  untouched because no new imports appear. `mask_args`, `tool_audit.py`, `tool_runner.py` are read
  only — the Issue's instruction forbids changing masking behavior, only its default input.
- **Two-default consistency**: the dataclass default (used when `ToolConfig()` is constructed
  directly, e.g. test helpers) and the builder fallback (used when the key is absent from TOML) must
  be changed together, otherwise a deployment without the TOML key and a direct construction would
  disagree. Both become the same literal list.
- **TOML region constraint (verified)**: `config/agent.toml:98` lives in the flat top-level region
  under `# ── Security ──`; the first table header is `[diagnostics]` at `:230`. The edit replaces the
  value in place; no key move, no `[tool]` re-verification needed.
- **Deployed copy**: `/opt/llm/config/agent.toml:98` is verified identical today. It is shared
  production config: Phase 4 syncs it only after explicit user confirmation (the Issue's own gate),
  matching `deploy.sh`'s config rsync path. No direct edit during Phases 1-3.
- **Prerequisite state (Issue constraint corrected)**: the Issue's constraint cites a top-level-only
  `mask_args` and orders this change after the nested-masking procedures. Current tree contradicts the
  premise: `mask_args` masks at any depth (commit `3cdacc601`) and those procedures are in
  `implementations/done/`. The ordering requirement is already satisfied; `edit_file`'s nested
  `old_text`/`new_text` will be masked the moment the new default lands.
- **Issue AC-4 corrected**: `tools/check_config_keys.py` and `tools/check_config_defaults.py` do not
  exist (verified by `tools/` listing and repo-wide `find` 2026-10-24). Substitute real gates:
  `tools/check_docs_consistency.py --domain agent`, the config test suite, and the full
  `rules/toolchain.md` sequence.

## Implementation steps
1. **Phase 1: Failing default tests first**
   - [ ] Add the default-config masking tests to `tests/agent/test_tool_result_formatter.py` and the
     default-names audit case to `tests/agent/test_tool_approval_preflight.py` (REQ-005). Expect them
     to fail against the current `file_content` default.
2. **Phase 2: Change the defaults in lockstep**
   - [ ] Update `config_dataclasses.py:182` and `config_section_builders.py:204-205` to
     `["content", "old_text", "new_text"]` (REQ-001, REQ-003).
   - [ ] Update `config/agent.toml:98` in place (REQ-002).
   - [ ] Update `tests/agent/test_config_builders.py:155` to the new expected default (REQ-004).
   - [ ] Run `uv run pytest tests/agent/test_config_builders.py
     tests/agent/test_tool_result_formatter.py tests/agent/test_tool_approval_preflight.py -q` — all
     pass.
3. **Phase 3: Documentation and full validation**
   - [ ] Update the `masked_fields` bullet in `agent_08_03` with the new names and the
     logs/audit-only split (REQ-006).
   - [ ] Verification pass: AC-1 grep; `uv run python tools/check_docs_consistency.py --domain
     agent`; docs gates (`check_docs_quality.py`, `check_docs_structure.py "docs/**/*.md"`,
     `check_docs_content_policy.py`); `rules/toolchain.md` sequence (`ruff format`/`check`,
     `mypy --no-namespace-packages scripts/`, `bandit -r scripts/ -c pyproject.toml -ll`,
     `PYTHONPATH=scripts uv run lint-imports`, `uv run pytest tests/agent -q`,
     `uv run pytest tests/integration -q`, coverage + diff-cover ≥ 90% on changed lines,
     `uv run pre-commit run --all-files`).
4. **Phase 4: Deployed config sync (confirmation-gated)**
   - [ ] Confirm with the user, then sync `config/agent.toml` to `/opt/llm/config/agent.toml` per
     `deploy.sh` / `skills/deploy/SKILL.md`; restart affected agent services; smoke-check one
     `write_file` call shows `***` for `content` in the audit row.
     Gate: no edit of `/opt/llm/config/agent.toml` without explicit user confirmation (Issue
     constraint; AGENTS.md shared-infrastructure rule).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py` | Unit + grep | `uv run pytest tests/agent/test_config_builders.py -q`; `grep -n "file_content" scripts/agent/config_dataclasses.py scripts/agent/config_section_builders.py config/agent.toml` | New default asserted; grep empty for `masked_fields` defaults |
| `config/agent.toml` | Builder-path unit | `uv run pytest tests/agent/test_config_builders.py -q` + `uv run python tools/check_docs_consistency.py --domain agent` | Config loads with new list; no key-consistency finding |
| `tests/agent/test_tool_result_formatter.py` | Regression (new default tests) | `uv run pytest tests/agent/test_tool_result_formatter.py -q` | `***` at `content`, `edits[*].old_text`, `edits[*].new_text` under default config |
| `tests/agent/test_tool_approval_preflight.py` | Regression (new audit case) | `uv run pytest tests/agent/test_tool_approval_preflight.py -q` | Default-names case passes; existing `["secret"]` cases unchanged |
| Whole change | Suite + toolchain | `uv run pytest tests/agent -q`; `uv run pytest tests/integration -q`; `rules/toolchain.md` sequence; coverage + `diff-cover` ≥ 90%; `uv run pre-commit run --all-files` | No new failures |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Docs gates | `check_docs_quality.py`, `check_docs_structure.py "docs/**/*.md"`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` | No findings |
| Deployed runtime (Phase 4, gated) | Operational smoke | `deploy.sh` sync + service restart + audit.log inspection of one `write_file` call | `content` shows `***` in audit row with no explicit config |

## Risks
- **Risk**: masking `content` also masks GitHub file-write bodies and any future tool using the common
  name `content`, reducing forensic detail in audit rows for legitimate writes. → **Mitigation**:
  intended behavior per Issue intent (file bodies are the sensitive payloads); documented explicitly
  in `agent_08_03` so operators can override per deployment.
- **Risk**: the dataclass default and the builder fallback drifting if only one is edited. →
  **Mitigation**: Phase 2 edits both in one step; `test_config_builders.py` pins the builder path and
  the new default tests exercise the constructed-config path.
- **Risk**: deployments relying on the shipped default see an audit-log behavior change without a
  config change. → **Mitigation**: the change strictly adds redaction (safer direction); the docs
  bullet states the new default names so operators know what changed (Issue's backward-compat open
  question closed as a decision).
- **Risk**: `agent_08_03` is high-churn (18 commits/30d measured). → **Mitigation**: single-bullet
  edit; `plan-to-implementation-procedure` Step 2 revalidates the row before procedure generation.
- **Risk**: production config drift if Phase 4 is skipped (repo TOML vs deployed TOML diverge). →
  **Mitigation**: Phase 4 is explicit and confirmation-gated; deploy.sh config rsync is the single
  sync path; drift is visible to `tools/check_docs_consistency.py`? No — drift is caught by the
  deploy skill's "deployed files are current" verification, recorded in the Execution Status notes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: failing default-config tests (`test_tool_result_formatter.py`, `test_tool_approval_preflight.py`) | Pending | — | — | REQ-005 |
| 2 | Phase 2: default change in `config_dataclasses.py`, `config_section_builders.py`, `config/agent.toml`, pinned test | Pending | — | — | REQ-001, REQ-002, REQ-003, REQ-004 |
| 3 | Phase 3: docs bullet (`agent_08_03`) + full validation | Pending | — | — | REQ-006 |
| 4 | Phase 4: gated deploy sync of `/opt/llm/config/agent.toml` + runtime smoke | Blocked | — | — | Requires explicit user confirmation (shared production config) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | Phase 4 requires explicit user confirmation before touching `/opt/llm/config/agent.toml` (Issue constraint + AGENTS.md shared-infrastructure rule) | no | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261023-072425_plan.md` (`UNK-01`, `REQ-001` boundary)
- **Source implementation procedure**: N/A: not applicable in this phase (prerequisite procedures already in `implementations/done/`)
- **Generated at**: 20261024-221904
- **Related target files**: `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `config/agent.toml`, `tests/agent/test_config_builders.py`, `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_tool_approval_preflight.py`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem (three default definitions measured 2026-10-24) + Required Changes | `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py` | Phase 2 | AC-1 | `test_config_builders.py` default pin | Confirmed by repository evidence |
| REQ-002 | Problem `config/agent.toml:98`; Constraints (flat Security region) measured 2026-10-24 | `config/agent.toml` | Phase 2 | AC-1, AC-4 (equivalent gates) | builder-path tests | Confirmed by repository evidence |
| REQ-003 | Unresolved Questions (replace vs keep) — closed as Plan decision; `file_content` matches no arg key (re-verified) | `scripts/agent/config_dataclasses.py`, `config/agent.toml` | Phase 2 | AC-1 | grep check | Explicit in issue (decision recorded) |
| REQ-004 | Target Files `test_config_builders.py:155` measured 2026-10-24; non-impact of other fixtures verified | `tests/agent/test_config_builders.py` | Phase 2 | AC-2 | `uv run pytest tests/agent/test_config_builders.py -q` | Confirmed by repository evidence |
| REQ-005 | Testing Expectations; real names verified at `write_tools.py:22/:31/:55/:59/:64` | `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_tool_approval_preflight.py` | Phase 1, Phase 2 | AC-3 | new default-config unit tests | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; bullet at `agent_08_03:32` measured 2026-10-24; `agent_13` second mention found | `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Phase 3 | AC-5 | docs gates + `check_docs_consistency --domain agent` | Confirmed by repository evidence |
