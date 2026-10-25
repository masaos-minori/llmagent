# Plan: tools001 frontmatter gate command

## Goal
- Fix the `manage_frontmatter` validation gate in `tools/run_validation_gates.py` so it
  invokes `tools/manage_frontmatter.py` with a valid report-only subcommand instead of
  the invalid literal token `add-missing|dedupe-lists`, ending its permanent Fail, and
  add a regression test that locks the gate's argv to the subcommand CLI.

## Priority
High

## Scope
- **In-Scope**:
  - Replace the invalid `"add-missing|dedupe-lists"` argv token in the
    `manage_frontmatter` gate (tools/run_validation_gates.py:934-942) with the valid
    report-only invocation `add-missing` (default dry-run mode, exit 1 when Front Matter
    is missing).
  - Update the quoted command in `routing.md:114` to match the fixed gate.
  - Add a regression test in `tests/tools/test_run_validation_gates.py` asserting the
    gate's subcommand token is one of the CLI's valid choices (the existing test only
    asserts the gate name).
- **Out-of-Scope**:
  - Making `dedupe-lists` report-only (e.g. adding a `--dry-run` flag) so it can join
    the gate. The Issue's suggested `--fix --dedupe-lists` variant was rejected in
    verification: `cmd_dedupe_lists` (manage_frontmatter.py:442-452) writes files
    unconditionally and has no dry-run mode — a validation gate must not mutate files.
  - Any change to `tools/manage_frontmatter.py` itself.
- **Dependencies**: N/A: none.

## Background
`tools/run_validation_gates.py` runs each gate's canonical command as a subprocess;
gate data is a two-source table (`rules/toolchain.md` for full mode, `routing.md`
path-keyed checkers for fast mode). Review finding F-005 (High confidence) observed
the `manage_frontmatter` gate Fail with an argparse usage error on every run at head
`2e87bad46`.

