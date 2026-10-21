# Module docstrings and helper comments describe components that no longer exist

## Priority
Low

## Summary
Correct the stale module-level claims in `scripts/agent/repl.py` and `scripts/shared/tool_executor_helpers.py`
so that a reader following the docstring reaches code that exists.

## Background
Module docstrings are the first architecture description a new reader sees, and these two are the entry
points for the REPL and tool paths.

## Problem
- `scripts/agent/repl.py:15` lists `ToolExecutor — MCP routing, error handling, TTL cache
  (shared/tool_executor.py)`. There is no cache or TTL in that module (`grep -in 'cache|ttl|idempot'
  scripts/shared/tool_executor.py` matches nothing); the module's own docstring (`:2-10`) describes it as the HTTP
  transport and routing layer (`HttpTransport` POST `/v1/call_tool`, `ToolRouteResolver`). The idempotency cache
  with TTL and eviction exists only server-side in `scripts/mcp_servers/dispatch.py`: TTL constant `:68`,
  `_duplicate_cache` `:93`, argument hashing `:101-106`, eviction `:113-119`, store `:122-129`, and the cache key
  is the caller-supplied `idempotency_key` (`:173`) that the Agent derives per logical call
  (`tool_runner.py:77-85`). `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:57-69` documents that correctly.
- `repl.py:19` names `AgentConfig — mutable runtime config dataclass (agent/config.py)`;
  `scripts/agent/config.py` does not exist (verified: `ls` reports no such file). The config dataclasses live
  in `scripts/agent/config_dataclasses.py`.
- `repl.py:21` states "Imported by agent.py as the entry point"; `scripts/agent.py` does not exist. The real
  entry point is `agent.repl:main()` (`repl.py:170-172`), which is what the deployed Nuitka binary
  `/opt/llm/bin/agent` is built from: `deploy/build_binaries.sh:124` lists `"agent.repl:agent:"` in its entry
  table and the generated launcher it compiles does `from agent.repl import main`
  (`build_binaries.sh:239-241`). `docs/90_deployment/deployment_01_deployment.md:185`, `:260` describe the same
  binary. Running `python scripts/agent/repl.py` from the repository root does fail with `ModuleNotFoundError`
  (verified); the reported missing module is the first package import, `No module named 'shared.config_loader'`
  from `scripts/agent/context.py:30`, not `agent`.
- `scripts/shared/tool_executor_helpers.py:41` states "Cache keys use plain string concatenation:
  f'{name}:{json_dumps(args)}'". No such cache key is constructed anywhere in `scripts/shared/` (verified). The
  only occurrence of that concatenation is the string `tool_hash_key` hashes before returning it (`:42-45`), and
  its real consumers use it as an identity for *failed* calls, not as a cache key: `tool_runner.py:237`
  (`out_failed_keys`) and `tool_loop_guard.py`. The one cache that does exist is the server-side idempotency
  cache described above, keyed by the idempotency key plus the tool name plus a normalized SHA-256 of the
  arguments (`dispatch.py:101-106`, `:122-129`) — i.e. the sentence describes a cache that no longer exists in
  this codebase and describes it incorrectly.
- The same block of `repl.py` also declares attributes nothing reads. Verified per attribute:
  - `_turn_active` (`:81`): no reader or writer in production outside `__init__`; the live flag is
    `ReplInputLoop._turn_active` (`repl_input_loop.py:66`, set at `:251`, cleared at `:314`). The only remaining
    references are two test *assignments* that nothing reads (`test_repl.py:1291`, `:1305`); both tests assert on
    `repl._ctx.conv.shutdown_requested` and `repl._shutdown_event`, so they pass without the attribute.
  - `_input_coro` (`:83`): never read in production; the live task is `ReplInputLoop._input_coro`
    (`repl_input_loop.py:67`, `:120`, `:149`), and the tests read that object as `repl._input_loop._input_coro`
    (`test_repl.py:172`, `:447`, `:703-704`).
  - `_prompt` (`:94-97`): returns `"> "` and has no consumer; the live prompts are literals inside the input
    path — `input("> ")` at `repl_input_loop.py:144` and `:191`, and the continuation prompt `input("... ")` at
    `cli_view.py:289`.
  - `_n_tools` (`:99-103`): a definition with no reference anywhere under `scripts/` or `tests/` (verified).
  - `_REPL_RESERVED_COMMANDS` (`:42`) is not dead: it is reachable through `reserved_repl_command_names()`
    (`:52-54`), consumed by `completion_command_names()` (`:59`) and by
    `tests/agent/commands/test_command_registry_consistency.py:104-109`. What is dead is a **second, unused
    copy** of the same `frozenset(["/exit"])` at `repl_input_loop.py:23`, which nothing in that module reads; a
    third copy is hardcoded inside `tools/check_docs_consistency.py:209`. Three definitions of one reserved set is
    the drift risk here, not the `repl.py` copy.
