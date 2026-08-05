# Implementation Procedure: 04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md

## Goal

- Update `docs/04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md` so it clearly
  explains the process-level impact ("blast radius") of an MCP subprocess server's startup
  `RuntimeError`, distinguishing `security_profile=production` (entire Agent process terminates)
  from `security_profile=local` (only the failing server is disabled; the rest of the Agent
  continues).

## Scope

- In scope: the single documentation file
  `docs/04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md`.
- Out of scope: any source code change; any other documentation file.
- This is a documentation-only edit — classification per `rules/coding.md` §"Current behavior"
  classification is **Accepted current specification** (the described behavior is correct and
  intentional fail-safe design), so the new text must be written as plain prose in the existing
  section with no "Current behavior" label.

## Assumptions

- The investigation findings in the source requirement
  (`requires/20260802-144026_require.md`, referenced by the plan) accurately describe the
  exception propagation path; verified directly against current source below.
- `HEALTH_CHECK_RETRY_DELAY_SEC = 1.0` (seconds) is the single retry delay used before the
  security-profile branch decides the outcome — confirmed in `scripts/agent/startup.py`.

## Design decisions

- Per `skills/python-design/workflow.md` "Evidence and Assumptions" guidance: describe only
  verified, current behavior as fact; do not introduce a new evidence-label system into this doc.
- Keep the addition as plain prose appended to the existing single-paragraph description, matching
  the doc's existing minimal style (no new headings needed given the doc's short length).
- Explicitly name both `SecurityProfile.PRODUCTION` and `SecurityProfile.LOCAL` outcomes so a
  reader cannot miss the asymmetry between "process crash" and "single server disabled".

## Alternatives considered

- Add a new `## Impact by security profile` subsection instead of extending the existing
  paragraph — rejected for this small doc to avoid over-structuring a 2-line file; a short
  additional paragraph is sufficient and keeps the doc proportionate to its current size.
- Use a "Current behavior" labelled callout — rejected per `rules/coding.md`: this is accepted,
  intentional specification, not a gap needing that framing.

## Implementation

### Target file

- `docs/04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md`

### Procedure

1. Read the existing file (already done — it is a short frontmatter + one paragraph + Related
   Documents/Keywords sections).
2. Insert a new paragraph immediately after the existing paragraph (before the `---` separator,
   line 17/18) describing the `security_profile`-dependent outcome.
3. Add the three source references (`scripts/agent/startup.py`,
   `scripts/agent/http_lifecycle.py`, `scripts/shared/mcp_config.py::SecurityProfile`) inline in
   the new paragraph or as a short trailing list.
4. Manually re-read the updated file for tone/register consistency (Japanese, plain prose, no
   English "Current behavior" label) and line length.

### Method

- Direct text edit (no code generation) of the single Markdown file; no build/compile step
  applies to documentation.

### Details

- Verified source facts to encode in the new paragraph:
  - `scripts/agent/startup.py:212` / `:276` — the single retry uses
    `HEALTH_CHECK_RETRY_DELAY_SEC = 1.0` (`scripts/agent/startup.py:44`) before the
    security-profile branch runs.
  - `scripts/agent/startup.py:227-231` (subprocess start retry) and `:290-293`
    (post-startup health check retry): when
    `ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION`, the retry failure is
    re-raised as `RuntimeError`, which is not caught locally and propagates out of
    `StartupOrchestrator.run()` (`scripts/agent/startup.py:98`, calls `_verify_mcp_health`
    at line 103) — terminating the Agent process.
  - `scripts/agent/startup.py:232-239` / `:294-301`: when `security_profile` is
    `SecurityProfile.LOCAL` (i.e., not `PRODUCTION`), the same failure is only logged as a
    warning and surfaced via `self._view.write_warning(...)`; the loop continues to the next
    server, so the rest of the Agent process and other MCP servers keep running.
  - `SecurityProfile` is a `StrEnum` defined at `scripts/shared/mcp_config.py:41` with members
    `LOCAL = "local"` (line 44) and `PRODUCTION = "production"` (line 45). Note: correct the
    plan's stated path `shared/mcp_config.py` to the actual repo path
    `scripts/shared/mcp_config.py` when writing the reference.
  - `scripts/agent/http_lifecycle.py` is where the underlying `/health` poll and
    `HttpStartupError(RuntimeError)` (`http_lifecycle.py:44`) originate (`start_http_subprocess`,
    referenced from `startup.py:197` / `:218`), before `startup.py` applies the
    security-profile-dependent handling described above.
- Do not claim a specific process-exit mechanism (e.g. `sys.exit`) beyond "the uncaught
  `RuntimeError` propagates out of the startup orchestrator" unless the caller chain proves an
  explicit exit call — keep the wording at the verified level ("terminates the Agent process")
  matching the plan's own phrasing.

## Compatibility considerations

- N/A — text-only change to a documentation file; no code, config, or API surface is touched.

## Security considerations

- Ensure no secrets or internal-only details are newly exposed; the existing code already masks
  secrets via `_mask_secrets()` before logging, and the doc only describes control flow, not
  credentials.

## Rollback considerations

- Revert is a single `git checkout -- docs/04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md`
  or equivalent revert commit; no migration or data-state implications.

## Validation plan

- Manual review only (per `plans/20260804-066800_plan.md` Validation plan table): confirm the
  updated paragraph clearly distinguishes `PRODUCTION` (process terminates) from `LOCAL` (server
  disabled, rest of Agent continues), includes the three source references, and matches the
  existing Japanese register and plain-prose style.
- Since this is a `docs/*.md`-only change, the code validation sequence in `rules/toolchain.md`
  (ruff/mypy/lint-imports/bandit/pytest/pre-commit) does not apply; optionally run
  `uv run check-mcp-docs` if available, since it checks Markdown/doc consistency
  (port/tool-name drift, broken internal links) — not required for this prose-only addition but
  safe to run.

## Out of scope

- Any change to `scripts/agent/startup.py`, `scripts/agent/http_lifecycle.py`, or
  `scripts/shared/mcp_config.py`.
- Any other documentation file under `docs/`.
- Filing an `issues/` entry — not applicable, since this is accepted/intentional behavior, not a
  bug or doc/code mismatch.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-066800_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-131446
- Related target files: 04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md
