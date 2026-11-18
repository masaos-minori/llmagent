# Make one source of truth for MCP retry classes

## Goal
- Make `shared.tool_constants.RETRYABLE_TOOLS` the single source of truth for MCP retry
  classification, make `config/mcp_dedup.toml [retry_class]` a load-time-validated mirror of
  it, reject unknown tool keys in that section, rename the dead `web_search` key to the real
  tool name `search_web`, fix the wrong port comment and the wrong ADR citation, and report —
  without changing — which retryable tools carry external side effects.

## Priority
Medium

## Scope
- **In-Scope**:
  - Load-time validation in `scripts/shared/mcp_dedup.py` for `[retry_class]` keys and values
    (known tool names, allowed values, per-key consistency with `RETRYABLE_TOOLS`).
  - Rename `web_search` to `search_web` in `config/mcp_dedup.toml` (value unchanged).
  - Comment fixes in `scripts/shared/tool_constants.py` (github-mcp port, ADR citation).
  - Fixture updates and new rejection/consistency tests under `tests/shared/`.
  - Documentation fixes in the MCP dedup guide and the agent tool-execution guide that
    currently misattribute the retry-class source (issue Documentation Impact trigger fired;
    see `Documentation Impact`).
- **Out-of-Scope**:
  - Changing any tool's retry class (issue constraint; requires maintainer approval).
  - Dedup storage or state-machine changes.
  - Dispatcher retry behavior beyond the load-time validation gate.
  - `scripts/agent/tool_runner.py`'s duplicated ADR citation (non-target file; tracked as a
    scope-amendment candidate in `Unknowns` UNK-03).
- **Dependencies**: N/A: none

## Background
Retry classification decides whether a failed MCP tool call may be safely re-dispatched
(replayable) or must fail closed. Two artifacts carry it today: the `RETRYABLE_TOOLS`
frozenset in `scripts/shared/tool_constants.py` (used by the Agent's `tool_runner`) and the
`[retry_class]` map in `config/mcp_dedup.toml` (used by the shared MCP dispatcher through
`shared.mcp_dedup.retry_class`). The frozenset's own comment calls it the single source of
truth but requires hand-syncing with the toml; nothing enforces the sync at load or in tests.
The issue `ADRCHK2-M06` (ADRCHK-M20, review finding N39) was filed from the consolidated ADR
review.

## Problem
Verified against current source (2026-11-18):
- `config/mcp_dedup.toml` line 49 holds `web_search = "non_retryable"`, but no MCP tool is
  named `web_search`; the real tool is `search_web` (`tool_constants.py:125`
  `WEB_SEARCH_TOOLS`; `scripts/mcp_servers/web_search/web_search_tools.py:14` `"name":
  "search_web"`). The key is dead: `retry_class("search_web")` falls through to the
  default `non_retryable` (`mcp_dedup.py:175-179`), so the entry matches no tool while the
  file header claims keys are live dispatch tool names.
- `load_dedup_config` (`mcp_dedup.py:92-164`) validates only section shapes and value types;
  unknown tool keys and invalid class values (anything other than `retryable` /
  `non_retryable`) are accepted silently. This resolves the issue's `Needs confirmation`
  item about loader behavior.
- Two consumers resolve classification independently: `scripts/agent/tool_runner.py:163-172`
  (`_classify_retry_class` from `RETRYABLE_TOOLS`, written into `workflow.sqlite`
  `tool_call_state`) vs `scripts/mcp_servers/dispatch.py:296,320,384`
  (`retry_class(name, config)` from the toml). Drift between the sources is currently
  invisible: no test compares them. (Today the effective classification is identical: the
  toml's retryable keys equal `RETRYABLE_TOOLS` exactly — confirmed by a `tomllib` diff — and
  `search_web` is `non_retryable` on both paths.)
- Comment defect 1: `tool_constants.py:133` says `# GitHub tools (github-mcp, port 8012)`;
  github-mcp's real port is 8006 (`registry/manifests/mcp_endpoints.yaml` port 8006;
  `config/agent.toml [mcp_servers.github] url`; `docs/22_mcp/mcp_01_tool_ownership_matrix.md`
  `| github-mcp | 8006 |`). 8012 belongs to cicd-mcp (same matrix). The git-mcp 8014 comment
  (`tool_constants.py:96`) is correct.
