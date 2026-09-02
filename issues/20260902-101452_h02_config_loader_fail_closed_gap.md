# H-02: `ConfigLoader`'s fail-closed guarantee is not actually wired into any production call site

## Priority
High

## Summary
`ConfigLoader.load_all()` supports a `strict` parameter that raises `ConfigMissingError` when a
required config file (`agent.toml`) is missing, and this parameter is correctly implemented and
unit-tested. However, every one of its 5 call sites in the codebase calls `load_all()` with no
argument, so `strict` defaults to `False` everywhere, including in production. A missing or
misnamed `agent.toml` is therefore silently skipped (a `DEBUG`-level log only), which — through a
second, independent gap in how `security_profile` defaults — also silently disables the one
production-only fail-closed gate (`ProductionConfigValidator`) that does exist. Two further gaps
were found in the same area: `ConfigLoader.restrict_to()` (the Config Isolation mechanism ADR-002
requires) is skipped entirely when a caller's `own_config_file` is falsy, and no config loader
validates unknown/mistyped top-level keys at all. This issue asks for these fail-closed gaps to be
closed and for the corresponding ADR-004/ADR-002 test coverage (already flagged as
"Needs confirmation"/"未検証" in ADR-004's own Verification section) to be added.

## Background
- `ConfigLoader.load_all(strict: bool = False)` (`scripts/shared/config_loader.py`) only raises
  `ConfigMissingError` for a missing file in `_REQUIRED_CONFIG_FILES` (currently just
  `agent.toml`) when `strict=True` is passed; otherwise it logs at `DEBUG` and continues with
  whatever files it could load. `ConfigParseError` (malformed TOML/JSON) and `ConfigReadError`
  (permission denied) are NOT caught by `load_all()`'s `try/except ConfigMissingError` block, so
  those two failure modes already propagate and abort the process unconditionally — the gap is
  specifically "file missing or misnamed," not "file present but broken." (`Explicit in code`)
- Every call site of `load_all()` omits `strict` (confirmed by `grep -rn "load_all("
  scripts/`, `Explicit in code`): `scripts/agent/config_builders.py:60`
  (`load_config()`, used by `build_agent_config()`), `scripts/agent/commands/cmd_config.py:59`,
  `scripts/rag/pipeline.py:75,119`, `scripts/rag/llm_client.py:68,81`. None pass `strict=True`,
  and `strict` is never conditioned on `security_profile` anywhere.
- By contrast, `ConfigLoader.load()` (used by every individual MCP server to load its own
  `<name>_mcp_server.toml`, e.g. `scripts/mcp_servers/git/git_models.py:65`) has no `strict`
  parameter and unconditionally raises `ConfigMissingError` on a missing file — that path is
  already fail-closed today. The defect is isolated to `load_all()`'s default and its callers
  (the Agent process and the RAG pipeline), not to individual MCP servers. (`Explicit in code`,
  `Verified by test` — `tests/shared/test_config_loader.py::TestErrors::test_missing_file_raises_value_error`)
- A second, independent gap compounds the first: `scripts/agent/config_builders.py::build_agent_config()`
  reads `security_profile_val = SecurityProfile(cfg.get("security_profile", "local"))` from the
  dict `load_config()` returned. If `agent.toml` was silently skipped (gap above), `cfg` has no
  `security_profile` key, so this defaults to `"local"` — which makes
  `ProductionConfigValidator.validate()`'s `is_production` check `False`, converting every one of
  its own checks (`tool_definitions_strict`, `routing_drift_strict`, `tool_safety_tiers`
  consistency, `approval_risk_rules` floor, empty `allowed_tools`) from a fatal `sys.exit(1)`
  error into a non-fatal warning. In other words, the one fail-closed gate that does exist for
  production is itself silently defeated by the same missing-file condition it was meant to catch
  in that exact scenario. (`Explicit in code`, `scripts/agent/config_builders.py::build_agent_config()`)
- `scripts/mcp_servers/server.py::MCPServer.run_http()` only calls
  `ConfigLoader.restrict_to(self.own_config_file)` `if self.own_config_file:` — an empty/unset
  `own_config_file` silently skips Config Isolation restriction entirely (the process then runs
  with `ConfigLoader._allowed_files = None`, i.e. unrestricted), rather than failing. This
  directly conflicts with `docs/adr/ADR-002-config-isolation.md` Decision #9 ("共通Config
  Loaderの利用は許可するが、プロセスごとに許可ファイルを限定し、許可外ファイルの読込をRuntime
  Errorとする") and its Fail-Fast Conditions ("各プロセスの設定ファイルが欠落している場合"[相当の設定不備]).
  (`Explicit in code`)
- Neither `ConfigLoader.load()`/`load_all()` nor `ProductionConfigValidator.validate()` validates
  unknown/mistyped top-level config keys against any allowlist or schema — a typo'd key is
  silently absorbed into the merged dict with no warning at any layer. `ProductionConfigValidator`
  does perform a comparable bidirectional check, but only for the narrow `tool_safety_tiers`
  mapping (`_check_missing_tool_safety_tiers`/`_check_unknown_tool_safety_tiers`, resolved against
  `shared.tool_registry.get_registry()`) — no equivalent exists for `agent.toml`'s top-level keys
  or any `<name>_mcp_server.toml`'s keys. (`Explicit in code`)
- `docs/adr/ADR-004-environment-failure-handling-policy.md` Decision #14 lists "認証設定の不正",
  "Allowlist設定の不正", "Config Isolation違反", "環境設定検証の失敗" among the conditions that
  MUST Fail-Fast at startup, and Decision #1-3/INV-01/INV-02 require this policy to be identical
  across all environments (no environment-based relaxation) — yet the gaps above only manifest as
  a silent, non-fatal skip. ADR-004's own Verification section already marks INV-07/INV-08/INV-09
  as `Needs confirmation`/`未検証` for exactly this class of startup scenario (missing/invalid
  config, undefined component requiredness), and its Known Deviations section explicitly
  recommends filing new Known Issues for the untested INV-09/INV-14 scenarios. This issue is that
  follow-up for the `ConfigLoader`-specific portion of that gap.
- `docs/adr/ADR-002-config-isolation.md` Fail-Fast Conditions explicitly lists "各プロセスの設定
  ファイルが欠落している場合" and "設定ファイルが不正である場合"; its Fail-Open/Degraded
  Conditions explicitly scope warning-only handling to "ローカル開発環境" only — implying
  non-local environments must not degrade a missing/invalid required file to a warning, which is
  exactly what the `load_all(strict=False)` default currently does in every environment,
  including production.

## Problem
`ConfigLoader`'s fail-closed primitive (`load_all(strict=True)`) exists and works correctly in
isolation, but no production code path actually invokes it, and the one downstream check that is
supposed to catch a production misconfiguration (`ProductionConfigValidator`) can itself be
silently bypassed by the same missing-file condition, because it relies on a `security_profile`
value that comes from the very file that might be missing. Additionally, the Config Isolation
restriction (`restrict_to()`) can be silently skipped by a falsy `own_config_file`, and no config
loader rejects unknown/mistyped keys. Together these mean a missing config file, a misnamed
config file, or a mistyped key can currently reach production silently, contrary to
ADR-002/ADR-004's explicit Fail-Fast requirements.

## Reason for Change
This is a security-relevant gap in the system's fail-closed guarantee: a deployment mistake as
simple as a missing or misspelled `agent.toml` would not stop the Agent process from starting, and
would additionally suppress the one config-content validator that could have caught related
problems, because that validator's own production/local branch depends on a key that lives inside
the same file. `ADR-002` and `ADR-004` both already mandate Fail-Fast for exactly this scenario;
this issue closes the gap between that documented policy and the current, unwired implementation.

## Implementation Intent
Wire the existing `strict` mechanism into the call sites that need it, close the two related
silent-skip paths, and add the ADR-004/ADR-002 test coverage those ADRs' own Verification sections
already flag as missing — without inventing new config semantics beyond what is explicitly
requested:
- Per `ADR-004` Decision #1-3/INV-01/INV-02 (single failure-handling policy across all
  environments, no environment-based relaxation), make a missing/misnamed required base config
  file (`agent.toml`) fail closed **unconditionally**, not only when `security_profile ==
  "production"` — this also avoids the bootstrapping problem of needing to read
  `security_profile` from the same file to decide whether to be strict about that file.
