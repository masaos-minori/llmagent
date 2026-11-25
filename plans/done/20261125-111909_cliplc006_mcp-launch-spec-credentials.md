## Goal
- Launch every MCP subprocess from one immutable, typed launch specification: the exact validated executable runs with a fixed process-group configuration and a minimal environment that holds only that server's own credentials, and a server identifier can never influence a path or terminal output.

## Priority
High

## Scope
- **In-Scope**:
  - An immutable `LaunchSpec` (validated absolute `argv[0]`, string-only arguments, fixed process options, minimal environment) built in one place and consumed by the launcher.
  - Removal of the public `McpServerConfig.fields` Popen-kwargs dictionary; no typed replacement (no `cwd` support).
  - The launcher executes the path `CommandValidator.validate` returns, not the original `cfg.cmd[0]`.
  - Strict trusted-directory confinement as the default, permissive mode only by explicit opt-in; executable and parent-directory ownership and mode checks.
  - A constrained server-identifier pattern enforced by `McpServerConfig` and defensively at the log-directory path.
  - Per-server credential environment: derived `MCP_<KEY>_AUTH_TOKEN` / `MCP_<KEY>_CONTROL_TOKEN` plus an explicit `credential_env` list; removal of the `MCP_*_AUTH_TOKEN`, `MCP_*_CONTROL_TOKEN`, and `GITHUB_TOKEN` wildcard inheritance; a minimal environment even when no `env` is configured; audit of key names only.
  - Release of the stderr handle when the real `CommandValidator` rejects a command (found during verification; see `Issue Verification`).
  - Documentation updates and regeneration of the generated API artifacts.
- **Out-of-Scope**:
  - MCP process ownership and restart (cliplc007) and health authentication (cliplc008).
  - API field cleanup (cliplc013), which this Plan unblocks together with cliplc007 and cliplc008.
  - Sandboxing of the child beyond environment and executable confinement (rlimits, seccomp, user switching).
  - Any change to `ProductionConfigValidator`, `scripts/agent/config_builders.py`, or the Agent-to-server authentication protocol.
- **Dependencies**:
  - Builds on the strict MCP configuration model of the staged-reload-transaction Plan (cliplc005), which is already implemented: `_MCP_SERVER_KEYS` and the `reject_unknown_keys` call in `_build_single_server` are in the current source (`scripts/shared/mcp_config.py:37-53`, `:368`), and its 38 procedures are archived under `implementations/done/20261125-074359_*` (UNK-01 resolved in this cycle). This Plan blocks cliplc007, cliplc008, and cliplc013.
  - **Depends on**: plans/done/20261124-110935_cliplc005_staged-reload-transaction.md | phase 1 | its strict `_build_single_server` parser declares the allowed MCP key set that this Plan extends with `credential_env`; the dependency is closed — the Plan is archived and its phase 1 code is present in the current source (re-verified in this cycle).

## Background
- Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 7), filed as `issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`.
- Related archived work the Issue asks to re-verify: `issues/done/20261004-065422_mcp002_filter_env-inherits-dangerous-loader-env-vars-from-parent-process-into-mcp-subprocess.md` (introduced the default-deny environment allowlist) and `issues/done/20261016-093001_mcp003_allowlist_basename_only_path_injection.md` (introduced opt-in strict confinement).
- Path B was selected at Step 3: 16 target rows, a public configuration interface change (`McpServerConfig.fields` removed, `credential_env` added), a new module, and a behavior change for production startup (strict confinement default).

## Problem
- Validation and execution can use different binaries: `SubprocessLauncher.create_and_validate_proc` discards the path `validate` returns and runs `cfg.cmd` as written.
- `popen_kwargs.update(cfg.fields)` runs after `start_new_session: True`, so a configured `fields` dictionary can override `shell`, `env`, `stdout`, `stderr`, `start_new_session`, or `preexec_fn`.
- Production runs in permissive mode (nothing sets `LLMAGENT_STRICT_COMMAND`), so a binary whose basename is `node`, `python`, `uv`, and so on is accepted from any directory on `PATH`; no owner or file-mode check exists.
- Server keys come from TOML section names and are used unvalidated in `{tmp}/mcp_server_logs/{server_key}` (path traversal), registry keys, and log or status text.
- `filter_env` passes every `MCP_*_AUTH_TOKEN`, every `MCP_*_CONTROL_TOKEN`, and `GITHUB_TOKEN` to every server, and returns `None` (full parent environment inherited) when `cfg.env` is `None`.

## Reason for Change
- Process-launch security and credential isolation. MCP process ownership (cliplc007) restarts and tracks processes, so it must build on a launch that is already safe and uniform.

## Implementation Intent
- Add a frozen launch specification built by the command validator after validation, from the config and the server key only. The launcher takes that object and has no other way to influence `Popen`. Confinement becomes strict by default, credentials move from wildcard inheritance to a per-server declared set derived from the server key plus an explicit extra list, and a shared identifier validator guards every place the key becomes a path.