- Comment defect 2: `tool_constants.py:174` cites `(ADR-008)`. ADR-008
  (`adr_02_05_008_db-sqlite-4db-separation.md`) owns the four-database split and the
  `mcp_dedup.sqlite` disposable-cache / fail-closed-replay semantics (its Decision section),
  not retry-class ownership; the retryable/non-retryable dispatch policy lives in ADR-004
  (`adr_02_01_004_platform-environment-failure-handling-policy.md`, registered exceptions
  MCP-001/MCP-002, which themselves reference ADR-008 for the non-retryable counterpart).
  The issue's claim "ADR-008 is not about retry" is therefore partially inaccurate: ADR-008
  is about the dedup store, not about who owns retry classification.
- Risk unrecorded: all 22 members of `RETRYABLE_TOOLS` are also in
  `ALL_SIDE_EFFECTING_TOOLS` (computed set intersection; count 22 of 22). Retry safety for
  `git_push`, `github_merge_pull_request`, `delete_directory` and the rest depends entirely
  on the dedup ledger, and nothing records that.
- Documentation trigger fired: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
  claims "The recorded `retry_class` comes from `shared/mcp_dedup.py::retry_class` (owned by
  `config/mcp_dedup.toml`)" for the Agent-side recorder — contradicted by
  `tool_runner.py:163-188`, which classifies from `RETRYABLE_TOOLS`. The MCP dedup guide
  (`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, "Retry classification" bullet)
  describes only the toml side. The guide cites the two sources, so the issue's conditional
  Documentation Impact applies.

## Reason for Change
A dead config key proves the hand-sync already drifted once. The dispatcher and the Agent
read different sources for the same classification, and a future edit to either side can
silently diverge, turning a `retryable` classification into a duplicate external side effect
or a false fail-closed. The review package (ADRCHK2-M06) asks for one source with the other
derived or checked.

## Implementation Intent
- Declare `RETRYABLE_TOOLS` (code) the owner; `config/mcp_dedup.toml [retry_class]` becomes a
  mirror that the loader refuses to accept unless it agrees with the owner key-by-key.
- At load time, reject unknown tool names, disallowed class values, and per-key
  classification mismatches (`ConfigParseError`, fail closed).
- Rename the dead key; fix the two comments; add tests that fail on disagreement between the
  sources; produce a maintainer-facing report of retryable side-effect tools without
  reclassifying anything.

## Requirements
- `REQ-001`: `scripts/shared/tool_constants.py RETRYABLE_TOOLS` is the single source of retry
  classification; `config/mcp_dedup.toml [retry_class]` is a mirror validated against it.
- `REQ-002`: `load_dedup_config` rejects, with typed `ConfigParseError`, any `[retry_class]`
  key that is not a known MCP tool name, any value not in `{retryable, non_retryable}`, and
  any key whose value contradicts `RETRYABLE_TOOLS` membership.
- `REQ-003`: Rename the toml key `web_search` to `search_web` (value `non_retryable`
  unchanged) and correct its grouping comment.
- `REQ-004`: Fix the github-mcp port comment in `tool_constants.py` (8012 -> 8006).
- `REQ-005`: Fix the retry-class comment's ADR citation in `tool_constants.py`: cite ADR-004
  for the retryable/non-retryable dispatch policy; reference ADR-008 only for the dedup-store
  semantics.
- `REQ-006`: Report the retryable tools with external side effects (the 22-tool table in
  `Design`) for a maintainer decision; change no classification.
- `REQ-007`: Correct the docs guides that misattribute the Agent-side recorded `retry_class`
  source and describe the two-source relationship.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/tool_constants.py` | Comment fixes only: port comment and ADR citation | Wrong port server name and wrong ADR citation | REQ-004, REQ-005 / AC-4 | `tool_constants.py:133` (8012 vs mcp_endpoints.yaml 8006); `tool_constants.py:174` (ADR-008 vs adr_02_01_004 MCP-001/002) | `tests/shared/test_tool_constants.py` (imports module; behavior unchanged) | Verified |
| `config/mcp_dedup.toml` | Rename `web_search` key to `search_web`; update grouping comment and header wording | Dead key matches no tool; header claims keys are live tool names | REQ-001, REQ-003 / AC-3 | `config/mcp_dedup.toml:48-49`; `tool_constants.py:125` (`search_web` is the tool name) | `tests/shared/test_tool_constants.py` (new consistency test reads this file) | Verified |
| `scripts/shared/mcp_dedup.py` | Add load-time `[retry_class]` validation: known tool names, allowed values, per-key consistency with `RETRYABLE_TOOLS` | Loader currently accepts unknown keys and invalid values silently | REQ-001, REQ-002 / AC-1 | `mcp_dedup.py:127-155` (validation today), `mcp_dedup.py:175-179` (`retry_class` default) | `tests/shared/test_mcp_dedup.py` (new rejection tests) | Verified |
| `tests/shared/test_mcp_dedup.py` | Update `TestConfigValidation` fixtures to valid tool names; add unknown-key, invalid-value, and mismatch rejection tests | Fixtures use non-tool names (`web_search`, `mdq_rag_query`) that the new gate rejects | REQ-002 / AC-1 | `test_mcp_dedup.py:301,313-322` (current fixtures) | new `TestConfigValidation` test methods | Verified |
| `tests/shared/test_tool_constants.py` | Add cross-source consistency tests against the repository `config/mcp_dedup.toml` | No test compares the two sources today | REQ-001 / AC-2 | `tests/shared/test_tool_runner.py:2414-2457` covers only frozenset membership, not toml sync | new consistency test class | Verified |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Update the "Retry classification" bullet and config-keys note to state the owner/mirror relationship and load-time rejection | Guide currently presents the toml as the standalone mapping owner | REQ-001, REQ-007 / AC-6 | `db_03_07` "Retry classification" bullet (line ~62) and "Config keys" note (line ~72) | N/A: documentation checker instead (see Validation plan) | Verified |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Fix the Tool Call State Recording paragraph's retry_class source claim | Guide attributes the Agent-side recorded value to `mcp_dedup.py::retry_class`/toml; code uses `RETRYABLE_TOOLS` | REQ-007 / AC-6 | guide line ~81 vs `scripts/agent/tool_runner.py:163-172,188` | N/A: documentation checker instead (see Validation plan) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/tool_runner.py` | Consumer of `RETRYABLE_TOOLS` (lines 24, 163-172, 188); its comment carries the same ADR-008 citation defect (scope-amendment candidate, UNK-03) | REQ-001, REQ-005 |
| `scripts/mcp_servers/dispatch.py` | Consumer of `retry_class()` toml lookups (lines 296, 320, 384); confirms the dispatcher-side classification path is lookup-only and unchanged | REQ-001, REQ-002 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Owner of the retryable/non-retryable dispatch failure policy (MCP-001, MCP-002); correct citation target | REQ-005 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Owns `mcp_dedup.sqlite` disposable-cache and fail-closed-replay semantics; what the fixed comment may legitimately cite | REQ-005 |
| `registry/manifests/mcp_endpoints.yaml` | Canonical port table (github 8006, cicd 8012, git 8014) for the port-comment fix; generated file, never hand-edited | REQ-004 |
| `scripts/shared/http_transport.py` | `derive_idempotency_key` boundary is independent of retry class; read to avoid conflating the two dimensions | REQ-001 |
| `tests/agent/test_tool_runner.py` | Existing `RETRYABLE_TOOLS` membership assertions (lines 2414-2457); must keep passing unchanged | REQ-001 |
| `deploy/deploy.sh` | Confirm the existing `cp` line for `config/mcp_dedup.toml` (line 154) means no deploy change is needed | REQ-003 |
| `docs/22_mcp/mcp_01_tool_ownership_matrix.md` | Server/port/tool ownership cross-check for the port comment | REQ-004 |

## Acceptance Criteria
- `AC-1` (REQ-002): A test fails when a `[retry_class]` key is not a known tool name
  (`ConfigParseError` raised by `load_dedup_config`).
- `AC-2` (REQ-001): A test fails when the two sources disagree (extra, missing, or
  contradictory entries), or when only one source remains (all toml retryable keys must equal
  `RETRYABLE_TOOLS`).
- `AC-3` (REQ-003): Every key in `config/mcp_dedup.toml [retry_class]` is a live tool name in
  `get_all_mcp_tool_names()`; no `web_search` key remains; no tool's effective
  classification changed (rename keeps `search_web` at `non_retryable`, which was already its
  effective value through the default).
- `AC-4` (REQ-004, REQ-005): `tool_constants.py` port comments match
  `registry/manifests/mcp_endpoints.yaml`; the retry-class comment cites ADR-004 for the
  dispatch policy and ADR-008 only for dedup-store semantics.
- `AC-5` (REQ-006): The 22-tool retryable side-effect report is delivered to the maintainer;
  the implementation diff contains zero `RETRYABLE_TOOLS` membership changes.
- `AC-6` (REQ-007): Both guides attribute the Agent-side recorded `retry_class` to
  `RETRYABLE_TOOLS` and describe the toml as the load-validated mirror.

## Tests
- `REQ-002` (`tests/shared/test_mcp_dedup.py`, class `TestConfigValidation`):
  - Update `test_bad_section_types_raise_parse_error` `bad3` fixture to a valid tool name with
    a non-integer-disallowed shape (keeps the value-type path covered under the new gate).
  - Update `test_retry_class_lookup` fixture to valid, consistent names (for example
    `write_file = "retryable"`, `shell_run = "non_retryable"`); keep the
    `retry_class("some_new_tool") == "non_retryable"` default assertion.
  - New: unknown tool name in `[retry_class]` raises `ConfigParseError`.
  - New: value outside `{retryable, non_retryable}` raises `ConfigParseError`.
  - New: key classified inconsistently with `RETRYABLE_TOOLS` membership (e.g.
    `search_web = "retryable"`) raises `ConfigParseError`.
- `REQ-001` (`tests/shared/test_tool_constants.py`, new class):
  - Load the repository `config/mcp_dedup.toml` and assert `{k for k, v in retry_class.items()
    if v == "retryable"} == RETRYABLE_TOOLS`.
  - Assert every key is in `get_all_mcp_tool_names()` and every `non_retryable` key is not in
    `RETRYABLE_TOOLS`.
- `REQ-001` regression (`tests/agent/test_tool_runner.py`, unchanged): existing membership
  assertions keep passing.
- Mutation spot-check (manual, one-off): locally add/remove one `RETRYABLE_TOOLS` member,
  confirm the new consistency test fails, then revert.
- Full sequence per `rules/toolchain.md` (see Validation plan).

## Documentation Impact
Required (REQ-001, REQ-007): the issue's conditional trigger fired — the MCP dedup guide and
the Agent tool-execution guide already describe the retry-class source (confirmed by `rg`
2026-11-18), and one of them names the wrong source. Target docs are named via
`docs/00_index.md`'s task mapping for the `41_db` dedup-snapshot guide and the `23_agent`
tool-execution guide; the exact frozen paths are the two `docs/` rows in Implementation Target
Files. After the docs edits, run the docs checkers listed in `routing.md` Tools → "When to
run which tool".

## Assumptions
- `RETRYABLE_TOOLS` is chosen as the owner (not the toml): the Agent path already depends only
  on it (config isolation, `tool_runner.py:166-172`), the toml header already says keys were
  "verified ... against scripts/shared/tool_constants.py", and a same-layer import from
  `shared.mcp_dedup` to `shared.tool_constants` does not violate any `.importlinter` contract
  (6 contracts kept, re-checked 2026-11-18).
- The load-time gate validates per key (name known, value allowed, membership consistent);
  full two-way set equality is enforced by the `tests/shared/test_tool_constants.py` test
  against the repository config instead of inside the loader, because strict set equality
  would force every synthetic test fixture to replicate the entire 22-tool constant. A toml
  that omits a retryable key is caught by the test, not the loader.
- `search_web` stays `non_retryable` and `shell_run` stays `non_retryable`: no classification
  change (issue constraint). The rename is behavior-preserving because today the dead key
  already fell through to the `non_retryable` default.
- The production overlay config directory mirrors the repository `config/mcp_dedup.toml`
  (no extra keys at `/opt/llm/config`); not observable from this dev host (no service
  listeners, no `/opt/llm/db` files — confirmed 2026-11-18), so the consistency test uses the
  repository file and deployment sync relies on the existing `deploy.sh` `cp` line.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Issue's `Needs confirmation`: `mcp_dedup.py` loader behavior | none — resolved this cycle by reading `mcp_dedup.py:92-179` (unknown keys accepted silently; `retry_class` defaults to `non_retryable`) | Resolved; evidence recorded in `Problem` | False (resolved) |
| UNK-02 | Whether any of the 22 retryable side-effect tools (`git_push`, `github_merge_pull_request`, `delete_directory`, `rag_delete_document`, ...) should be reclassified `non_retryable` | maintainer decision (issue constraint + governance_01/governance_05 approval record) | Deliver the REQ-006 report; maintainer decision opens a follow-up issue; this Plan changes none | False |
| UNK-03 | `scripts/agent/tool_runner.py:166-170` carries the same ADR-008 citation and a "keep the two consistent" note; file is not in Target Files | maintainer approval for a scope amendment (issue constraint: "Change only the Target Files; if another file must change, stop and report it as a scope amendment") | Report as scope amendment; if approved, add the comment fix to this Plan's frozen table before procedure generation; otherwise defer to the next Plan touching the file (`rules/coding.md` deprecation-policy style) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/tool_constants.py` | comments only | Wide import fan-out (30+ scripts/tests import the module) but zero behavior change | 3 | 1 (single maintainer, name variants) | None: `scripts/` synced by `rsync -av --delete`; no `deploy.sh` edit |
| `config/mcp_dedup.toml` | key rename + comment | Dispatcher and Agent config load path | 3 | 1 | None: existing `cp` line (`deploy.sh:154`); no new line |
| `scripts/shared/mcp_dedup.py` | load-time validation added | `dispatch.py` store paths, Agent dedup-store wiring; a malformed config now fails service startup | 6 | 1 | None: `rsync` sync of `scripts/` |
| `tests/shared/test_mcp_dedup.py` | fixtures + new tests | tests only | 5 | 1 | N/A: not deployed |
| `tests/shared/test_tool_constants.py` | new consistency tests | tests only | 0 | 1 | N/A: not deployed |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | retry-classification bullet update | docs readers | 7 | 1 | None: `docs/` synced by `rsync` (`deploy.sh:206`) |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | recording-source paragraph fix | docs readers | 8 | 1 | None: `docs/` synced by `rsync` (`deploy.sh:206`) |

## Design
Path classification: **Path B (Medium)** — shared-constant/config change with cross-layer
consumers (`agent`, `mcp_servers`, `shared`); consumer scan, import-contract check, churn and
coverage evidence gathered (grimp/pyan3 not needed: `tool_constants.py` has no intra-repo
imports; `import-linter` reports 6 contracts kept, 0 broken).

Claim verification (issue claim -> verdict -> evidence):
- `web_search` key exists -> confirmed -> `config/mcp_dedup.toml:48-49`.
- tool name is `search_web` -> confirmed -> `tool_constants.py:125`, `web_search_tools.py:14`.
- "two sources hand-synced" -> confirmed -> `tool_constants.py:174-181` comment,
  `tool_runner.py:170` "keep the two consistent"; no enforcing test exists.
- "one key matches no tool" -> confirmed -> toml keys minus `get_all_mcp_tool_names()` =
  `{web_search}` (computed 2026-11-18).
- "risky tools are retryable" -> confirmed -> `git_push` (toml:31),
  `github_merge_pull_request` (toml:38), `delete_directory` (toml:25); all 22 retryable
  members are in `ALL_SIDE_EFFECTING_TOOLS` (computed intersection 22/22).
- "port comment names the wrong server" -> confirmed -> `tool_constants.py:133` (8012 =
  cicd-mcp) vs github-mcp 8006 (`mcp_endpoints.yaml`, `agent.toml`, ownership matrix).
- "comment cites ADR-008 which is not about retry" -> partially inaccurate -> ADR-008 owns
  the dedup-store/replay fail-closed semantics; retry dispatch policy is ADR-004
  (MCP-001/MCP-002). Fix targets ADR-004 with an ADR-008 store reference.
- loader behavior (`Needs confirmation`) -> confirmed resolved -> unknown keys accepted;
  values only type-checked; `retry_class` default `non_retryable` (`mcp_dedup.py:127-179`).

Consumer-scan disposition (`tools/scan_change_consumers.py` seeds `RETRYABLE_TOOLS`,
`retry_class`, `web_search`, `mcp_dedup.toml`; 2026-11-18):
- Target rows: the seven Implementation Target Files rows.
- Reference rows: `tool_runner.py`, `dispatch.py`, `adr_02_01_004`, `adr_02_05_008`,
  `mcp_endpoints.yaml`, `http_transport.py`, `test_tool_runner.py`, `deploy.sh`,
  `mcp_01_tool_ownership_matrix.md`.
- Not affected: `tests/agent/test_http_lifecycle_env_allowlist_integration.py` (references the
  config *filename* only); `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` (comment only);
  `tests/mcp_servers/test_mcp_dispatch.py` (builds `DedupConfig` objects directly, bypassing
  the loader); `registry/manifests/config_ownership.yaml` (its `retry` entries are LLM retry
  fields, unrelated to `[retry_class]`; no manifest regeneration needed); other
  `tests/mcp_servers/*` consumer-scan hits (import unrelated `*_TOOLS` sets).

Validation gate design (`mcp_dedup.py`):
- `load_dedup_config` imports `RETRYABLE_TOOLS` and `get_all_mcp_tool_names` from
  `shared.tool_constants` (same-layer import; contract-safe).
- Per key: name must be in `get_all_mcp_tool_names()`; value must be `retryable` or
  `non_retryable`; `(name in RETRYABLE_TOOLS) == (value == "retryable")`. Any violation ->
  `ConfigParseError(filename, ValueError(...))` naming the key.
- Lookup-time default (`retry_class()` for unlisted tools -> `non_retryable`) is unchanged:
  unlisted *known* tools stay fail-safe.
- Full two-way set equality against the repository config is enforced by the new
  `tests/shared/test_tool_constants.py` test (see Assumptions for why it is not in the
  loader).

REQ-006 report — retryable tools with external side effects (all 22, for maintainer decision;
no change proposed): `write_file`, `edit_file`, `create_directory`, `move_file`,
`delete_file`, `delete_directory`, `git_add`, `git_commit`, `git_checkout`, `git_pull`,
`git_push`, `github_add_issue_comment`, `github_create_branch`, `github_create_issue`,
`github_create_or_update_file`, `github_delete_file`, `github_merge_pull_request`,
`github_push_files`, `github_update_pull_request`, `index_paths`, `refresh_index`,
`rag_delete_document`. Their replay-safety guarantee is exactly the dedup ledger
(`mcp_dedup.sqlite`, disposable per ADR-008; loss => non-retryable replay blocked, retryable
replay allowed per ADR-004 MCP-001/MCP-002).

## Implementation steps
1. **Phase 1: Config key rename and comment fixes**
   - [ ] Re-run the issue's named searches (`rg` for `web_search`, `retry_class`,
     `port 8012`, `ADR-008`) and skip any already-fixed item (issue constraint; evidence:
     this Plan's Problem section, 2026-11-18). (REQ-003, REQ-004, REQ-005;
     `config/mcp_dedup.toml`, `scripts/shared/tool_constants.py`)
   - [ ] Rename `web_search = "non_retryable"` to `search_web = "non_retryable"` in
     `[retry_class]`, update its grouping comment, and adjust the header note that claims
     keys are live tool names so it states keys are validated against `RETRYABLE_TOOLS` and
     known tool names at load. (REQ-001, REQ-003; `config/mcp_dedup.toml`)
   - [ ] Fix `# GitHub tools (github-mcp, port 8012)` to `port 8006` and the retry-class
     comment's citation to ADR-004 (dispatch retry policy) with ADR-008 referenced only for
     dedup-store semantics; remove no other comment. (REQ-004, REQ-005;
     `scripts/shared/tool_constants.py`)
