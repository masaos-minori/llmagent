# Implementation Procedure: 04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md

## Goal

Correct `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md` so it removes
references to nonexistent config/log mechanisms and instead documents the actual error
counters and structured JSON audit log used for tool/transport error investigation.

## Scope

- In scope: the "ツールエラーとトランスポートエラーの区別" section (error-counter and
  audit-log subsections) of this single file.
- Out of scope: the "ツールのスケジューリングと直列化" section of the same file (already
  accurate per current content, not flagged by the source plan), `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`
  (separate procedure document), and any source code file.

## Assumptions

- The source plan's investigation findings (`repeated_tool_error_threshold`, `[debug]` log
  prefixes, and logfmt `error_type=tool`/`error_type=transport` grep patterns do not exist)
  are accurate as of the plan's writing.
- Verified during this procedure's own investigation (2026-08-05):
  `stat_tool_errors` / `stat_transport_errors` counters exist on `ToolTransportInvoker`
  (`scripts/shared/tool_transport_invoker.py:38-39`, incremented at lines ~145 and ~153) with
  no threshold or automatic warning log tied to them.
  A second, differently-scoped counter pair also exists on the agent's per-session stats
  (`ctx.stats.stat_tool_errors`, `scripts/agent/context.py:188`, incremented in
  `scripts/agent/tool_runner.py:283`); the doc should be clear it is describing the
  `ToolTransportInvoker` counters, not conflate the two.
- `audit_tool_exec()` (`scripts/agent/tool_audit.py:159`) emits a `ToolExecEvent`
  (`scripts/agent/shared/models.py:44-61`, frozen dataclass) with fields including
  `event: Literal["tool_exec"]` and `error_type: str = ""` (values `"transport"` / `"tool"` /
  `""`).

## Design decisions

- Keep the doc's existing two-subsection layout (counters, then audit log) and correct facts
  in place rather than restructuring, consistent with `skills/python-design` guidance to scope
  changes to the identified defect.
- Explicitly note the existence of a second, unrelated `stat_tool_errors` counter
  (agent-context-level) so a future reader does not conflate it with the
  `ToolTransportInvoker` counters this doc describes — avoids reintroducing ambiguity.
- Keep the corrected search examples in both `jq` and `grep` form (as already drafted in the
  file), since the audit log is JSON-lines and both tools are legitimate for that format.

## Alternatives considered

- Describe both counter pairs (`ToolTransportInvoker` and `AgentContext.stats`) in full detail
  — rejected: out of scope per the source plan, which only asked to document
  `ToolTransportInvoker`'s counters; adding the second pair in full would expand scope beyond
  the identified defect. A one-line disambiguation note is enough to prevent confusion.
- Drop the `ToolExecEvent` field list down to only `error_type` — rejected: `"event":"tool_exec"`
  is needed context for the `jq`/`grep` examples to make sense (it is the discriminator field
  used to filter to this event type in a shared audit log).

## Implementation

### Target file

`docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md`

### Procedure

1. Open the file and locate "エラーカウンタの追跡" and "監査ログによる詳細確認"
   subsections (approx. lines 27-46 as of 2026-08-05).
2. Re-confirm before editing (values may have moved since this document was written):
   - Counter fields and increment sites: `scripts/shared/tool_transport_invoker.py:38-39`
     (declaration), `~145`/`~153` (increments).
   - `ToolExecEvent` field list and `error_type` default/comment:
     `scripts/agent/shared/models.py:44-61`.
   - `audit_tool_exec()` signature and call to construct `ToolExecEvent`:
     `scripts/agent/tool_audit.py:159` onward.
3. Confirm no nonexistent items remain in the text: `repeated_tool_error_threshold`,
   `[debug]` prefix, or logfmt `error_type=tool`/`error_type=transport` grep patterns
   (search the file for these literal strings; expect zero matches after edit).
4. Add a brief disambiguation note distinguishing `ToolTransportInvoker`'s
   `stat_tool_errors`/`stat_transport_errors` from `AgentContext.stats.stat_tool_errors`
   (`scripts/agent/context.py:188`) if not already present, so the doc does not imply there is
   only one such counter pair in the codebase.

### Method

Direct manual Markdown edit of the flagged subsections. No doc-generation tooling involved.

### Details

- Source-of-truth symbols to cite: `ToolTransportInvoker.stat_tool_errors` /
  `stat_transport_errors` (`scripts/shared/tool_transport_invoker.py:38-39`), `ToolExecEvent`
  (`scripts/agent/shared/models.py:44-61`), `audit_tool_exec`
  (`scripts/agent/tool_audit.py:159`).
- Secondary counter for disambiguation only: `AgentContext.stats.stat_tool_errors`
  (`scripts/agent/context.py:188`, incremented at `scripts/agent/tool_runner.py:283`).

## Compatibility considerations

- Documentation-only change; no runtime or API compatibility impact.
- Field names/values quoted (`"tool_exec"`, `"transport"`, `"tool"`, `""`) must match
  `scripts/agent/shared/models.py` verbatim to avoid re-introducing a doc/code mismatch.

## Security considerations

- N/A for the change itself. When citing example log lines, ensure no real audit-log content
  (which may include masked but still user-supplied `args_preview` data) is pasted verbatim —
  use synthetic examples only, consistent with the file's existing placeholder examples.

## Rollback considerations

- Single Markdown file change; revert via `git checkout -- docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md`
  or a standard `git revert` of the commit introducing the change.

## Validation plan

- Manual review: re-read the edited subsections side-by-side with
  `scripts/shared/tool_transport_invoker.py`, `scripts/agent/shared/models.py`, and
  `scripts/agent/tool_audit.py` to confirm every claim currently holds.
- Grep the file for the removed nonexistent strings (`repeated_tool_error_threshold`,
  `[debug]`, `error_type=tool`, `error_type=transport`) to confirm zero remaining matches.
- Run `uv run check-mcp-docs` (per `rules/toolchain.md`) to confirm no broken internal links.

## Out of scope

- `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md` (covered by its own
  implementation-procedure document).
- The "ツールのスケジューリングと直列化" section of this same file (not flagged as
  inaccurate by the source plan).
- Any change to `scripts/shared/tool_transport_invoker.py`, `scripts/agent/shared/models.py`,
  `scripts/agent/tool_audit.py`, or `scripts/agent/context.py`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-067100_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-131959
- Related target files: 04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md
