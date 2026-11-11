## Goal

Verify that the Agent records each tool's `retry_class` from the Agent's own stored state (`workflow.sqlite` `tool_call_state.retry_class`), not from the dispatcher's dedup config, and that an unknown tool stays `non_retryable` after the config-isolation refactor (`REQ-004`).

## Scope
**Release unit**: N/A: config-isolation test; independent of the Empty-store fail-closed release unit (Plan Implementation steps, Phase 3 + Phase 4).

## Assumptions
- seq 04 refactors `scripts/agent/tool_runner.py` so `retry_class` is obtained from the Agent's own stored state instead of importing the dispatcher's `retry_class()` (`tool_runner.py` L24 `from shared.mcp_dedup import retry_class`; current call `record_tool_call(task_id, key, pc.name, retry_class(pc.name))` at L177 passes no config, so it currently falls through to `load_dedup_config()` → `mcp_dedup.toml`).
- The dispatcher classifies dispatch-capable MCP tools; the Agent stores the resulting value in `workflow.sqlite` for replay. The recorded value therefore reflects the dispatcher's classification, but its SOURCE is the Agent's stored state, not the imported function.
- Open (flag, do not fabricate): the exact shape of the Agent-side lookup (which helper/column reads the stored value) is decided by the seq 04 refactor; this test pins the observable contract (recorded value matches stored classification; unknown stays `non_retryable`).

## Design decisions
- **Pin the source, not just the value.** The existing `test_retry_class_from_owner` (L2412-2433) asserts `recorded_write[4] == retry_class("write_file") == "retryable"` — i.e. the recorded value equals the dispatcher-config-sourced function verbatim. After the refactor the recorded value must be asserted against the Agent's stored classification, not against `shared.mcp_dedup.retry_class(...)`.
- **Unknown stays `non_retryable`.** An unlisted tool must resolve to `non_retryable` from the Agent's stored state (fail-safe; REQ-004 / `mcp_dedup.py` L166-170 default preserved).

## Alternatives considered
- **Assert only the final string (`"retryable"`/`"non_retryable"`).** Rejected as insufficient alone: the value could coincidentally match while still being sourced from the dispatcher config. The test must also assert the source is the Agent's stored state (e.g. by stubbing/disabling the dispatcher config load and confirming the recorded value is unchanged, or by asserting the recorded value tracks the stored column).

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
1. In `TestToolCallStateProducer`, modify `test_retry_class_from_owner` (L2412-2433): replace the assertion that the recorded value equals `shared.mcp_dedup.retry_class(name)` verbatim with an assertion that the recorded value equals the Agent's stored classification for the same tool. Concretely, drive the Agent's stored `retry_class` (via the recorder/state-store the producer writes to) and assert `recorded_write[4]` / `recorded_read[4]` track those stored values rather than the imported function.
2. Add an unknown-tool case: record a call for a tool absent from any classification and assert the recorded value is `non_retryable`.
3. Guard the source: if the test environment can still reach the dispatcher config, neutralise it (e.g. point `LLMAGENT_CONFIG_DIR` at an empty temp dir or stub `load_dedup_config`) so the only way the recorded value becomes `retryable`/`non_retryable` is the Agent's stored state. This proves the import path was removed.

### Method
- Extend the existing `FakeRecorder`-based producer test (the recorded tuple carries `retry_class` at index 4, L2222); assert against the stored value the producer wrote, not the imported function.
- Keep the test async and `_state_ctx`-wired like the surrounding producer tests (L2238-2248).

### Details
- The module import `from shared.mcp_dedup import retry_class` (L39) may become unused once the test no longer calls `retry_class(...)`; remove it if nothing else in the file references it, to avoid an unused-import lint failure. Verify usage before removing.
- Do not change `FakeRecorder.record_tool_call`'s signature (index-4 contract, L2215/L2222).

## Compatibility considerations
- Existing producer tests (`test_pending_recorded_before_dispatch`, etc.) are unaffected; only `test_retry_class_from_owner` changes shape.
- If seq 04 keeps a fallback to the dispatcher config for backwards compatibility, document it and ensure the test does not accidentally exercise that fallback.

## Security considerations
- Low: a wrong `retry_class` source could default a side-effecting tool to `retryable` and allow replay of a completed non-retryable effect. The unknown-tool `non_retryable` assertion guards this.

## Rollback considerations
Revert the commit. No state or schema changes.

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py -v`:
  - `test_retry_class_from_owner`: recorded value matches the Agent's stored classification for a listed tool (`write_file` → `retryable`, `read_text_file` → `non_retryable`), sourced from stored state, not the dispatcher config.
  - Unknown tool recorded as `non_retryable`.
  - Dispatcher config neutralised in-test; recorded value still correct (proves the import path was removed).
- Impact-radius check (`rules/toolchain.md`) for the config loader and dispatcher symbols; full validation sequence.

## Completion criteria
- `test_retry_class_from_owner` asserts the recorded `retry_class` comes from the Agent's own stored state, not `shared.mcp_dedup.retry_class`.
- An unknown tool records `non_retryable`.
- `uv run pytest tests/agent/test_tool_runner.py -v` passes.

## Out of Scope
- The `tool_runner.py` refactor itself (seq 04); this doc covers only its test.
- Config file edits (`config/agent.toml` seq 05, `config/mcp_dedup.toml` seq 06).
- ADR/db documentation (seq 10-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Modify `test_retry_class_from_owner` to pin the Agent-stored source; add unknown-tool `non_retryable` case | Pending | — | — | Coordinated with seq 04 |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — `retry_class` sourced from the Agent's own stored state, not the dispatcher config; unknown tools stay `non_retryable`
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `tests/agent/test_tool_runner.py`

### Companion test files
- `tests/agent/test_tool_runner.py` (this doc): `TestToolCallStateProducer.test_retry_class_from_owner` + unknown-tool case.
- Validation: `uv run pytest tests/agent/test_tool_runner.py -v` passes.