- Fix `MCPServer.run_http()` to fail (not silently skip) when `own_config_file` is falsy, so
  Config Isolation can never be silently unrestricted.
- Add a validation step that rejects unknown top-level (and, where the dataclasses expose nested
  structure, nested) config keys in production. Decided: derive the set of valid keys from
  `scripts/agent/config_dataclasses.py`'s existing dataclasses (`AgentConfig` and its 9 composed
  sub-configs — `LLMConfig`, `RAGConfig`, `ToolConfig`, `MemoryConfig`, `MCPConfig`,
  `ApprovalConfig`, `ObservabilityConfig`, `DiagnosticsConfig`, `MessageRoleConfig`) via
  introspection (e.g. `dataclasses.fields()`), rather than a separately hand-maintained key
  allowlist that could drift out of sync with those dataclasses. These are plain `@dataclass`
  definitions, not pydantic models, so this is not a pydantic `extra="forbid"` mechanism — it is
  closer in shape to `ProductionConfigValidator`'s existing bidirectional `tool_safety_tiers`
  check (`_check_missing_tool_safety_tiers`/`_check_unknown_tool_safety_tiers`), generalized from
  one nested mapping to the config's top-level (and relevant nested) key sets. The exact mapping
  between a raw TOML key and the dataclass field(s) that consume it (some are read via
  `cfg.get("some_key")` inside `_build_*` helper functions rather than a 1:1 field-name match)
  needs to be worked out during implementation — this issue records the source-of-truth decision,
  not the full mapping.