## Requirements
- `REQ-001`: Define an immutable `LaunchSpec` whose `argv[0]` is the validated absolute executable, whose remaining arguments are strings, whose process options (`start_new_session=True`, `stdout=DEVNULL`, `shell` never set, `stderr`, `env`) are fixed by one construction site, and which the launcher consumes as its only `Popen` input.
- `REQ-002`: Remove `McpServerConfig.fields` and the `popen_kwargs.update(cfg.fields)` merge; no config value or dataclass argument may override `shell`, `env`, `stdout`, `stderr`, `start_new_session`, or `preexec_fn`. No `cwd` option is added.
- `REQ-003`: Validation and execution use the same executable: the launcher runs the path `CommandValidator.validate` returns. The file identity (device, inode) recorded at validation is re-checked immediately before `Popen`, and a PATH change after validation cannot change the launched binary because `argv[0]` is the resolved absolute path.
- `REQ-004`: Strict confinement is the default: the resolved executable must be a regular file directly inside the trusted binary directory, the directory must not be group- or world-writable, the executable must not be group- or world-writable, and both must be owned by the Agent's effective user or root. Permissive mode (basename allowlist) is available only through an explicit opt-in environment variable intended for development and tests.
- `REQ-005`: Server identifiers match `^[a-z0-9][a-z0-9_-]{0,63}$` (lowercase ASCII, digits, underscore, hyphen; no dots, separators, whitespace, control characters; at most 64 characters). `McpServerConfig` rejects a non-matching non-empty `key`, `_build_mcp_servers` rejects a non-matching section name, and the stderr log manager rejects a non-matching key before building the log directory. The log directory name is the validated key.
- `REQ-006`: The child environment is built from a fixed runtime set (`PATH`, `HOME`, `USER`, `LOGNAME`, `SHELL`, `TMPDIR`, `TMP`, `TEMP`, `LANG`, `LC_*`, `LLMAGENT_CONFIG_DIR`, `LLMAGENT_SUDACHI_DICT`), the server's own `MCP_<KEY>_AUTH_TOKEN` and `MCP_<KEY>_CONTROL_TOKEN`, the variables named in the server's `credential_env` list, and the configured `env` (denylist and protected-variable rules unchanged). The wildcard token patterns and the unconditional `GITHUB_TOKEN` pattern are removed. The environment is always an explicit minimal dictionary, never `None`.
- `REQ-007`: `config/agent.toml` declares `credential_env = ["GITHUB_TOKEN"]` for the `github` and `cicd` servers only; no other shipped server receives `GITHUB_TOKEN`. The launch audit log records environment key names only, never values.
- `REQ-008`: A command rejected by the real `CommandValidator` (which raises `HttpStartupError`, a `RuntimeError`) releases the stderr handle and its tracking entries, as the `ValueError` path already does.
- `REQ-009`: Unit and integration tests cover the launch-spec contract, override rejection, PATH and symlink change after validation, server-key traversal and control characters, cross-server credential isolation, and minimal-environment startup for every shipped MCP server; they are written before the implementation changes.
- `REQ-010`: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` and `docs/90_deployment/deployment_01_deployment.md` describe the launch-spec contract, the trusted-directory policy, the identifier rule, and the per-server credential model; generated API artifacts are regenerated, never hand-edited.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/mcp_config.py | Modify: add `validate_server_key`, enforce it in `McpServerConfig` and `_build_mcp_servers`; remove the `fields` dataclass field; add `credential_env` field and parse key | Key rule, `fields` removal, per-server credential declaration | REQ-002, REQ-005, REQ-006; AC-2, AC-4 | `fields: dict[str, Any]` at lines 108-110; `_MCP_SERVER_KEYS` at 37-53 and `reject_unknown_keys` at 368 already declare the allowed key set; `_build_single_server` passes `key=key` at 405 with no key-pattern check (re-verified in this cycle) | tests/shared/test_mcp_config_validation.py | Verified |
| scripts/agent/http_lifecycle_launch_spec.py | Create (new file): frozen `LaunchSpec`, the fixed option set, and the minimal-environment builder | One construction site for the Popen inputs | REQ-001, REQ-006, REQ-007; AC-1, AC-3 | No launch-spec type exists; `popen_kwargs` is a free dict at `http_lifecycle_subprocess_launcher.py:96-103` (checked in Step 3) | tests/agent/test_http_lifecycle_launch_spec.py | Verified |
| scripts/agent/http_lifecycle_command_validator.py | Modify: strict default with explicit permissive opt-in, owner and file-mode checks, identity capture, narrowed env allowlist, `filter_env` replaced by a per-server builder | Confinement and credential isolation | REQ-003, REQ-004, REQ-006; AC-1, AC-2, AC-3 | `_strict_confinement` opt-in at lines 118-121 (`_STRICT_ENV_VAR` at 75); wildcard patterns at 63-65 inside `_DEFAULT_ALLOWED_ENV_VARS` (51-66); `filter_env` returns `None` for `None` at line 241 (re-verified in this cycle) | tests/agent/test_http_lifecycle_command_validator.py | Verified |
| scripts/agent/http_lifecycle_subprocess_launcher.py | Modify: build and run a `LaunchSpec`, drop `cfg.fields`, execute the validated path, release stderr on `HttpStartupError` | Execute what was validated; no option override | REQ-001, REQ-002, REQ-003, REQ-008; AC-1, AC-2 | `validate(...)` return discarded at line 84; `popen_kwargs` at 96-103 with `popen_kwargs.update(cfg.fields)` at 102-103; `Popen(cfg.cmd, **popen_kwargs)` at 106-107; `except ValueError` at line 85 vs `HttpStartupError(RuntimeError)` (re-verified in this cycle) | tests/agent/test_http_lifecycle.py | Verified |
| scripts/agent/http_lifecycle_stderr_log_manager.py | Modify: reject an invalid key before building `{tmp}/mcp_server_logs/{key}` | Key must not become a path component | REQ-005; AC-4 | `log_dir = f"{tempfile.gettempdir()}/mcp_server_logs/{server_key}"` at line 46 (checked in Step 3) | tests/agent/test_http_lifecycle_stderr_log_manager.py | Verified |
| config/agent.toml | Modify: add `credential_env = ["GITHUB_TOKEN"]` to `[mcp_servers.github]` and `[mcp_servers.cicd]` | Only designated servers get `GITHUB_TOKEN` | REQ-007; AC-3 | Only `scripts/mcp_servers/github` and `scripts/mcp_servers/cicd` read `GITHUB_TOKEN` (`rg environ.get("GITHUB_TOKEN")`); both tables at lines 293-309 (checked in Step 3) | tests/agent/test_http_lifecycle_env_allowlist_integration.py | Verified |
| tests/shared/test_mcp_config_validation.py | Modify: add key-pattern, `fields`-removed, and `credential_env` type cases | Validate REQ-002, REQ-005, REQ-006 | REQ-005, REQ-009; AC-4 | Existing server-key error case at 168-170 and env-denylist cases at 176-188 (re-verified in this cycle) | itself | Verified |
| tests/agent/test_http_lifecycle_launch_spec.py | Create (new file): spec immutability, fixed options, minimal env, credential isolation, key names only in audit | Cover the new module | REQ-001, REQ-006, REQ-007, REQ-009; AC-1, AC-3 | New module has no test file (checked in Step 3) | itself | Verified |
| tests/agent/test_http_lifecycle_command_validator.py | Modify: strict-by-default, opt-in permissive, owner and mode, PATH and symlink change after validation, replaced env-filter cases | Cover REQ-003, REQ-004, REQ-006 | REQ-003, REQ-004, REQ-009; AC-1, AC-2 | 36 existing cases cover allowlist, strict mode, and `filter_env` (checked in Step 3) | itself | Verified |
| tests/agent/test_http_lifecycle.py | Modify: replace `test_cfg_fields_reach_popen_kwargs` (line 295) with an override-impossible test; make the validation-failure test use the real validator's `HttpStartupError` | Existing test pins the removed behavior and masks the leak | REQ-002, REQ-008, REQ-009; AC-2 | Test sets `fields={"cwd": ...}` at line 299; failure test mocks `ValueError` at line 195 (re-verified in this cycle) | itself | Verified |
| tests/agent/test_http_lifecycle_env_allowlist_integration.py | Modify: replace the pattern-alignment gate with a per-server gate (each shipped server's child env holds its own tokens, no other server's) and start every shipped server under the minimal env | Static allowlist gate pins the wildcard model | REQ-006, REQ-007, REQ-009; AC-3 | Imports `_DEFAULT_ALLOWED_ENV_VARS` and calls `CommandValidator().filter_env({})` at lines 183 and 301 (checked in Step 3) | itself | Verified |
| tests/agent/test_http_lifecycle_stderr_log_manager.py | Modify: add traversal and control-character key cases | Cover REQ-005 at the path boundary | REQ-005, REQ-009; AC-4 | 216-line file; no key-validity case (checked in Step 3) | itself | Verified |
| docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | Modify: replace the inherited-variable list and `env` text with the per-server model; document `credential_env` and the key rule | Documentation Impact | REQ-010; AC-5 | "Inherited variables" list at lines 25-28 names the wildcard patterns (re-verified in this cycle) | `tools/check_docs_*` gates | Verified |
| docs/90_deployment/deployment_01_deployment.md | Modify: describe strict confinement default, the opt-in permissive variable, and owner and mode requirements | Documentation Impact | REQ-010; AC-5 | Line 240 states the CommandValidator rejects binaries under a writable directory (checked in Step 3) | `tools/check_docs_*` gates | Verified |
| docs/23_agent/agent_13_reference-api-generated.md | Regenerate (never hand-edit) | Public symbols change | REQ-010; AC-5 | Lists `CommandValidator` (checked in Step 3) | generator check | Verified |
| registry/manifests/agent_api.yaml | Regenerate (never hand-edit) | Public symbols change | REQ-010; AC-5 | Lists `CommandValidator` (checked in Step 3) | generator check | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/config_builders.py | The Issue names it as a target; it only calls `_build_mcp_servers` (defined in `shared/mcp_config.py`), so it needs no change | REQ-005 |
| scripts/agent/http_lifecycle.py | Calls `create_and_validate_proc` and logs `cfg.cmd` (line 346); constructs the validator and launcher | REQ-001, REQ-003 |
| scripts/agent/http_lifecycle_errors.py | `HttpStartupError` is a `RuntimeError`, not a `ValueError` | REQ-008 |
| scripts/shared/config_utils.py | `resolve_env_ref` resolves `${ENV:...}` inside the child | REQ-006 |
| scripts/agent/production_config_validator.py | Production validation entry; confirms no server-key check exists there | REQ-005 |
| scripts/mcp_servers/github/github_service_init.py | Reads `GITHUB_TOKEN` | REQ-007 |
| scripts/mcp_servers/cicd/cicd_service_init.py | Reads `GITHUB_TOKEN` | REQ-007 |
| config/github_mcp_server.toml | Child-side `${ENV:MCP_GITHUB_*}` references | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-003): The executable passed to `Popen` equals the path `validate` returned; a PATH change or a symlink retarget after validation does not change it, and a changed file identity before `Popen` aborts the start with a `StartupFailure`.
- AC-2 (REQ-002, REQ-004, REQ-008): No `fields` attribute or argument exists; `LaunchSpec` cannot carry `shell`, `env` override, `stdout`, `stderr` override, `start_new_session=False`, or `preexec_fn`; with default settings a binary outside the trusted directory, or owned by another user, or group/world-writable, is rejected; a rejected command leaves no stderr handle or tracking entry.
- AC-3 (REQ-006, REQ-007): For each shipped server, the child environment holds that server's own two tokens and no other server's; `GITHUB_TOKEN` appears for `github` and `cicd` only; the environment is a dict even with no configured `env`; no log line contains an environment value.
- AC-4 (REQ-005): Keys containing `.`, `/`, `\`, whitespace, control characters, uppercase, or more than 64 characters are rejected by `McpServerConfig`, by `_build_mcp_servers`, and by the log manager, and no directory is created for them.
- AC-5 (REQ-010): The two documentation files describe the final behavior and the generated artifacts are regenerated.

## Tests
- REQ-001, REQ-002: construct `LaunchSpec` directly with unsafe options and assert rejection or absence; assert `McpServerConfig(fields=...)` raises `TypeError`.
- REQ-003: patch `PATH` and retarget a symlink between `validate` and spawn; assert the spawned `argv[0]` is the validated path; swap the file between validation and spawn and assert the identity re-check aborts.
- REQ-004: tmp-directory fixtures for wrong owner (mocked `os.stat` uid), group-writable executable, group-writable directory, symlink in the trusted directory; default is strict; the opt-in variable restores the basename allowlist.
- REQ-005: parametrized keys (`..`, `a/b`, `a.b`, `A`, `a b`, `a\n`, 65 characters, empty) against all three enforcement points.
- REQ-006, REQ-007: two-server fixture proving A's env lacks B's tokens; shipped `config/agent.toml` loop asserting the exact env key set per server; log capture asserting key names only.
- REQ-008: `start()` with the real `CommandValidator` and a rejected command asserts the stderr handle closed and `_stderr_files` empty.
- REQ-009: real-child startup for every shipped subprocess server under the minimal env (existing integration gate, retargeted).

## Documentation Impact
- Yes. REQ-010 drives updates to the MCP server-config field document (`mcp_06_02`) and the deployment document (`deployment_01`), located via `docs/00_index.md` "Document References by Task"; `docs/23_agent/agent_13_reference-api-generated.md` and `registry/manifests/agent_api.yaml` are regenerated by their generator, not edited.

## Assumptions
- Strict-by-default replaces the opt-in `LLMAGENT_STRICT_COMMAND`; the opt-in name for permissive mode is `LLMAGENT_COMMAND_MODE=permissive` (a judgment call, falsifiable by the owner at procedure review). No production or development indicator exists in `scripts/` (`rg LLMAGENT_ENV|is_production` finds none), so an explicit variable is the only available switch.
- All ten shipped subprocess servers use `cmd = ["/opt/llm/bin/mcp_<name>"]` (`config/agent.toml:239-327`) and `/opt/llm/bin` is mode 0755 owned by uid 1000, the Agent user; the shipped binaries therefore pass strict confinement. A deployment with a different owner would be rejected by the new owner check.
- The parent's `PATH`, `HOME`, `USER` remain inherited for the runtime set because the existing protected-variable rule already treats them as parent-controlled.
- cliplc005 is already implemented: `_build_single_server` is the strict declared-key parser (`_MCP_SERVER_KEYS` at `scripts/shared/mcp_config.py:37-53`, `reject_unknown_keys` called at 368), so this Plan's parser edit adds `credential_env` to that existing key set instead of rewriting a coercing parser. Its procedures are archived under `implementations/done/20261125-074359_*` (verified in this cycle).
- Overlap judgment (`tools/check_plan_target_overlaps.py`, run after the freeze): no other Frozen Plan in `plans/` lists any of these files; no overlap to judge.
- The `fields` removal is safe: `_build_single_server` never sets it, so no TOML configuration can reach it today; the only user is `tests/agent/test_http_lifecycle.py:299` (re-verified in this cycle).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Resolved in this cycle: cliplc005's strict-parser procedures (`implementations/done/20261125-074359_*`) are implemented, so `_build_single_server` already declares the allowed key set | None: `_MCP_SERVER_KEYS` at `scripts/shared/mcp_config.py:37-53` and the `reject_unknown_keys` call at 368 are in the current source | This Plan's `scripts/shared/mcp_config.py` step adds `credential_env` to `_MCP_SERVER_KEYS` | False |
| UNK-02 | Whether any out-of-tree deployment places `mcp_*` binaries owned by a user other than the Agent user, which the new owner check would reject | Deployment inventory beyond `/opt/llm/bin` on this host | Check owner on the target host at deploy time (`skills/deploy/SKILL.md`); report any rejected server rather than relaxing the check | False |
| UNK-03 | Whether the rag_pipeline child needs credentials beyond its own two tokens (`rag/ingestion` configs) | The static scan found only `MCP_RAG_PIPELINE_*` references in `config/`; runtime reads in `scripts/rag` are not exhaustively confirmed | The real-child startup gate (REQ-009) starts every shipped server under the minimal env; a failure names the missing variable and is added to that server's `credential_env` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/mcp_config.py | Modify | High (19 modules import it) | N/A | N/A | Yes: a source change under `scripts/` needs a deploy |
| scripts/agent/http_lifecycle_launch_spec.py | Create | Medium | N/A | N/A | Yes |
| scripts/agent/http_lifecycle_command_validator.py | Modify | Medium | N/A | N/A | Yes |
| scripts/agent/http_lifecycle_subprocess_launcher.py | Modify | Medium | N/A | N/A | Yes |
| scripts/agent/http_lifecycle_stderr_log_manager.py | Modify | Low | N/A | N/A | Yes |
| config/agent.toml | Modify | High (startup config for every server) | N/A | N/A | Yes: config change needs a deploy |
| tests/shared/test_mcp_config_validation.py | Modify | Low | N/A | N/A | None |
| tests/agent/test_http_lifecycle_launch_spec.py | Create | Low | N/A | N/A | None |
| tests/agent/test_http_lifecycle_command_validator.py | Modify | Low | N/A | N/A | None |
| tests/agent/test_http_lifecycle.py | Modify | Low | N/A | N/A | None |
| tests/agent/test_http_lifecycle_env_allowlist_integration.py | Modify | Low | N/A | N/A | None |
| tests/agent/test_http_lifecycle_stderr_log_manager.py | Modify | Low | N/A | N/A | None |
| docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | Modify | Low | N/A | N/A | None |
| docs/90_deployment/deployment_01_deployment.md | Modify | Low | N/A | N/A | None |
| docs/23_agent/agent_13_reference-api-generated.md | Regenerate | Low | N/A | N/A | None |
| registry/manifests/agent_api.yaml | Regenerate | Low | N/A | N/A | None |

## Design
- **Issue Verification** (each claim re-checked against current source; Step 2):

| Issue claim | Verdict | Evidence |
|---|---|---|
| Launcher builds env with `filter_env(cfg.env)` | Confirmed | `http_lifecycle_subprocess_launcher.py:69` |
| `popen_kwargs.update(cfg.fields)` follows `start_new_session: True`, so `fields` can override it | Confirmed, with a correction | Lines 96-107. `_build_single_server` never passes `fields`, so TOML cannot reach it; the exposure is direct construction and the one test at `tests/agent/test_http_lifecycle.py:299` |
| Permissive mode accepts a resolved basename on an allowlist and returns a resolved path | Confirmed | `http_lifecycle_command_validator.py:83-89` (docstring), 180-196, with `return cmd_path` at 177 (strict) and 198 (permissive) |
| Validation may resolve one binary while another runs | Confirmed | `validate(...)` result discarded (launcher line 84); `Popen(cfg.cmd, **popen_kwargs)` at 106-107 runs the unresolved `cfg.cmd[0]` |
| `filter_env(None)` behavior | Confirmed | Returns `None` (line 241), so `Popen(env=None)` inherits the full parent environment. Not reachable from TOML (`dict(v.get("env", {}))`), reachable by direct construction |
| `MCP_*_AUTH_TOKEN` and `GITHUB_TOKEN` inherited by all servers | Confirmed | Patterns in `_DEFAULT_ALLOWED_ENV_VARS` (lines 63-65) |
| Server keys unvalidated, used in paths | Confirmed | `http_lifecycle_stderr_log_manager.py:46`; no key check in `mcp_config.py` or `production_config_validator.py` |
| Strict mode is a production control | Corrected | Opt-in only: `_STRICT_ENV_VAR` at `http_lifecycle_command_validator.py:75` and `self._strict_confinement` at 118-121 read `LLMAGENT_STRICT_COMMAND`, which no deploy script or config sets, so production is permissive |
| (Found) validation failure releases stderr | Contradicted | `validate` raises `HttpStartupError(RuntimeError)`, the launcher catches `ValueError` at line 85; the handle and `_stderr_files` entry leak. The existing test (`test_http_lifecycle.py:195`) mocks a `ValueError`, which hides it |
| `scripts/agent/config_builders.py` is a target | Corrected | It only imports `_build_mcp_servers`; the builder lives in `shared/mcp_config.py`. It is a reference row |

- **Launch spec**: `LaunchSpec` is a frozen dataclass in a new `scripts/agent/http_lifecycle_launch_spec.py` (agent layer; it depends on `shared.mcp_config` only, consistent with the import-layer contract). `CommandValidator` returns the resolved path and file identity; one `build_launch_spec(server_key, cfg, resolved, env, stderr)` call produces the spec. The launcher calls `Popen(spec.argv, **spec.popen_kwargs())`, where `popen_kwargs()` is the only source of keyword arguments.
- **Identity check**: capture `(st_dev, st_ino)` of the resolved file during validation and compare immediately before `Popen`. The residual window between that check and `execve` is documented, not closed (see Risks); strict confinement makes it unreachable for an attacker who cannot write the trusted directory.
- **Credentials**: derived keys are `MCP_<KEY.upper()>_AUTH_TOKEN` and `MCP_<KEY.upper()>_CONTROL_TOKEN` (every shipped child config uses exactly these names; checked by the existing `${ENV:...}` scan). Extra variables come from `credential_env` and must name variables, not patterns.
- **Consumer scan** (`tools/scan_change_consumers.py`, seed `scripts/shared/mcp_config.py`): 20 direct script importers, none reads `McpServerConfig.fields`; `rg "\.fields\b"` finds only the launcher. Each candidate is `not affected: field never read` except the launcher and the stderr log manager (targets). ADR citations of `tests/shared/test_mcp_config.py` cases are untouched because those cases are not edited.
- **Predictable fallout**: `tests/agent/test_http_lifecycle_env_allowlist_integration.py` pins the removed patterns (target row); generated reference artifacts (rows 15-16); no tool inventory change; module size gate: the new module is small and the validator grows by under 60 lines.
- **Step 2 and Step 3a revalidation (this cycle)**: all 16 rows re-checked against the current source; every row still passes the four Plan-Freeze checks, and no other Frozen Plan in `plans/` lists any of these files. Corrected evidence: `fields` at `scripts/shared/mcp_config.py:108-110` (was line 77); validator at 118-121, 51-66, 241 (was 107-109, 56-71, 240); launcher `Popen` at 106-107 (was 108); `tests/agent/test_http_lifecycle.py` at 195 and 295/299 (was 152 and 252/256); `tests/shared/test_mcp_config_validation.py` at 168-188 (was 168-186); `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` at 25-28 (was 23-28); `scripts/agent/http_lifecycle.py:346` (was 343). cliplc005 is implemented, so UNK-01 is resolved and the stale `Reference Files` row naming its pending procedure was removed (a `Reference Files` row is never a modification target, so implementation scope is unchanged).

## Implementation steps
1. **Phase 1: Tests first (REQ-009)**
   - [ ] Add the unsafe-option, override, cross-server credential, key-pattern, PATH and symlink change, owner and mode, and `HttpStartupError` release tests, expecting failure (REQ-009; tests/shared/test_mcp_config_validation.py, tests/agent/test_http_lifecycle_launch_spec.py, tests/agent/test_http_lifecycle_command_validator.py, tests/agent/test_http_lifecycle.py, tests/agent/test_http_lifecycle_stderr_log_manager.py, tests/agent/test_http_lifecycle_env_allowlist_integration.py)
2. **Phase 2: Identifier rule and configuration (REQ-005, REQ-006, REQ-007)**
   - [ ] `validate_server_key`, key enforcement, `fields` removal, `credential_env` field and parse (scripts/shared/mcp_config.py)
   - [ ] Key check before the log directory (scripts/agent/http_lifecycle_stderr_log_manager.py)
   - [ ] `credential_env` for `github` and `cicd` (config/agent.toml)
3. **Phase 3: Launch spec and confinement (REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-008)**
   - [ ] `LaunchSpec` and minimal-environment builder (scripts/agent/http_lifecycle_launch_spec.py)
   - [ ] Strict default, owner and mode checks, identity capture, narrowed allowlist, per-server env (scripts/agent/http_lifecycle_command_validator.py)
   - [ ] Launcher consumes the spec, executes the validated path, releases stderr on `HttpStartupError` (scripts/agent/http_lifecycle_subprocess_launcher.py)
4. **Phase 4: Documentation and generated artifacts (REQ-010)**
   - [ ] Update docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md and docs/90_deployment/deployment_01_deployment.md; regenerate docs/23_agent/agent_13_reference-api-generated.md and registry/manifests/agent_api.yaml
5. **Phase 5: Deployment & Verification**
   - [ ] Run `uv run ruff format`, `uv run ruff check`, `uv run mypy`, and the full `uv run pytest`; hand off to `skills/deploy/SKILL.md` after the change is committed and pushed (deploying is the user's decision); confirm owner and mode of `/opt/llm/bin` and every `mcp_*` binary before restart (UNK-02) (REQ-004, REQ-009; scripts/agent/http_lifecycle_command_validator.py, config/agent.toml)

### Release units
**Unit**: R1-launch-spec | **Phases**: 2, 3 | **Reason**: removing `fields` and the wildcard patterns breaks the existing launcher and tests until the spec-based launcher and the per-server environment land together; the tests-first Phase 1 is expected to fail until then.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/mcp_config.py | Unit | `uv run pytest tests/shared/test_mcp_config_validation.py tests/shared/test_mcp_config.py` | Key and `credential_env` cases pass |
| scripts/agent/http_lifecycle_launch_spec.py | Unit | `uv run pytest tests/agent/test_http_lifecycle_launch_spec.py` | Spec contract and isolation pass |
| scripts/agent/http_lifecycle_command_validator.py | Unit | `uv run pytest tests/agent/test_http_lifecycle_command_validator.py` | Strict default, owner and mode, identity pass |
| scripts/agent/http_lifecycle_subprocess_launcher.py | Unit | `uv run pytest tests/agent/test_http_lifecycle.py` | Validated path executed, no override, stderr released |
| config/agent.toml and shipped servers | Integration | `uv run pytest tests/agent/test_http_lifecycle_env_allowlist_integration.py` | Every shipped server starts under its minimal env |
| All changed Python | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml` | Clean |
| Whole suite and coverage | Regression | `uv run pytest` and the diff-cover sequence in `rules/toolchain.md` | Green; changed lines at the Completion-checklist threshold |
| docs and generated artifacts | Gates | the checkers in `rules/tool-gates.md` "When to run which tool" | No findings |