2. **Phase 2: Load-time validation gate**
   - [ ] In `load_dedup_config`, add the per-key `[retry_class]` validation described in
     Design (known name, allowed value, membership consistency), raising `ConfigParseError`
     naming the offending key. (REQ-001, REQ-002; `scripts/shared/mcp_dedup.py`)
   - [ ] Update `TestConfigValidation` fixtures to valid, consistent tool names and add the
     three new rejection tests listed in Tests. (REQ-002; `tests/shared/test_mcp_dedup.py`)
3. **Phase 3: Cross-source test, docs, verification**
   - [ ] Add the repository-config consistency test class to `tests/shared/test_tool_constants.py`
     (retryable keys == `RETRYABLE_TOOLS`; all keys known). (REQ-001; `tests/shared/test_tool_constants.py`)
   - [ ] Update the two guides per `Documentation Impact` (owner/mirror wording; Agent-side
     source is `RETRYABLE_TOOLS`), then run the docs checkers from `routing.md` Tools.
     (REQ-007; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`,
     `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`)
   - [ ] Run the validation sequence (Validation plan), confirm `deploy/deploy.sh` needs no
     change (existing `cp` line 154), and deliver the REQ-006 report in the procedure's final
     report. (REQ-001, REQ-002, REQ-006; all target rows)

### Release units
**Unit**: retry-class-load-gate | **Phases**: 1, 2 | **Reason**: Phase 2's gate rejects the un-renamed repository config (`web_search` key is not a known tool name), so services would fail config load unless the Phase 1 rename lands in the same commit; neither phase validates green alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/mcp_dedup.py` | Unit (loader gate) | `uv run pytest tests/shared/test_mcp_dedup.py -q` | All existing + 3 new rejection tests pass |
| `tests/shared/test_tool_constants.py` | Unit (cross-source consistency) | `uv run pytest tests/shared/test_tool_constants.py -q` | New consistency tests pass against repository config |
| `config/mcp_dedup.toml` | Unit (same consistency test) + local mutation spot-check | mutate `RETRYABLE_TOOLS` locally -> `uv run pytest tests/shared/test_tool_constants.py -q` -> revert | Tests fail on induced disagreement, pass after revert |
| `scripts/shared/tool_constants.py` | Static + regression | `uv run ruff check scripts/shared/ tests/shared/`, `uv run mypy scripts/shared/mcp_dedup.py`, `uv run bandit -q -r scripts/shared/tool_constants.py scripts/shared/mcp_dedup.py -c pyproject.toml`, `uv run pytest tests/agent/test_tool_runner.py -q` | Clean; existing membership assertions pass |
| `scripts/shared/mcp_dedup.py` (import added) | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | 6 contracts kept, 0 broken |
| all target rows | Full suite baseline | `uv run pytest tests/ -m "not integration and not production_paths_allowed and not repo_scan" -q` | 12794 passed / 7 skipped baseline (2026-11-18) preserved or better |
| docs target rows | Docs checkers | commands per `routing.md` Tools -> "When to run which tool" (docs scope) | Clean |
| `config/mcp_dedup.toml` (deployment) | Deploy-config check | `rg -n "mcp_dedup" deploy/deploy.sh` | Existing `cp` line present; no `deploy.sh` edit needed |

## Risks
- **Risk**: strict loader fails service startup if an overlay/legacy config carries an unknown
  key. -> **Mitigation**: fail-closed is the intended policy (ADR-004 registered exceptions,
  Current-Specification-Only); repository-config consistency test proves the shipped config
  loads; `deploy.sh` copies the repository config verbatim.
- **Risk**: fixture updates hide a regression (fixtures rewritten until nothing fails). ->
  **Mitigation**: keep the value-type failure test (`bad3`) with a valid tool name; run the
  mutation spot-check in the Validation plan to prove the tests actually detect drift.
- **Risk**: concurrent Plans edit the same files (issue constraint: "Other plans edit the same
  files"). -> **Mitigation**: re-run the issue's named searches at implementation start; skip
  already-fixed items with recorded evidence.
- **Risk**: docs claim-fixes contradict a future reclassification decision (UNK-02). ->
  **Mitigation**: docs edits describe the mechanism (owner/mirror), never per-tool class
  values; classification changes are out of scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: config key rename + comment fixes (`config/mcp_dedup.toml`, `scripts/shared/tool_constants.py`) | In Progress | — | — |  |
| 2 | Phase 2: loader validation + `tests/shared/test_mcp_dedup.py` fixtures/new tests | In Progress | — | — | Lands with Phase 1 (release unit) |
| 3 | Phase 3: cross-source test + docs fixes + full validation + REQ-006 report | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker at plan time | N/A: no blocker | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-162033_01_scripts_shared_tool_constants.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-162033_02_config_mcp_dedup.toml.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-162033_03_scripts_shared_mcp_dedup.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261118-162033_05_tests_shared_test_tool_constants.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-162033_06_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-162033_07_docs_23_agent_agent_06_01_tool-execution-and-approval-execution.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123018_adrchk018_mcp-retry-classes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-153543
- **Related target files**: `scripts/shared/tool_constants.py`; `config/mcp_dedup.toml`;
  `scripts/shared/mcp_dedup.py`; `tests/shared/test_mcp_dedup.py`;
  `tests/shared/test_tool_constants.py`;
  `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`;
  `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` — the full list of
  `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Reason for Change; `tool_constants.py:174-181`; `mcp_dedup.py:175-179` | `config/mcp_dedup.toml` | Phase 1 | AC-2, AC-3 | `tests/shared/test_tool_constants.py` consistency test | Derived from confirmed evidence |
| REQ-001 | same | `scripts/shared/mcp_dedup.py` | Phase 2 | AC-2 | `tests/shared/test_mcp_dedup.py` rejection tests | Derived from confirmed evidence |
| REQ-001 | same | `tests/shared/test_tool_constants.py` | Phase 3 | AC-2 | new consistency test class | Derived from confirmed evidence |
| REQ-001 | same | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 3 | AC-6 | docs checker | Derived from confirmed evidence |
| REQ-002 | Issue Implementation Intent "Unknown keys are rejected"; `mcp_dedup.py:127-155` | `scripts/shared/mcp_dedup.py` | Phase 2 | AC-1 | `TestConfigValidation` new tests | Explicit in issue |
| REQ-002 | same | `tests/shared/test_mcp_dedup.py` | Phase 2 | AC-1 | fixture updates + 3 new tests | Explicit in issue |
| REQ-003 | Issue Problem ("`web_search` key", Explicit in code); `config/mcp_dedup.toml:48-49` | `config/mcp_dedup.toml` | Phase 1 | AC-3 | consistency test + `rg web_search` re-check | Explicit in issue |
| REQ-004 | Issue Reason for Change "port comment names the wrong server"; `tool_constants.py:133` vs `mcp_endpoints.yaml` | `scripts/shared/tool_constants.py` | Phase 1 | AC-4 | `rg` re-check against `mcp_endpoints.yaml` | Confirmed by repository evidence |
| REQ-005 | Issue Reason for Change "comment cites ADR-008"; `tool_constants.py:174` vs `adr_02_01_004` MCP-001/002 | `scripts/shared/tool_constants.py` | Phase 1 | AC-4 | `rg` re-check against ADR index | Confirmed by repository evidence |
| REQ-006 | Issue Reason for Change "risky tools ... risk is not recorded"; computed 22/22 intersection | N/A: report-only requirement (Design section carries the table) | Phase 3 | AC-5 | N/A: delivered in procedure final report | Confirmed by repository evidence |
| REQ-007 | Issue Documentation Impact trigger; guide line ~81 vs `tool_runner.py:163-172` | `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Phase 3 | AC-6 | docs checker | Confirmed by repository evidence |
| REQ-007 | same | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 3 | AC-6 | docs checker | Confirmed by repository evidence |