## Problem
The gate passes the single argv token `"add-missing|dedupe-lists"` — a shell-style
alternation never split by the subprocess invocation. `manage_frontmatter.py`'s
argparse rejects it: re-measured at HEAD `b0415bd3d`, the invocation prints
`invalid choice: 'add-missing|dedupe-lists'` and exits 2. The gate is therefore a
permanent Fail whenever a docs/** diff selects it in fast mode. `routing.md:114`
quotes the same broken command and is the gate's routing source.

## Reason for Change
A permanently failing gate makes the fast-mode summary uninterpretable (real Front
Matter problems are indistinguishable from the usage error) and breaks the
single-Pass/Fail signal the orchestrator is built to provide.

## Implementation Intent
Swap one argv token for the valid `add-missing` subcommand, mirror the change in the
routing.md row that documents the gate, and lock the fix with a argv-level
regression test. No change to `manage_frontmatter.py`.

## Requirements
- `REQ-001`: The `manage_frontmatter` gate command in `tools/run_validation_gates.py`
  must invoke a valid CLI subcommand in report-only mode: `add-missing` (default
  dry-run; `--fix` not passed).
- `REQ-002`: `routing.md`'s Front Matter checker row must quote the corrected command,
  keeping the routing.md ↔ gate-table correspondence that the `drift` subcommand checks.
- `REQ-003`: A regression test must assert the gate's subcommand token is a valid
  `manage_frontmatter.py` subcommand choice, so a future edit cannot silently re-introduce
  an invalid argv token.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tools/run_validation_gates.py | Replace the invalid gate argv token with `add-missing` | Gate is a permanent Fail (exit 2 usage error) | REQ-001 / AC-1 | Gate entry at lines 934-942; re-measured usage error at HEAD `b0415bd3d` | tests/tools/test_run_validation_gates.py | Verified |
| routing.md | Update the quoted command in the Front Matter checker row (line 114) to the fixed invocation | Row quotes the broken string; it is the gate's routing source | REQ-002 / AC-2 | `routing.md:114` contains `add-missing\|dedupe-lists`; only occurrence outside the gate table and the Issue | tests/tools/test_run_validation_gates.py (drift gate: `tools/run_validation_gates.py drift`) | Verified |
| tests/tools/test_run_validation_gates.py | Add argv-level regression test for the gate | Existing test (`:95`) asserts gate name selection only; the gate itself was never validated | REQ-003 / AC-3 | Test file asserts `names >= {..., "manage_frontmatter"}` with no command assertions | (self) | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tools/manage_frontmatter.py | Confirm subcommand choices, `add-missing` default dry-run semantics (writes only with `--fix`, cmd_add_missing lines 197-308), and `cmd_dedupe_lists` unconditional writes (lines 442-452) that rule it out as a gate command | REQ-001 |
| tools/TOOL_DESCRIPTIONS.md | Confirm its `manage_frontmatter.py`/`run_validation_gates.py` entries describe behavior generically and contain no stale command string (verified: none) | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001): `uv run python tools/manage_frontmatter.py add-missing` exits 0 on
  a clean docs tree; the gate no longer emits the usage-error Fail in a fast-mode run
  selected by a docs/** diff.
- `AC-2` (REQ-002): `routing.md` contains no `add-missing\|dedupe-lists` string;
  `uv run python tools/run_validation_gates.py drift` exits 0.
- `AC-3` (REQ-003): The new test fails if the gate's subcommand token is replaced with
  an invalid choice and passes with `add-missing`; full
  `uv run pytest tests/tools/test_run_validation_gates.py -q` passes.

## Tests
- `REQ-003`: New test in tests/tools/test_run_validation_gates.py locates the
  `manage_frontmatter` Gate and asserts its argv subcommand token ∈
  {add-missing, dedupe-lists, merge-related, rename-category-to-area, classify} and
  that no token contains `|`.
- `REQ-001`: Existing selection test (`test_selection_docs_only_fast_mode`) must keep
  passing unchanged.

## Documentation Impact
`routing.md` (repo-root routing table, not under `docs/`) is a target row (REQ-002).
No `docs/*.md` update is required: `tools/TOOL_DESCRIPTIONS.md` describes these tools
generically and contains no stale command string (verified by grep).

## Assumptions
- `add-missing` exit code: 0 when all docs have valid Front Matter, non-zero when
  issues are found (cmd_add_missing returns 1 on docs-dir/issue paths, 0 otherwise;
  clean-tree run measured exit 0). Gate value depends on this contract.
- The gate intentionally checks Front Matter presence only; duplicate-list detection
  remains a manual maintenance command (`dedupe-lists`), as documented in
  tools/TOOL_DESCRIPTIONS.md.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | None. All Issue claims verified against source at HEAD `b0415bd3d`, including the rejection of the Issue's `--fix --dedupe-lists` suggestion. | N/A: no unresolved evidence gap | N/A | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tools/run_validation_gates.py | Gate argv token swap | Any fast-mode run that selects the docs gate (docs/** diffs); no runtime service consumes it | N/A: Path A skipped historical analysis | N/A: Path A skipped historical analysis | tools/ is rsynced by deploy.sh; no new dependencies; no service restarts required |
| routing.md | Command string fix in one table row | Docs/routing readers and the gate drift check | N/A: Path A skipped historical analysis | N/A: Path A skipped historical analysis | rsynced by deploy.sh; no restarts required |
| tests/tools/test_run_validation_gates.py | New regression test | Test-only | N/A: Path A skipped historical analysis | N/A: Path A skipped historical analysis | rsynced to `/opt/llm/tests/`; no restarts required |

## Design
Gate commands must be non-mutating; that rule is what selects `add-missing` (dry-run by
default) over the Issue's proposed `--fix --dedupe-lists` (dedupe writes
unconditionally). Keeping one argv tuple per Gate entry preserves the existing gate
table structure; no Gate schema change is needed.

## Implementation steps

1. **Phase 1: Gate fix**
   - [ ] Replace `"add-missing|dedupe-lists"` with `"add-missing"` in the gate entry (REQ-001; tools/run_validation_gates.py)
2. **Phase 2: Routing and test update**
   - [ ] Update the Front Matter checker row command string (REQ-002; routing.md)
   - [ ] Add the argv-level regression test (REQ-003; tests/tools/test_run_validation_gates.py)
3. **Phase 3: Verification and deployment check**
   - [ ] Run `uv run pytest tests/tools/test_run_validation_gates.py -q`, `uv run python tools/manage_frontmatter.py add-missing`, and `uv run python tools/run_validation_gates.py drift` (REQ-001..REQ-003; tools/run_validation_gates.py)
   - [ ] Deployment validation: tools/, tests/, and routing.md are rsynced by deploy.sh; confirm the deployed gate converges on next deploy; no service restart needed (REQ-001; tools/run_validation_gates.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/run_validation_gates.py | Integration (gate command executed) | `uv run python tools/manage_frontmatter.py add-missing` | exit 0, "All files have valid YAML Front Matter." |
| tests/tools/test_run_validation_gates.py | Unit (new + existing tests) | `uv run pytest tests/tools/test_run_validation_gates.py -q` | all pass; new test fails on an invalid token mutation |
| routing.md | Consistency gate | `uv run python tools/run_validation_gates.py drift` | exit 0 |

## Risks
- **Risk**: The fixed gate no longer detects duplicate list-field entries in docs Front
  Matter (dedupe is not report-capable). → **Mitigation**: accepted trade-off;
  duplicate detection remains available as the manual `dedupe-lists` command. If gated
  dedupe detection is wanted later, a separate Issue should add a dry-run mode to
  `dedupe-lists` first (out-of-scope here).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix gate argv in tools/run_validation_gates.py | Pending | — | — | Phase 1 |
| 2 | Update routing.md row | Pending | — | — | Phase 2 |
| 3 | Add regression test | Pending | — | — | Phase 2 |
| 4 | pytest + manage_frontmatter + drift verification, deploy.sh check | Pending | — | — | Phase 3 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blockers identified | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261025-210306_tools001_frontmatter-gate-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-214041
- **Related target files**: tools/run_validation_gates.py, routing.md, tests/tools/test_run_validation_gates.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Evidence (gate entry, observed exit 2); re-measured at HEAD b0415bd3d | tools/run_validation_gates.py | Phase 1 | AC-1 | Validation plan row 1 | Explicit in issue |
| REQ-002 | Repository evidence: routing.md:114 quotes the broken string (discovered in verification; Issue did not list it) | routing.md | Phase 2 | AC-2 | Validation plan row 3 | Derived from confirmed evidence |
| REQ-003 | Issue Verification section: existing tests assert only gate name; gate never validated | tests/tools/test_run_validation_gates.py | Phase 2 | AC-3 | Validation plan row 2 | Explicit in issue |
