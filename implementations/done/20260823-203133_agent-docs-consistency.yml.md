# Implementation Procedure: .github/workflows/agent-docs-consistency.yml

## Goal

Update the `run:` step invocation and the stale `paths:` filter entries to reference the
consolidated `tools/check_docs_consistency.py --domain agent` script instead of the
deleted `tools/check_agent_docs_consistency.py`, restoring real CI drift protection for
the agent doc domain.

## Scope

**In-Scope**
- The `run:` step: `python tools/check_agent_docs_consistency.py` ->
  `python tools/check_docs_consistency.py --domain agent`.
- Both `paths:` filter entries (under `push` and `pull_request`) listing
  `tools/check_agent_docs_consistency.py` -> `tools/check_docs_consistency.py`.

**Out-of-Scope**
- `on:` trigger types, the other `paths:` entries (`docs/05_agent_*.md`,
  `docs/90_shared_04_*.md`), `concurrency:` block, job name, `runs-on:`,
  `actions/checkout@v4`, `actions/setup-python@v5` with `python-version: "3.13"` — all
  left byte-for-byte identical.
- `pyproject.toml`'s `check-agent-docs` console-script entry (also stale, same defect
  class) — not one of this plan's two target files; flagged as a follow-up risk.
- Fixing the 29 pre-existing content-level warnings this check will newly surface —
  genuine doc-content issues, not part of this CI-invocation fix.

## Assumptions

- `tools/check_agent_docs_consistency.py` no longer exists — confirmed by `ls`
  returning "No such file or directory" during this review.
- `tools/check_docs_consistency.py --domain agent` is the correct, currently-supported
  replacement invocation — confirmed: `DOMAIN_PREFIXES` contains an `"agent"` key, and
  the `argparse --domain` argument's `choices=list(DOMAIN_PREFIXES.keys())` accepts it.
- Running `python tools/check_docs_consistency.py --domain agent` locally exits 0 today
  (29 pre-existing warnings, no errors) — per the source plan's already-recorded local
  verification; warnings do not fail the job, only errors do.
- `.pre-commit-config.yaml` does not separately invoke the deleted script — confirmed
  via `grep -n "check_agent_docs_consistency" .pre-commit-config.yaml` returning no
  matches, so no pre-commit config change is needed alongside this fix.

## Design decisions

- Pure one-line invocation-target swap in the `run:` block; keep `set -euo pipefail`
  and the step name (`Run Agent docs consistency checks`) unchanged.
- Update the stale `paths:` entries to `tools/check_docs_consistency.py` (not simply
  removed) so a future edit to the now-shared consolidated script still re-triggers
  this workflow.

## Alternatives considered

- Leave the `paths:` filter unpatched (only fix the `run:` step) — rejected: since
  `check_agent_docs_consistency.py` no longer exists, that `paths:` entry can never
  match a real file change again, silently narrowing the workflow's trigger surface
  compared to intent; updating it to the actual script that governs the check's
  behavior preserves the original trigger intent.

## Implementation

### Target file
`.github/workflows/agent-docs-consistency.yml`

### Procedure
1. Re-read the file immediately before editing to reconfirm content has not shifted.
2. In the `run:` block, replace `python tools/check_agent_docs_consistency.py` with
   `python tools/check_docs_consistency.py --domain agent`.
3. In both `push.paths` and `pull_request.paths`, replace
   `"tools/check_agent_docs_consistency.py"` with `"tools/check_docs_consistency.py"`.
4. Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('.github/workflows/agent-docs-consistency.yml'))"`
   (or `actionlint`/`yamllint` if available — neither was installed in this review's
   environment).
5. Diff the file and confirm only the `run:` line and the two `paths:` lines changed.

### Method
Direct text substitution in a YAML file — three lines changed total (one `run:` line,
two `paths:` lines), no structural YAML changes (no new keys, no reordering).

### Details
- No `deploy/deploy.sh` change needed — this is a CI workflow file, not a `scripts/`
  module.

## Compatibility considerations

- **Behavior change, intended**: this workflow currently fails before reaching any
  check logic (missing script -> immediate error), so it has never actually gated on
  doc content. After this fix, it will exit 0 with 29 pre-existing warnings surfaced
  for the first time — warnings do not fail the job, so CI status does not turn red,
  but the log output changes materially (new visible warnings). Documented as a risk in
  the source plan.

## Security considerations

N/A: CI configuration change only, no secrets or permissions altered.

## Rollback considerations

- Trivially revertable: reverting these three line changes restores the previous
  (non-functional but familiar) `run:`/`paths:` values. No other file depends on this
  one's exact content.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| .github/workflows/agent-docs-consistency.yml | Integration: local invocation matching new `run:` line | `python tools/check_docs_consistency.py --domain agent` | Exit 0; 29 pre-existing warnings, no `FileNotFoundError`/`ModuleNotFoundError` |
| .github/workflows/agent-docs-consistency.yml | YAML syntax | `python -c "import yaml; yaml.safe_load(open('.github/workflows/agent-docs-consistency.yml'))"` | No parse error |
| .github/workflows/agent-docs-consistency.yml | Manual diff review | `git diff .github/workflows/agent-docs-consistency.yml` | Only the `run:` line and two `paths:` lines changed |

This is a CI-YAML-only change; the `rules/toolchain.md` Python gate sequence does not
apply.

## Out of scope

- `.github/workflows/mcp-docs-consistency.yml` — covered by its own implementation
  procedure document.
- `pyproject.toml`'s stale `check-agent-docs` console-script entry — flagged as a
  follow-up, not fixed here (not one of this plan's two target files).

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-102217_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-203133
- Related target files: .github/workflows/agent-docs-consistency.yml
