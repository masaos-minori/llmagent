# Implementation procedure: `tests/test_tool_approval_risk.py`

Source plan: `plans/20260717-130159_plan.md` (requirement `requires/20260717_07_require.md`),
Implementation step 7 (test-file portion covering the requirement's stated `tests/test_tool_approval.py`).

## Goal

Extend `tests/test_tool_approval_risk.py` — the real file covering `classify_risk()`/
`classify_operation_type()` behavior consumed through the approval flow — with a fail-safe test case
for an unregistered tool (`RiskLevel.HIGH`), and confirm the file's existing GitHub-mutation-set
coverage stays correct once `tool_approval.py`'s `_GITHUB_MUTATION_TOOLS` classification flows through
`RuntimeToolRegistry`-backed `classify_risk()`/`classify_operation_type()` (this plan's steps 2, 6).

## Scope

**In scope**
- `tests/test_tool_approval_risk.py` only: new test case(s) for the unregistered-tool fail-safe path,
  and review of whether any existing assertion in this file becomes stale post-migration.

**Out of scope / naming correction (read this before assuming file identity)**
- This plan's own Assumption 7 states real test-file paths are "`tests/test_tool_policy.py`,
  `tests/test_tool_approval.py`, `tests/test_repository_gateway.py`" and calls this pattern "confirmed
  3 times in this same requirement batch." **Direct investigation for this specific item found this to
  be inaccurate for the approval file**: `tests/test_tool_approval.py` **does not exist**.
  `tool_approval.py`'s test coverage is split across four real files:
  `tests/test_tool_approval_paths.py`, `tests/test_tool_approval_risk.py`,
  `tests/test_tool_approval_preflight.py`, `tests/test_tool_approval_repos.py`. Per this workflow's
  filename-match rule against `implementations/` and `implementations/done/`, three of the four already
  have implementation docs (`done/20260626-103315_test_tool_approval_paths.py.md`,
  `done/20260715-154002_test_tool_approval_preflight.py.md`,
  `done/20260715-154002_test_tool_approval_repos.py.md`); **`test_tool_approval_risk.py` has no
  existing doc** and is the one that actually covers this plan's subject matter (risk/operation-type
  classification), so it was selected as the concrete target for this plan's `tests/test_tool_approval.py`
  step instead of guessing at a file that isn't there. This substitution is noted here explicitly per
  this workflow's "if ambiguous, report rather than guess" instruction — it should be treated as a
  correction to the plan's Assumption 7, not a silent reinterpretation.
- `scripts/agent/tool_approval.py` itself — filename-matched to existing docs
  (`implementations/done/20260715-154002_tool_approval.py.md` and two earlier ones) and therefore
  skipped as already covered by this workflow's rule. Not re-verified against this plan's specific
  ask (same caveat as the paired `tool_policy.py` doc,
  `implementations/20260717-220433_test_tool_policy.py.md` — flag for human review, not re-implemented
  here).
- `_GITOPS_BLOCKABLE_TOOLS`/`gitops_push_blocked` gating (`tool_approval.py:46, 118`) — confirmed by
  direct read to be a distinct feature from risk classification (blocks GitHub pushes/PR mutations
  outright when a config flag is set, independent of risk tier); this resolves this plan's Unknown #2
  ("does `_GITHUB_MUTATION_TOOLS` serve a purpose beyond risk classification?") — **yes, it does** — so
  `tool_approval.py`'s own `_GITHUB_MUTATION_TOOLS` construction (line 41) should be *kept*, not
  removed, when `tool_approval.py` is actually migrated; it is out of scope for this test-file doc,
  which only needs to confirm no existing test asserts on its removal.

## Assumptions

1. Current file structure (confirmed by direct read, `tests/test_tool_approval_risk.py:1-353`):
   `_make_cfg(**overrides)` (21-90) and `_make_ctx(cfg=None)` (93-102) helpers; test classes
   `TestMakeCfgDefaults` (105-116), `TestClassifyRisk` (122-238, uses `_classify_risk` aliased from
   `agent.tool_policy.classify_risk`), `TestBuildPreview` (243-287), `TestClassifyOperationType`
   (292-353, uses `agent.tool_policy.classify_operation_type` imported locally inside each test method).
2. `TestClassifyRisk::test_truly_unknown_tool_returns_medium_fail_safe` (current lines 142-146) asserts
   `_classify_risk(cfg, "some_unregistered_tool", {}) == "medium"`, with an explicit comment: "Tool
   absent from both approval_risk_rules and tool_safety_tiers → Fail-Safe: WRITE_DANGEROUS default →
   'medium'". This is the **same staleness issue** flagged in the paired `test_tool_policy.py` doc
   (`implementations/20260717-220433_test_tool_policy.py.md`, Assumption 2): this plan's acceptance
   criterion for a fully-unregistered tool is `RiskLevel.HIGH`, not `MEDIUM`. This existing test's name,
   comment, and assertion must all be updated together once the migration lands, not left as a
   contradicting "fail-safe" test with a stale expected value.
3. `TestClassifyRisk::test_empty_risk_rules_falls_back_to_tier` (222-226) and
   `test_empty_risk_rules_read_only_still_none` (228-231) test a **registered** tool (`delete_file`,
   `list_directory`) with `approval_risk_rules` explicitly emptied but `tool_safety_tiers` still
   populated by `_make_cfg`'s defaults (lines 60-86) — these are unaffected by the unregistered-tool
   fail-safe change and do not need updating.
4. `OperationType.UNKNOWN` (paired doc `implementations/20260717-220404_tool_enums.py.md`) is available
   for import once that enum change lands; this file's `TestClassifyOperationType` class (292-353)
   currently compares against plain strings (e.g. `== "execute"`, `== "api_write"`) rather than enum
   members — new unknown-tool test cases should follow the same plain-string comparison style used
   throughout this file's `TestClassifyOperationType` for consistency (`== "unknown"`), even though
   `tests/test_tool_policy.py`'s equivalent class imports and compares against the `OperationType` enum
   directly — both styles are valid since `OperationType` is a `StrEnum`; match each file's existing
   convention rather than unifying style across files as an unrelated drive-by change.

## Implementation

### Target file

`tests/test_tool_approval_risk.py`

### Procedure

1. In `TestClassifyRisk` (current lines 122-238), **update**
   `test_truly_unknown_tool_returns_medium_fail_safe` (142-146): rename to
   `test_truly_unknown_tool_returns_high_risk_fail_safe`, change the asserted value from `"medium"` to
   `"high"`, and update the inline comment to state the new fail-safe target
   (`RuntimeToolRegistry`-unregistered + `OperationType.UNKNOWN` → `RiskLevel.HIGH`) instead of the old
   "`WRITE_DANGEROUS` default → medium" rationale.
2. Add one new test to `TestClassifyRisk` confirming the high-risk fail-safe is not silently escalatable
   downward: `test_unregistered_tool_high_risk_survives_no_special_case` — call `_classify_risk` with an
   unregistered tool name and empty args, assert `"high"`, mirroring the existing style of this class
   (no new class needed; this is the same functional area as the existing tests).
3. In `TestClassifyOperationType` (current lines 292-353), add
   `test_unregistered_tool_returns_unknown` following the existing per-method local-import style
   (`from agent.tool_policy import classify_operation_type as _classify_operation_type`), asserting
   `_classify_operation_type("totally_unregistered_tool_xyz") == "unknown"`.
4. Do not touch `TestMakeCfgDefaults`, `TestBuildPreview`, or the rest of `TestClassifyRisk`/
   `TestClassifyOperationType` — those cover registered-tool behavior unaffected by this plan's
   unregistered-tool fail-safe change.

### Method

Plain pytest function-based test methods, matching each existing class's own style (module-level
aliasing for `TestClassifyRisk`, per-method local import for `TestClassifyOperationType`) — do not
unify the two import styles as part of this change.