- `tools/check_docstrings.py` enforces the `scripts/<relpath> — <description>` header by requiring exactly one
  em-dash separator, and `agent/repl.py` is grandfathered as a violation
  (`tools/check_docstrings_baseline.txt:52`, kind `empty description`) because its architecture list uses one
  em-dash per line. Verified: with that baseline line removed the checker exits 1 ("stale baseline entry"), so a
  rewrite that accidentally makes the docstring conform fails the guard unless the baseline line is removed in the
  same change.
- `_spawned_subprocesses` (`:123`, `:132`) is handled in `shutdown003`.

## Reason for Change
These claims are how a new contributor locates the config dataclass, the entry point, and the tool cache. Each
of the three pointers currently leads to a file that does not exist, and the unused attributes make it
ambiguous which object owns the live state (`ReplInputLoop` does).

## Implementation Intent
Make module-level descriptions point at real files and real owners, and delete declared-but-unused state from
the composition facade.

## Target Files or Areas
- `scripts/agent/repl.py` (module docstring, `__init__`, unused properties)
- `scripts/shared/tool_executor_helpers.py` (comment at `:41`)

## Required Changes
- Update the `repl.py` architecture list to the actual modules and remove claims about a nonexistent cache and
  `agent/config.py` / `agent.py`. The corrected list must match `docs/23_agent/agent_12_reference-api.md:192-195`
  for the config owner (`agent/config_dataclasses.py`) and must not introduce a spaced em-dash on any line other
  than the header line the checker parses (see Constraints).
- State the real entry point: `main()` in this module, compiled into `/opt/llm/bin/agent` by
  `deploy/build_binaries.sh:124`, whose generated launcher does `from agent.repl import main`
  (`build_binaries.sh:239-241`).
- Remove `_turn_active`, `_input_coro`, `_prompt`, `_n_tools` from `AgentREPL`: nothing reads them (verified
  above). Keep `reserved_repl_command_names()`/`completion_command_names()`/`builtin_command_names()`/
  `SLASH_COMMANDS` as the documented public helpers they are. Do not remove `import subprocess` (`repl.py:27`): it
  exists for `_spawned_subprocesses` (`:123`, `:132`), which is `shutdown003`'s scope.
- Correct the `tool_executor_helpers.py:41` sentence so it describes what the function actually does — an MD5 over
  `f"{name}:{json_dumps(args)}"` used as a failed-call identity by `tool_runner.py:237` and `tool_loop_guard.py` —
  and either drops the cache-key claim or points at the real server-side cache in `scripts/mcp_servers/dispatch.py`
  without describing its key as a plain concatenation.

## Constraints
- Do not change behavior: this issue must not alter runtime paths.
- `SLASH_COMMANDS`, `builtin_command_names()`, `reserved_repl_command_names()`,
  `completion_command_names()` are public helpers; keep their behavior unless a test proves they are unused.
  Verified: all four have live consumers (`repl.py:79`, `repl.py:59`,
  `tests/agent/commands/test_command_registry_consistency.py:104-109`,
  `tests/agent/commands/test_agent_cmd_context.py:324`), so all four are kept.