Validation quality baseline (Step 5): `radon cc` average complexity A or B for all four Python targets, no C-or-worse block; `vulture scripts/ --min-confidence 80` reports only three unrelated 100%-confidence findings in `rag/ingestion/document_manager.py`, `shared/mcp_call_state_contract.py`, `shared/runtime_paths.py`; `bandit` reports 0 Low, 4 Medium, 24 High findings repository-wide for `scripts/agent` and `scripts/shared` (pre-existing, not in the target functions); the diff-cover baseline is N/A in this document-only phase (no diff exists) and is recorded at implementation.

## Risks
- **Risk**: Strict-by-default rejects a binary that production currently runs in permissive mode (the Issue marks this `不明`; all shipped `cmd` values are in `/opt/llm/bin`) → **Mitigation**: UNK-02 check of owner and mode at deploy time; the explicit opt-in variable exists for development; a rejected server aborts startup with a named `StartupFailure` rather than starting a degraded Agent.
- **Risk**: Removing wildcard token inheritance leaves a server without a variable it reads (UNK-03) → **Mitigation**: the real-child startup gate for every shipped server runs before merge; the missing name goes into that server's `credential_env`.
- **Risk**: A residual race remains between the identity re-check and `execve` → **Mitigation**: the trusted directory must not be group- or world-writable and must be owned by the Agent user or root, so only a privileged attacker can win it; recorded in the deployment document.
- **Risk**: `McpServerConfig` has 19 importing modules; removing a field and adding one can break an equality-based `/reload` diff → **Mitigation**: the consumer scan found no reader of `fields`; the new field participates in equality like `env` does, which is the intended restart-required behavior from cliplc005.
- **Risk**: Landing before cliplc005 conflicts on `_build_single_server` → **Mitigation**: resolved in this cycle; cliplc005's strict parser is already in the source (`_MCP_SERVER_KEYS` at `scripts/shared/mcp_config.py:37-53`, `reject_unknown_keys` at 368), so this Plan's edit extends an existing declared key set rather than racing a pending rewrite.
- **Risk**: A secret reaches a log line → **Mitigation**: the audit records key names only, asserted by a log-capture test (AC-3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | In Progress | — | — | Expected to fail until Phases 2-3 land Procedures generated 20261125-223712 |
| 2 | Phase 2: identifier rule and configuration | In Progress | — | — | Release unit R1-launch-spec Procedures generated 20261125-223712 |
| 3 | Phase 3: launch spec and confinement | In Progress | — | — | Release unit R1-launch-spec Procedures generated 20261125-223712 |
| 4 | Phase 4: documentation and generated artifacts | In Progress | — | — | Regenerate, do not hand-edit Procedures generated 20261125-223712 |
| 5 | Phase 5: deployment and verification | Pending | — | — | Deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261125-223712_01_scripts_shared_mcp_config.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-223712_02_scripts_agent_http_lifecycle_launch_spec.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-223712_03_scripts_agent_http_lifecycle_command_validator.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-223712_04_scripts_agent_http_lifecycle_subprocess_launcher.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-223712_05_scripts_agent_http_lifecycle_stderr_log_manager.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-223712_06_config_agent.toml.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-223712_07_tests_shared_test_mcp_config_validation.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-223712_08_tests_agent_test_http_lifecycle_launch_spec.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-223712_09_tests_agent_test_http_lifecycle_command_validator.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-223712_10_tests_agent_test_http_lifecycle.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-223712_11_tests_agent_test_http_lifecycle_env_allowlist_integration.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-223712_12_tests_agent_test_http_lifecycle_stderr_log_manager.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-223712_13_docs_22_mcp_mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261125-223712_14_docs_90_deployment_deployment_01_deployment.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261125-223712_15_docs_23_agent_agent_13_reference-api-generated.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261125-223712_16_registry_manifests_agent_api.yaml.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-111909
- **Related target files**: scripts/shared/mcp_config.py, scripts/agent/http_lifecycle_launch_spec.py, scripts/agent/http_lifecycle_command_validator.py, scripts/agent/http_lifecycle_subprocess_launcher.py, scripts/agent/http_lifecycle_stderr_log_manager.py, config/agent.toml, tests/shared/test_mcp_config_validation.py, tests/agent/test_http_lifecycle_launch_spec.py, tests/agent/test_http_lifecycle_command_validator.py, tests/agent/test_http_lifecycle.py, tests/agent/test_http_lifecycle_env_allowlist_integration.py, tests/agent/test_http_lifecycle_stderr_log_manager.py, docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md, docs/90_deployment/deployment_01_deployment.md, docs/23_agent/agent_13_reference-api-generated.md, registry/manifests/agent_api.yaml

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (launch-spec object) | scripts/agent/http_lifecycle_launch_spec.py | 3 | AC-1 | tests/agent/test_http_lifecycle_launch_spec.py | Explicit in issue |
| REQ-001 | Required Changes; launcher line 96-108 | scripts/agent/http_lifecycle_subprocess_launcher.py | 3 | AC-1 | tests/agent/test_http_lifecycle.py | Confirmed by repository evidence |
| REQ-002 | Required Changes (`fields`); launcher line 102 | scripts/shared/mcp_config.py | 2 | AC-2 | tests/shared/test_mcp_config_validation.py | Confirmed by repository evidence |
| REQ-002 | Required Changes (reject overrides) | scripts/agent/http_lifecycle_subprocess_launcher.py | 3 | AC-2 | tests/agent/test_http_lifecycle.py | Explicit in issue |
| REQ-003 | Problem (validate vs execute); launcher line 84 | scripts/agent/http_lifecycle_command_validator.py | 3 | AC-1 | tests/agent/test_http_lifecycle_command_validator.py | Confirmed by repository evidence |
| REQ-003 | Problem; launcher line 84, 108 | scripts/agent/http_lifecycle_subprocess_launcher.py | 3 | AC-1 | tests/agent/test_http_lifecycle.py | Confirmed by repository evidence |
| REQ-004 | Required Changes (trusted directory); validator lines 107-166 | scripts/agent/http_lifecycle_command_validator.py | 3 | AC-2 | tests/agent/test_http_lifecycle_command_validator.py | Confirmed by repository evidence |
| REQ-004 | Required Changes (production confinement) | docs/90_deployment/deployment_01_deployment.md | 4 | AC-5 | docs gates | Derived from confirmed evidence |
| REQ-005 | Required Changes (server identifier) | scripts/shared/mcp_config.py | 2 | AC-4 | tests/shared/test_mcp_config_validation.py | Explicit in issue |
| REQ-005 | stderr log manager line 46 | scripts/agent/http_lifecycle_stderr_log_manager.py | 2 | AC-4 | tests/agent/test_http_lifecycle_stderr_log_manager.py | Confirmed by repository evidence |
| REQ-006 | Required Changes (per-server credentials); validator lines 56-71, 222-257 | scripts/agent/http_lifecycle_command_validator.py | 3 | AC-3 | tests/agent/test_http_lifecycle_env_allowlist_integration.py | Confirmed by repository evidence |
| REQ-006 | Required Changes (minimal environment) | scripts/agent/http_lifecycle_launch_spec.py | 3 | AC-3 | tests/agent/test_http_lifecycle_launch_spec.py | Explicit in issue |
| REQ-006 | Required Changes (declared environment keys) | scripts/shared/mcp_config.py | 2 | AC-3 | tests/shared/test_mcp_config_validation.py | Derived from confirmed evidence |
| REQ-007 | Required Changes (`GITHUB_TOKEN` only for designated servers); `rg GITHUB_TOKEN scripts/mcp_servers` | config/agent.toml | 2 | AC-3 | tests/agent/test_http_lifecycle_env_allowlist_integration.py | Confirmed by repository evidence |
| REQ-007 | Required Changes (audit key names only) | scripts/agent/http_lifecycle_launch_spec.py | 3 | AC-3 | tests/agent/test_http_lifecycle_launch_spec.py | Explicit in issue |
| REQ-008 | Verification finding: `HttpStartupError` is a `RuntimeError` | scripts/agent/http_lifecycle_subprocess_launcher.py | 3 | AC-2 | tests/agent/test_http_lifecycle.py | Confirmed by repository evidence |
| REQ-009 | Testing Expectations | tests/shared/test_mcp_config_validation.py | 1 | AC-4 | itself | Explicit in issue |
| REQ-009 | Testing Expectations | tests/agent/test_http_lifecycle_launch_spec.py | 1 | AC-1, AC-3 | itself | Explicit in issue |
| REQ-009 | Testing Expectations | tests/agent/test_http_lifecycle_command_validator.py | 1 | AC-1, AC-2 | itself | Explicit in issue |
| REQ-009 | Testing Expectations | tests/agent/test_http_lifecycle.py | 1 | AC-2 | itself | Explicit in issue |
| REQ-009 | Testing Expectations (minimal-environment startup for every shipped server) | tests/agent/test_http_lifecycle_env_allowlist_integration.py | 1 | AC-3 | itself | Explicit in issue |
| REQ-009 | Testing Expectations (server-key control characters) | tests/agent/test_http_lifecycle_stderr_log_manager.py | 1 | AC-4 | itself | Explicit in issue |
| REQ-010 | Documentation Impact | docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | 4 | AC-5 | docs gates | Explicit in issue |
| REQ-010 | Documentation Impact (generated reference) | docs/23_agent/agent_13_reference-api-generated.md | 4 | AC-5 | generator check | Derived from confirmed evidence |
| REQ-010 | Documentation Impact (generated manifest) | registry/manifests/agent_api.yaml | 4 | AC-5 | generator check | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261125-223712 -->