### Details

Pseudocode sketch (no production code, illustrative only):

```
class TestClassifyRisk:
    def test_truly_unknown_tool_returns_high_risk_fail_safe(self) -> None:
        # Tool absent from RuntimeToolRegistry, approval_risk_rules, and tool_safety_tiers
        # -> OperationType.UNKNOWN -> RiskLevel.HIGH (fail-safe; was "medium" pre-migration)
        cfg = _make_cfg()
        assert _classify_risk(cfg, "some_unregistered_tool", {}) == "high"

    def test_unregistered_tool_high_risk_survives_no_special_case(self) -> None:
        cfg = _make_cfg()
        assert _classify_risk(cfg, "totally_unregistered_tool_xyz", {}) == "high"


class TestClassifyOperationType:
    def test_unregistered_tool_returns_unknown(self) -> None:
        from agent.tool_policy import classify_operation_type as _classify_operation_type
        assert _classify_operation_type("totally_unregistered_tool_xyz") == "unknown"
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Targeted tests | `uv run pytest tests/test_tool_approval_risk.py -v` | all pass, including the renamed/updated fail-safe test and the two new unregistered-tool cases |
| Related approval tests | `uv run pytest tests/test_tool_approval_paths.py tests/test_tool_approval_preflight.py tests/test_tool_approval_repos.py -v` | unaffected — confirm no cross-file assumption about `_GITHUB_MUTATION_TOOLS`/`_GITOPS_BLOCKABLE_TOOLS` regresses |
| Format/lint | `uv run ruff format tests/test_tool_approval_risk.py && uv run ruff check tests/test_tool_approval_risk.py` | 0 errors |
| Type check | `uv run mypy tests/test_tool_approval_risk.py` | 0 errors |
| Full suite | `uv run pytest -v` | no new failures elsewhere |
| Precondition gate | manual review | confirm `scripts/agent/tool_policy.py` (consulted here via `classify_risk`/`classify_operation_type`) has actually been migrated to `RuntimeToolRegistry`-backed classification before expecting the updated/new cases to pass — same caveat as the paired `test_tool_policy.py` doc |
