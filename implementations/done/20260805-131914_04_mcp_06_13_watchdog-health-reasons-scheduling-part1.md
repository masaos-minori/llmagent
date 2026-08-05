# Implementation Procedure: 04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md

## Goal

Correct `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md` so it accurately
describes `record_failure()`, `record_degraded()`, and `get_degraded_reason()` behavior, and
resolves the prior contradiction with `docs/04_mcp_06_12_watchdog-configuration-monitoring.md`.

## Scope

- In scope: the "ヘルス理由の優先順位" / "プローブチェーン全体でのボディ理由の追跡" /
  "degraded の理由一覧" sections of this single file.
- Out of scope: `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md` (separate
  procedure document), `docs/04_mcp_06_12_watchdog-configuration-monitoring.md` (already
  confirmed accurate per the source plan), and any source code file.

## Assumptions

- The source plan's investigation findings (record_failure has no `reason` param,
  record_degraded exists but is uncalled, get_degraded_reason always returns None) are accurate
  as of the plan's writing.
- Verified during this procedure's own investigation (2026-08-05): `record_failure(server_key)`
  has no `reason` parameter (`scripts/shared/mcp_health.py:37`); `record_degraded()` is defined
  at `scripts/shared/mcp_health.py:54` with zero call sites in `scripts/` confirmed via
  `grep -rn "\.record_degraded(" scripts/ --include="*.py" | grep -v "def record_degraded"`
  (empty result); `get_degraded_reason()` (`scripts/shared/mcp_health.py:84`) is called from
  `scripts/agent/commands/cmd_mcp.py:189` and `:202`.
- Line references in the plan (`tool_executor.py:115`) have drifted; current call site is
  `scripts/shared/tool_executor.py:101`. `scripts/shared/tool_transport_invoker.py:157` is
  still current. Re-verify exact line numbers at edit time since this is a moving target.

## Design decisions

- Keep the existing doc structure (prose + annotated pseudo-code block) rather than
  restructuring the file; only correct factual claims, per `skills/python-design` guidance to
  keep changes minimal and scoped to the identified defect rather than a rewrite.
- State facts as verified current behavior, not as a permanent guarantee — `record_degraded`
  having zero call sites is a snapshot fact that can change; phrase it as "currently unused"
  rather than "will always be unused".
- Preserve the cross-reference to `docs/04_mcp_06_12_watchdog-configuration-monitoring.md` so
  readers land on the authoritative state-machine description.

## Alternatives considered

- Merge this content directly into `04_mcp_06_12` instead of keeping a separate part1 doc —
  rejected: out of scope per the source plan, which explicitly preserves the file split.
- Remove the pseudo-code walkthrough and use prose only — rejected: the existing doc's
  step-by-step snippet format is the established convention in this doc series and aids
  traceability to actual call order.

## Implementation

### Target file

`docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`

### Procedure

1. Open the file and locate the "プローブチェーン全体でのボディ理由の追跡" and
   "degraded の理由一覧" sections (approx. lines 45-70 as of 2026-08-05).
2. Re-confirm the three facts below against current source before editing (code may have
   moved since this document was written):
   - `record_failure(server_key)` signature and call sites
     (`scripts/shared/mcp_health.py:37`, `scripts/shared/tool_transport_invoker.py:157`,
     `scripts/shared/tool_executor.py:101`).
   - `record_degraded()` call-site count via the grep command above.
   - `get_degraded_reason()` call sites (`scripts/agent/commands/cmd_mcp.py:189`, `:202`).
3. Edit the prose/snippet so each fact is stated plainly and matches the current source.
4. Confirm the cross-reference link to `04_mcp_06_12_watchdog-configuration-monitoring.md`
   is present in both the inline text and the "Related Documents" list.

### Method

Direct manual Markdown edit of the flagged sections. No doc-generation tooling or script
involved.

### Details

- Source-of-truth symbols to cite: `record_failure` (`scripts/shared/mcp_health.py:37-52`),
  `record_degraded` (`scripts/shared/mcp_health.py:54-82`), `get_degraded_reason`
  (`scripts/shared/mcp_health.py:84-86`).
- Call-site references: `scripts/shared/tool_transport_invoker.py:157`,
  `scripts/shared/tool_executor.py:101`, `scripts/agent/commands/cmd_mcp.py:189,202`.

## Compatibility considerations

- Documentation-only change; no runtime or API compatibility impact.
- Terminology (`DEGRADED`, `UNAVAILABLE`, `HALF_OPEN`) must stay consistent with
  `docs/04_mcp_06_12_watchdog-configuration-monitoring.md` to avoid reintroducing a
  cross-doc contradiction.

## Security considerations

N/A — no secrets, credentials, or executable code paths are touched.

## Rollback considerations

- Single Markdown file change; revert via `git checkout -- docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`
  or a standard `git revert` of the commit introducing the change.

## Validation plan

- Manual review: re-read the edited section side-by-side with
  `scripts/shared/mcp_health.py` and confirm every claim currently holds.
- Re-run `grep -rn "\.record_degraded(" scripts/ --include="*.py" | grep -v "def record_degraded"`
  immediately before merging to reconfirm the "zero call sites" claim.
- Run `uv run check-mcp-docs` (per `rules/toolchain.md`) to confirm no broken internal links
  were introduced.

## Out of scope

- `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md` (covered by its own
  implementation-procedure document).
- `docs/04_mcp_06_12_watchdog-configuration-monitoring.md`.
- Any change to `scripts/shared/mcp_health.py`, `scripts/shared/tool_executor.py`,
  `scripts/shared/tool_transport_invoker.py`, or `scripts/agent/commands/cmd_mcp.py`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-067100_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-131914
- Related target files: 04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md
