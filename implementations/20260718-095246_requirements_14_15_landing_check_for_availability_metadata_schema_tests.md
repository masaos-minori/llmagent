# Implementation procedure: pre/post landing-status gate for requirements 14/15 (requirement 18, plan steps 1 and 6)

Source plan: `plans/20260717-175630_plan.md` ("Add schema tests for MCP runtime availability
metadata", requirement 18), Implementation steps 1 and 6.

**Disambiguation note (per this batch's established convention)**: named with the specific
requirement-number slug rather than the generic `full_validation_pass`, matching the precedent set
by `implementations/20260718-094534_requirement_17_disabled_reason_landing_check.md` (requirement
17's analogous gate for requirement 15). Checked all existing `implementations/*.md` filenames and
contents for `"requirement 14"` / `"requirement 15"` combined in one landing-check doc before
writing this — none exists; the closest matches
(`implementations/20260717-225949_requirements_04_09_landing_check.md`,
`implementations/20260718-094534_requirement_17_disabled_reason_landing_check.md`) are gates for
different requirement pairs (04/09, and 17-checks-15 respectively), not this one. Not a duplicate.

## Goal

Before writing hard (non-`xfail`) assertions in the two new test files this plan adds
(`tests/test_tool_schema.py`, `tests/test_tools_endpoint.py`), and again before finally removing any
`xfail` markers from them, mechanically re-verify whether sibling requirements 14 (`requires_config`
-> `config_dependent` rename, `plans/20260717-173602_plan.md`) and 15 (add `enabled`/
`disabled_reason`, `plans/20260717-174024_plan.md`) have actually landed in real `scripts/` source
(not merely as `implementations/*.md` design docs). This plan's own tests are meaningless as hard
assertions until that dependency is real, per the plan's Risks table ("assert on fields that do not
exist in production code yet").

## Scope

**In scope**: a two-point procedural check (not a source-file change) —
1. Pre-check (plan step 1): `grep -rn "config_dependent\|disabled_reason" scripts/mcp_servers/`,
   run once before writing the two new test files' assertions, to decide whether each assertion is
   written as a hard assertion or wrapped in `pytest.mark.xfail(strict=True)`.
2. Post-check (plan step 6): the same grep, re-run once both dependencies are believed to have
   landed, followed by removing every `xfail` marker and re-running the suite to confirm the
   assertions now pass unconditionally (not just because `xfail` was masking a failure).

**Out of scope**: implementing requirements 14 or 15 themselves (separate plans/lineages — requirement
14 already has its own `implementations/*.md` lineage, e.g.
`implementations/20260718-090322_full_validation_pass_config_dependent_rename.md`; requirement 15
likewise, e.g. `implementations/20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md`).
This doc only gates requirement 18's own two new test files against that external landing status.

## Assumptions

- At the time this documents-only workflow pass is being run (today, `2026-07-18`, processing the
  RuntimeToolRegistry/MCP-availability-metadata plan batch), `grep -rn "config_dependent\|disabled_reason"
  scripts/` returns **zero matches** repo-wide (verified directly; also matches the source plan's own
  Assumption 2). Every current `TOOL_LIST` entry across `read_tools.py` / `write_tools.py` /
  `delete_tools.py` / `git/tools.py` still uses the old `"requires_config"` key (confirmed by direct
  read of `scripts/mcp_servers/file/read_tools.py` and `scripts/mcp_servers/git/tools.py` — the latter
  has 10 `"requires_config": True` occurrences, none renamed). Neither requirement 14 nor 15 has
  landed in real source yet, only as `implementations/*.md` design docs (this entire batch, per the
  batch's own convention, is documents-only at this stage).
- Therefore the pre-check (point 1 above) resolves today to "not landed" — the two new test files
  must be written with `xfail(strict=True)` wrapping every assertion on `config_dependent`,
  `enabled`, and `disabled_reason` at implementation time. The post-check (point 2) cannot be
  resolved today; it is recorded here as a mandatory future step for whoever turns this plan's
  design docs into real committed test code, to run only after requirements 14 and 15's own design
  docs have themselves been turned into real `scripts/` changes.
- `strict=True` is required (not plain `xfail`) so that an unexpectedly-passing assertion (i.e. the
  dependency landed but the `xfail` marker was left in place) itself becomes a hard test failure,
  forcing marker removal rather than silently masking drift forever — this mirrors the exact
  reasoning already used for the same pattern in requirement 15/16's own risk mitigations.

## Implementation

### Target file

None (process/checklist step, not a source file) — governs the `xfail` gating strategy inside
`tests/test_tool_schema.py` (this batch's companion doc,
`implementations/{same-timestamp-block}_test_tool_schema.py.md`) and
`tests/test_tools_endpoint.py` (companion doc `..._test_tools_endpoint.py.md`).

### Procedure

1. Immediately before writing assertions in either new test file, run:
   `grep -rn "config_dependent\|disabled_reason" scripts/mcp_servers/`.
2. **If zero matches** (current state, confirmed today): write every assertion that depends on
   `config_dependent`, `enabled`, or `disabled_reason` existing/being correctly shaped, wrapped at
   the individual parametrize-case level in `@pytest.mark.xfail(reason="depends on requirement 14/15
   landing in scripts/mcp_servers/", strict=True)`. Assertions that do NOT depend on those fields
   (e.g. `name`/`description`/`inputSchema`/`status` non-emptiness, `TestClient` returning HTTP 200)
   remain hard, unwrapped assertions — only the specific new-field checks get the marker.
3. **If matches are found** (requirements 14/15 have landed): write the corresponding assertions as
   plain hard assertions with no `xfail` wrapper at all — do not add the marker preemptively only to
   remove it later.
4. At final-completion time (plan step 6), re-run the same grep. If it now returns matches (and it
   did not before), go through both test files, remove every remaining `xfail(strict=True)` marker
   whose dependency has landed, and run
   `uv run pytest tests/test_tool_schema.py tests/test_tools_endpoint.py -v` once more to confirm
   every previously-`xfail`'d case now passes as a hard assertion (a `strict=True` xfail that
   unexpectedly passes surfaces as `XPASS(strict)` failure, which is the intended forcing function —
   do not silence it by re-adding a non-strict marker).
5. Record the check's outcome (landed / not landed, date, matches found if any) in the commit
   message or PR description for requirement 18's implementation, so a future re-run of this gate has
   a timestamped trail — same convention already established by
   `implementations/20260718-094534_requirement_17_disabled_reason_landing_check.md` step 4.

### Method

Manual grep + conditional branch, run twice (once before writing assertions, once before declaring
the plan fully done) — not automatable as a CI gate, since "requirement 14/15 landed" is a
cross-plan state with no automated tracking beyond grepping for the field names.

### Details

No pseudocode needed — purely a procedural check. The two possible outcomes and their concrete
actions are fully enumerated in Procedure steps 2-4 above. This doc deliberately does not restate
the two dependency plans' own field-shape details (field names, exact `disabled_reason` string
values) — see `implementations/20260718-090741_test_mcp_tools_validation.py.md` (requirement 15's own
test-addition doc) for the authoritative exact-string values (`"allowed_dirs is empty"`,
`"allowed_repo_paths is empty"`, `"read_only=true"`) that this plan's own test files should reuse
verbatim once the `xfail` markers come off, to avoid literal-string drift between the two plans'
independently-written tests.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Dependency grep (pre) | `grep -rn "config_dependent\|disabled_reason" scripts/mcp_servers/` | run before writing hard assertions; branch per Procedure steps 2/3 |
| Dependency grep (post) | same command, re-run at plan step 6 | if matches now found, all `xfail` markers removed and suite re-run |
| Residual xfail check | `grep -rn "xfail" tests/test_tool_schema.py tests/test_tools_endpoint.py` | 0 matches once both dependencies have landed and step 6 is complete |
| Regression | `uv run pytest tests/test_tool_schema.py tests/test_tools_endpoint.py -v` | all pass (as hard assertions or as expected `xfail`, per current landing status) |