- Any attribute removal must be checked against `tests/agent/test_repl.py` first. Checked: the only references to
  the four attributes are `test_repl.py:1291` and `:1305`, which assign `_turn_active` and assert on
  `repl._ctx.conv.shutdown_requested` / `repl._shutdown_event`; nothing reads the attribute, so the tests pass
  unchanged.
- The module docstring must keep the shape that `tools/check_docstrings_baseline.txt:52` records as a
  grandfathered violation (multiple em-dash-separated segments). Verified: deleting that baseline line without also
  making the docstring conform to one `scripts/<relpath> — <description>` separator makes
  `tools/check_docstrings.py` exit 1, and making the docstring conform without removing the baseline line also
  makes it exit 1. The two must move together or not at all.
- `docs/23_agent/agent_13_reference-api-generated.md:117` copies the first line of the **class** docstring of
  `AgentREPL`. Changing the module docstring does not require regenerating that table; changing the class
  docstring's first line does (`tools/generate_reference_table.py --type agent`).

## Acceptance Criteria
- Every file path named in a module docstring exists. Verified scope of this criterion: `repl.py:12-18` names six
  paths that exist (`agent/context.py`, `agent/cli_view.py`, `shared/llm_client.py`, `agent/history.py`,
  `agent/commands/registry.py`, `agent/orchestrator.py`); only `agent/config.py` (`:19`) does not, and
  `:21` names a nonexistent `agent.py`. `shared/tool_executor.py` (`:15`) exists; its claim about a TTL cache does
  not.
- No `AgentREPL` attribute remains that nothing reads. Measured against HEAD: `_turn_active`, `_input_coro`,
  `_prompt` and `_n_tools` have no production reader; `SLASH_COMMANDS`, `_ctx`, `_view`, `_diagnostic_store`,
  `_shutdown_event`, `_input_loop`, `_persister`, `_wal`, `_shutdown`, `_banner`, `_signal`, `_cmds`,
  `_orchestrator` do, and are kept.
- A grep for "TTL cache" in `scripts/agent/repl.py` and "Cache keys" in `scripts/shared/` returns nothing.
- `tools/check_docstrings.py` still exits 0 with `tools/check_docstrings_baseline.txt` byte-identical, or the
  `agent/repl.py` line is removed in the same change together with a docstring that conforms to the single
  separator the checker enforces. No other baseline line changes.
- The composition description names every object `repl.py` actually constructs. Measured against HEAD: the
  delegation paragraph (`:6-9`) already names `ReplInputLoop`, `SessionPersister`, `WalCheckpointManager`,
  `ResourceShutdownCoordinator`, `StartupBanner` and `SignalHandler`, and the two objects it omits while importing
  and constructing them are `DiagnosticStore` (`:32`, `:80`) and `StartupOrchestrator` (`:38`, `:120`). Those two
  are the gap to close; no other constructed object is missing.

## Testing Expectations
- Documentation-and-comment-only change plus attribute removals: run `uv run pytest tests/agent -q` to confirm
  no test depends on a removed attribute, then `uv run ruff check scripts/agent` and
  `uv run mypy --no-namespace-packages scripts/agent`.
- Also run `uv run python tools/check_docstrings.py` (must report no new violations and no stale baseline entry)
  and `uv run vulture scripts/agent/repl.py scripts/shared/tool_executor_helpers.py --min-confidence 80`, which
  currently reports nothing on these two files.
- No new test is required for the docstring text itself. Note the consequence: the criterion "every file path
  named in a module docstring exists" is enforced here by review, not by a guard. `tools/check_docstrings.py`
  validates only the docstring's own header path (`expected_prefix`), and `tools/fix_docstring_paths.py` rewrites
  only that header; neither inspects paths mentioned in a docstring body. Whether a guard for body paths should
  exist is recorded as an open question below.

## Documentation Impact
This issue changes in-code documentation only. If `docs/23_agent/` names any of the removed components, update
those sections in the same change; verify against `docs/00_index.md`'s scope mapping before editing. Verified
against HEAD:
- No file under `docs/` mentions `agent/config.py`, `scripts/agent.py` as an entry point, a `TTL cache` in
  `ToolExecutor`, `_prompt`, `_n_tools`, `AgentREPL._turn_active`, or the "Cache keys use plain string
  concatenation" sentence. Nothing in `docs/` needs correcting because of these stale claims.