- Document, per process, which config file(s) it reads, which keys are required, and which keys
  may legitimately be empty — grounded in `ADR-002` Decision Details #1-6 (which file each process
  reads) plus a new per-key breakdown. Decided: embed this table directly in
  `docs/adr/ADR-002-config-isolation.md`, rather than a new standalone doc or a section in an
  existing config-reference doc.
- Add startup-level tests (missing file, empty file, malformed TOML, permission denied,
  misnamed file) mapped 1:1 to `ADR-004`'s INV-07/INV-08/INV-09 and `ADR-002`'s INV-01/INV-02,
  closing the "Needs confirmation"/"未検証" status those ADRs' own Verification sections already
  record for this scenario class.

## Target Files or Areas
- `scripts/shared/config_loader.py` (`load_all()`'s `strict` default and/or its interaction with
  `_REQUIRED_CONFIG_FILES`)
- `scripts/agent/config_builders.py` (`load_config()`, `build_agent_config()`'s `security_profile`
  resolution order relative to the missing-file check)
- `scripts/agent/commands/cmd_config.py`, `scripts/rag/pipeline.py`, `scripts/rag/llm_client.py`
  (all call `load_all()` with no `strict` argument)
- `scripts/mcp_servers/server.py` (`MCPServer.run_http()`'s falsy `own_config_file` skip)
- `scripts/shared/production_config_validator.py` (candidate location for the unknown-key check
  derived from `agent/config_dataclasses.py`)
- `scripts/agent/config_dataclasses.py` (read-only: source of truth for the valid-key
  introspection; not itself modified by this issue unless implementation finds a field naming gap)
- `tests/shared/test_config_loader.py`, `tests/agent/test_startup.py`,
  `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/agent/test_config_permission_cross_server.py`
  (new startup-scenario tests)
- `docs/adr/ADR-004-environment-failure-handling-policy.md` (Verification section — update
  INV-07/INV-08/INV-09 status once tests are added)
- `docs/adr/ADR-002-config-isolation.md` (Verification section update for INV-01/INV-02, plus the
  new embedded per-process required-file/required-key/empty-allowed-key table)

## Required Changes
- Make a missing or misnamed `agent.toml` abort Agent/RAG-pipeline startup unconditionally
  (all 5 `load_all()` call sites), not only under a production check.
- Fix the `security_profile` resolution order (or the underlying cause) so that
  `ProductionConfigValidator` can never be silently routed onto its local/warning branch merely
  because the file that would have told it the profile was missing.
- Fix `MCPServer.run_http()` to raise (or otherwise fail closed) instead of silently skipping
  `restrict_to()` when `own_config_file` is falsy.
- Add unknown-top-level-key rejection for production config loading, with valid keys derived from
  `agent/config_dataclasses.py` via introspection (decided; see Implementation Intent).
- Author a per-process table of required config file(s), required keys, and keys that may
  legitimately be empty (Agent, each MCP server, crawler, chunk_splitter, ingester, EventBus —
  matching `ADR-002` Decision Details #1-6's per-process file list), embedded directly in
  `docs/adr/ADR-002-config-isolation.md` (decided).
- Add startup tests for: missing required file, empty (zero-byte) file, malformed TOML, permission
  denied, and a misnamed file (e.g. a typo'd filename that resolves to "not found"), for both the
  Agent process (`load_all()`) and at least one MCP server (`load()`).
- Map each new/existing test to the specific `ADR-004` Invariant(s) and `ADR-002` Invariant(s) it
  verifies, and update both ADRs' Verification sections' `Status` fields accordingly (e.g. from
  `Needs confirmation`/`未検証` to `Confirmed`).

## Constraints
- Do not change `ConfigLoader.load()`'s behavior — it is already fail-closed on a missing file and
  is out of scope for this issue.
- Do not weaken `ProductionConfigValidator`'s existing checks; only fix the input (`security_profile`
  resolution) that can currently cause them to run on the wrong branch.
- Per `ADR-004` INV-01/INV-02, any fix must not introduce environment-based branching for the
  base-file-missing case — the fix must apply identically in local, development, and production.
- Do not redesign `ConfigLoader`'s merge semantics, JSON/TOML dual-format support, or the
  `_filter_meta_keys()`/`_merge_one_level()` behavior — out of scope.

## Acceptance Criteria
- A missing or misnamed `agent.toml` causes `load_config()`/`build_agent_config()` to raise/exit
  rather than silently continue, in every environment (verified by a new test per Required
  Changes).
- With `agent.toml` missing, `ProductionConfigValidator`'s checks are not reachable at all (the
  process has already aborted before `security_profile_val` is computed) — i.e., the
  local/production branch ambiguity described in Background cannot occur.
- `MCPServer.run_http()` with a falsy `own_config_file` fails at startup instead of running
  unrestricted.
- At least one new test asserts that an unknown/mistyped top-level config key (not present among
  `agent/config_dataclasses.py`'s introspected fields) is rejected in production.
- A per-process required-file/required-key/empty-allowed-key table exists as a new section in
  `docs/adr/ADR-002-config-isolation.md`.
- `docs/adr/ADR-004-environment-failure-handling-policy.md`'s Verification section's INV-07/
  INV-08/INV-09 rows, and `docs/adr/ADR-002-config-isolation.md`'s INV-01/INV-02 rows, are updated
  to cite the new tests and no longer read `Needs confirmation`/`未検証` for the scenarios this
  issue's tests cover.
- `uv run pytest tests/shared/test_config_loader.py tests/agent/test_startup.py
  tests/agent/shared/test_startup_validation_pipeline.py
  tests/agent/test_config_permission_cross_server.py -q` passes.

## Testing Expectations
New unit/integration tests per Required Changes (missing/empty/malformed/permission-denied/
misnamed config file scenarios, for both `load_all()` call sites and `restrict_to()`'s falsy-skip
path), plus regression runs of the existing `tests/shared/test_config_loader.py` suite (already
has `TestLoadAllStrictMode` covering the `strict` parameter's own correctness — this issue does
not need to re-test that primitive, only its wiring and the two related silent-skip paths).

## Documentation Impact
Yes: `docs/adr/ADR-004-environment-failure-handling-policy.md` and
`docs/adr/ADR-002-config-isolation.md` Verification sections need updating once tests land (per
Acceptance Criteria), and a new per-process required-file/required-key/empty-allowed-key table
needs to be added as a new section in `docs/adr/ADR-002-config-isolation.md` (decided).

## Out of Scope
- `scripts/eventbus/config.py` — does not use `ConfigLoader` at all (already tracked separately as
  `ADR-002`'s Known Deviation `CI-001`); this issue does not extend `ConfigLoader` fail-closed
  behavior to EventBus.
- The `attach_auth_middleware()` empty-token-skips-auth design in `scripts/mcp_servers/server.py`
  — this is documented, intentional behavior for token-less local/loopback binds. This issue does
  not change that design; it is mentioned in Background only to explain why the `load_all()` gap
  matters (an accidentally-missing `agent.toml` can compound with this pre-existing design), not
  as a target for a code change here.
- Whether `allow_public_bind`-style host-based public-bind detection (as implemented in
  `scripts/eventbus/config.py::_is_public_host()`) should be added to the generic MCP server base
  (`scripts/mcp_servers/server.py`) to pair with a required-token check — this would be a new
  feature beyond fail-closed config *loading*, and is not part of this issue's scope.
- Any change to `ProductionConfigValidator`'s existing `_REQUIRED_STRICT_KEYS`/`tool_safety_tiers`/
  `approval_risk_rules` checks — only the input it receives is in scope, not its own check logic.

## Dependencies
- `docs/adr/ADR-004-environment-failure-handling-policy.md` Known Deviations already recommends
  filing new Known Issues for the untested INV-09/INV-14 scenarios — this issue is that
  recommended follow-up for the `ConfigLoader`-specific portion.
- `docs/adr/ADR-002-config-isolation.md` Known Deviation `CI-001` (EventBus not using
  `ConfigLoader`) is related but explicitly out of scope here (see Out of Scope).
- N/A: no other open issue or plan currently targets `ConfigLoader.load_all()`'s `strict` default,
  confirmed by `grep -rl "load_all" issues/ plans/` returning no matches at investigation time.

## Unresolved Questions
- Whether `_REQUIRED_CONFIG_FILES`/`_BASE_CONFIG_FILES` should be extended if new base config
  files are ever added (currently both are the single-element `("agent.toml",)`) — not blocking
  today since they're identical, but the strict-by-default fix should account for the possibility
  they diverge later. Flagged for the implementer's awareness, not a blocking decision.
- The exact mapping between each raw TOML key and the `agent/config_dataclasses.py` field(s) that
  consume it is not 1:1 in every case (some values are read via `cfg.get("some_key")` inside
  `_build_*` helper functions in `scripts/agent/config_builders.py` under a different name or
  nested path than the dataclass field). Working out this mapping is implementation work, not a
  blocking design question — the source-of-truth decision (derive from
  `agent/config_dataclasses.py`) is already made.

## AI Implementation Instruction
The unknown-key validation mechanism (derive from `agent/config_dataclasses.py` via introspection)
and the documentation target (`docs/adr/ADR-002-config-isolation.md`) are both decided — do not
re-litigate either. Before editing `scripts/shared/config_loader.py` or
`scripts/agent/config_builders.py`, re-read both files in full and re-confirm the current
call-site list via `grep -rn "load_all(" scripts/`, since this issue's evidence may go stale if
either file changes before implementation. Do not weaken any existing passing test in
`tests/shared/test_config_loader.py::TestLoadAllStrictMode` — that suite already correctly
exercises the `strict` parameter's own behavior; only the call sites and the two related
silent-skip paths need changing. The missing-file strictness fix, the `own_config_file` falsy-skip
fix, and the ADR test-coverage additions are all separable from the unknown-key-validation work
and may be implemented independently of it. If the TOML-key-to-dataclass-field mapping proves
ambiguous for a given key during implementation, stop and report it rather than guessing which
field it corresponds to.
