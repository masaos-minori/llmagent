# Implementation Procedure: .github/workflows/mcp-docs-consistency.yml

## Goal

Update the `run:` step invocation and the stale `paths:` filter entry to reference the
consolidated `tools/check_docs_consistency.py --domain mcp` script instead of the
deleted `tools/check_mcp_docs_consistency.py`, restoring real CI drift protection for
the MCP doc domain.

## Scope

**In-Scope**
- The `run:` step: `python tools/check_mcp_docs_consistency.py` ->
  `python tools/check_docs_consistency.py --domain mcp`.
- Both `paths:` filter entries (under `push` and `pull_request`) listing
  `tools/check_mcp_docs_consistency.py` -> `tools/check_docs_consistency.py`.

**Out-of-Scope**
- `on:` trigger types, the other `paths:` entry (`docs/**/*.md`), `concurrency:`
  block, job name, `runs-on:`, `actions/checkout@v4`, `actions/setup-python@v5` with
  `python-version: "3.13"` — all left byte-for-byte identical.
- `pyproject.toml`'s `check-mcp-docs` console-script entry (also stale, same defect
  class) — not one of this plan's two target files; flagged as a follow-up risk.
- Fixing the 20 pre-existing content-level errors (stale doc-file references, MCP
  port-number mismatches vs. `config/agent.toml`) this check will newly surface —
  genuine doc-content issues, not part of this CI-invocation fix.

## Assumptions

- `tools/check_mcp_docs_consistency.py` no longer exists — confirmed by `ls` returning
  "No such file or directory" during this review.
- `tools/check_docs_consistency.py --domain mcp` is the correct, currently-supported
  replacement invocation — confirmed: `DOMAIN_PREFIXES` contains an `"mcp"` key.
- **Behavior change, intended and higher-impact than the agent-domain sibling fix**:
  running `python tools/check_docs_consistency.py --domain mcp` locally exits 1 today
  (20 genuine ERROR-level findings), per the source plan's already-recorded local
  verification — so this workflow will go from "silently broken (missing-script error)"
  to "genuinely red on real content drift" immediately after this fix merges, on the
  very next triggering push/PR. This is the intended, correct behavior per the source
  requirement's Acceptance Criteria.
- `.pre-commit-config.yaml` does not separately invoke the deleted script — confirmed
  via `grep -n "check_mcp_docs_consistency" .pre-commit-config.yaml` returning no
  matches.

## Design decisions

- Pure one-line invocation-target swap in the `run:` block; keep `set -euo pipefail`
  and the step name (`Run MCP docs consistency checks`) unchanged.
- Update the stale `paths:` entry to `tools/check_docs_consistency.py`, same rationale
  as the sibling `agent-docs-consistency.yml` procedure.

## Alternatives considered

- Fix the 20 pre-existing content-level errors as part of this same change, so the
  workflow doesn't immediately turn red — rejected: out of scope for this requirement
  (a CI-invocation fix, not a doc-content fix), and conflating the two would make this
  change harder to review and revert independently. The source plan documents this as
  an accepted, intended consequence in its Risks section, with a recommended follow-up
  issue instead.

## Implementation

### Target file
`.github/workflows/mcp-docs-consistency.yml`

### Procedure
1. Re-read the file immediately before editing to reconfirm content has not shifted.
2. In the `run:` block, replace `python tools/check_mcp_docs_consistency.py` with
   `python tools/check_docs_consistency.py --domain mcp`.
3. In both `push.paths` and `pull_request.paths`, replace
   `"tools/check_mcp_docs_consistency.py"` with `"tools/check_docs_consistency.py"`.
4. Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('.github/workflows/mcp-docs-consistency.yml'))"`.
5. Diff the file and confirm only the `run:` line and the two `paths:` lines changed.
6. Before or immediately after merging, file a follow-up issue documenting the 20
   pre-existing MCP doc-content errors this fix newly surfaces, so maintainers are not
   surprised by the job turning red for a legitimate, expected reason (per the source
   plan's Risks section).

### Method
Direct text substitution in a YAML file — three lines changed total, no structural YAML
changes.

### Details
- No `deploy/deploy.sh` change needed — CI workflow file, not a `scripts/` module.

## Compatibility considerations

- **Behavior change, intended, CI-status-visible**: this workflow will start exiting 1
  (red) on the next triggering push/PR due to 20 real, pre-existing content-level
  errors that were never actually checked before (the job failed on a missing script
  before reaching the check logic). This is correct per the requirement's Acceptance
  Criteria, but is a visible change maintainers should be told about — see Procedure
  step 6.

## Security considerations

N/A: CI configuration change only, no secrets or permissions altered.

## Rollback considerations

- Trivially revertable: reverting these three line changes restores the previous
  (non-functional but familiar) `run:`/`paths:` values. If the newly-surfaced CI
  failures are disruptive before the content-level errors can be fixed, reverting this
  workflow file alone (without touching `tools/check_docs_consistency.py`) restores the
  prior (silently broken) status quo without needing any other file change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| .github/workflows/mcp-docs-consistency.yml | Integration: local invocation matching new `run:` line | `python tools/check_docs_consistency.py --domain mcp` | Exit 1 due to 20 pre-existing content-level errors (expected/unchanged by this fix) — no `FileNotFoundError`/`ModuleNotFoundError` |
| .github/workflows/mcp-docs-consistency.yml | YAML syntax | `python -c "import yaml; yaml.safe_load(open('.github/workflows/mcp-docs-consistency.yml'))"` | No parse error |
| .github/workflows/mcp-docs-consistency.yml | Manual diff review | `git diff .github/workflows/mcp-docs-consistency.yml` | Only the `run:` line and two `paths:` lines changed |

This is a CI-YAML-only change; the `rules/toolchain.md` Python gate sequence does not
apply.

## Out of scope

- `.github/workflows/agent-docs-consistency.yml` — covered by its own implementation
  procedure document.
- `pyproject.toml`'s stale `check-mcp-docs` console-script entry — flagged as a
  follow-up, not fixed here.
- The 20 pre-existing MCP doc-content errors themselves — a separate, unauthorized
  scope for this requirement; file as a follow-up issue instead (Procedure step 6).

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
- Related target files: .github/workflows/mcp-docs-consistency.yml