- Two docs treat the `repl.py` docstring as the authoritative source of the layer split, so the corrected list
  must stay consistent with them: `docs/01_overview/overview_01_02-arch-pipelines.md:60` ("The responsibilities of
  each layer are declared in the docstrings of `agent/repl.py`") and
  `docs/23_agent/agent_07_04_cli-and-commands-purpose.md:32`.
- `docs/23_agent/agent_12_reference-api.md:192-195` already states the `AgentConfig` dataclass lives in
  `agent/config_dataclasses.py`; the docstring fix must match that existing wording, not invent a new owner.
- `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md:65` already describes `SLASH_COMMANDS` as
  derived from `_COMMANDS` plus REPL-reserved commands via `completion_command_names()`; that stays correct.

## Out of Scope
- Using `_spawned_subprocesses` at the REPL level (`shutdown003`).
- Adding a tool-result cache to `ToolExecutor` (no such feature is proposed).
- `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, which already documents the server-side cache correctly.
- The unused second copy of `_REPL_RESERVED_COMMANDS` at `repl_input_loop.py:23` and the third copy inside
  `tools/check_docs_consistency.py:209`. Consolidating three definitions of one reserved set is a design decision
  (`repl.py` imports `agent.repl_input_loop`, so the canonical copy could live there or in a shared constants
  module), and `repl_input_loop.py` is another issue's target file. Recorded here so it is not lost; deferred.
- Making the `repl.py` module docstring conform to the single-separator form `tools/check_docstrings.py` enforces,
  which would also drop one line from `tools/check_docstrings_baseline.txt`. That is a style migration, not the
  stale claim this issue is about.

## Dependencies
- Independent. `repl003` and `shutdown002` touch the same file; sequence this one last to avoid churn.
- Review after `repl001`, which decides whether signal handling reaches `ReplInputLoop` at all. If `repl001`
  changes what `AgentREPL` must hold in order to hand a shutdown event to the input loop (`repl.py:82`, `:85`,
  `:113-114`), the set of `AgentREPL` attributes that have a reader changes, and the removal list must be
  re-derived from the post-`repl001` tree rather than from HEAD.
- `test_repl.py:1291` and `:1305` assign `repl._turn_active` as scaffolding for assertions that never use it.
  After this issue's removal those two lines become inert assignments. `repl003` is the issue that rewrites that
  test class, so cleaning those two lines belongs there, not here.

## Unresolved Questions
- Is `AgentREPL._turn_active` kept intentionally as a public surface for tests or tooling? Needs confirmation
  before deletion.
  Resolved against HEAD: no. `SignalHandler` carries no `_turn_active` guard at all —
  `tests/agent/test_repl.py:1250-1259` records that the guard and the `_turn_active`/`_input_coro` attributes were
  removed from `SignalHandler` in commit `44d7f2e4f` in favour of `shutdown_event` coordination with
  `ReplInputLoop`, and `scripts/agent/signal_handler.py` contains no such attribute. The flag that is used lives
  in `ReplInputLoop` (`:66`, `:251`, `:314`). `AgentREPL._turn_active` came from `26dc21eff`, the original
  implementation commit, and has no reader: leftover state, not a public surface.
- Should a guard check the file paths a module docstring *body* names, the way `tools/check_docstrings.py` checks
  the header path? Nothing under `tools/` inspects body paths today (`check_docstrings.py` validates
  `expected_prefix` only; `fix_docstring_paths.py` rewrites the header only), which is why this drift survived.
  Whether it belongs in `tools/check_docstrings.py` or in a test is undecided and out of scope here.

## AI Implementation Instruction
Verify each named path exists before writing it. Delete unused state rather than documenting it.

## Traceability
- **Workflow phase**: `python-code-review` (REPL core-loop review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/repl.py`, `scripts/shared/tool_executor_helpers.py`
