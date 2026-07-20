# Implementation procedure: `tests/test_tool_safety_tiers.py` (new — safety-tier coverage test)

Source plan: `plans/20260719-202346_plan.md`, Implementation step Phase 3 / Design §4.

No prior implementation doc exists for this exact filename (`grep -rl`/`ls | grep -F` over
`implementations/` and `implementations/done/` returns no hits). This is a new document.

**Important grounding note found during investigation**: the underlying check logic this file
needs already exists and is already partially tested elsewhere, under different file names. This
changes the Method below from "write assertions from scratch" to "call existing functions against
the real config."

## Goal

Add `tests/test_tool_safety_tiers.py` verifying every tool registered in `ToolRegistry` (populated
from `tool_constants.py`'s frozensets, `search_web` included) has a `[tool_safety_tiers]` entry in
`config/agent.toml`, and that no `[tool_safety_tiers]` entry references an unknown tool name —
exercised against the **real** `config/agent.toml`, not a synthetic stub.

## Scope

**In scope**
- New test module `tests/test_tool_safety_tiers.py`.
- Assertions using the *real* `config/agent.toml` file (not a mock), calling the existing
  `shared.tool_routing_validation.check_tool_safety_tiers()` and
  `check_unknown_tool_safety_tiers()` functions (verified present, `tool_routing_validation.py`
  lines 86-121) against the real registry and the real `[tool_safety_tiers]` table.
- An explicit, named assertion that `search_web` specifically resolves to `"READ_ONLY"` (per
  Design §4's stated requirement), not just that the tier-coverage check passes generically.

**Out of scope**
- Re-implementing the missing/unknown-tier detection logic — that already exists in
  `shared/tool_routing_validation.py` (`check_tool_safety_tiers`, `check_unknown_tool_safety_tiers`);
  this new file's job is to call those functions with the *real* config, which no existing test
  currently does (see Assumption 1).
- Modifying `shared/tool_routing_validation.py`, `shared/tool_registry.py`, or `config/agent.toml`'s
  `[tool_safety_tiers]` table itself — this is a test-only addition; if the real-config assertions
  fail, that is a separate finding to report, not something this test file fixes.

## Assumptions

1. **Existing coverage is generic/synthetic only — real-config coverage is the actual gap.**
   Verified via `grep -rln "check_tool_safety_tiers\|check_unknown_tool_safety_tiers"  tests/`:
   only `tests/test_startup_routing_drift.py` exercises these two functions today, and its tests
   (`test_safety_tiers_missing_tools_reported`, `test_safety_tiers_all_present_returns_empty`,
   `test_safety_tiers_empty_config_skips_check`, verified at lines 72-95) all use synthetic/stub
   registries and hand-built `tool_safety_tiers` dicts — none loads the real
   `config/agent.toml` `[tool_safety_tiers]` table. `tests/test_tool_registry.py`'s
   `TestValidateRoutingAgainstRealConfig` class (lines 300-334, verified) loads the real
   `config/agent.toml` but only exercises `validate_routing_against_config()` (tool_names drift),
   not the safety-tier functions. This new file closes that specific gap: real config +
   safety-tier check, matching the pattern `TestValidateRoutingAgainstRealConfig` already
   established for the tool_names drift check.
2. `config/agent.toml`'s `[tool_safety_tiers]` table starts at line 209 (verified via
   `grep -n "^\[tool_safety_tiers\]" config/agent.toml`) and includes
   `search_web               = "READ_ONLY"` at line 222 (verified) — this is the concrete value
   the named `search_web` assertion checks against.
3. `check_tool_safety_tiers()`'s signature (verified, lines 86-108) accepts an optional `registry`
   (defaults to `get_registry()`) and a `tool_safety_tiers: dict[str, str] | None` — the real dict
   must be parsed out of `config/agent.toml`'s `[tool_safety_tiers]` TOML table via `tomllib`,
   matching the pattern already used in `tests/test_tool_registry.py`'s real-config class.
4. Both `check_tool_safety_tiers()` and `check_unknown_tool_safety_tiers()` return `[]` on success
   (list of warning-message strings on failure) — the new test asserts an empty list for the real
   config in both directions (no registered tool missing a tier; no tier entry naming an unregistered
   tool).

## Implementation

### Target file

`tests/test_tool_safety_tiers.py` (new — verified via `find . -name "test_tool_safety_tiers.py"`
returning no results).

Related existing files this test imports from:
- `scripts/shared/tool_routing_validation.py` — `check_tool_safety_tiers`,
  `check_unknown_tool_safety_tiers` (lines 86-121, verified).
- `scripts/shared/tool_registry.py` — `get_registry()` (used by the checked functions' default
  path, and directly by this test to derive the full tool-name set for the `search_web`-specific
  assertion).
- `config/agent.toml` — real file, `[tool_safety_tiers]` table (line 209 onward).

### Procedure

1. Create the new file with a module docstring describing its purpose (real-config safety-tier
   coverage, complementing `test_startup_routing_drift.py`'s synthetic-registry unit tests).
2. Add a helper that loads `config/agent.toml` via `tomllib` (repo-root-relative path, same pattern
   as `tests/test_tool_registry.py::TestValidateRoutingAgainstRealConfig`) and returns the
   `[tool_safety_tiers]` table as a `dict[str, str]`.
3. Add test cases:
   - `test_no_registered_tool_missing_safety_tier` — `check_tool_safety_tiers(tool_safety_tiers=<real dict>)`
     returns `[]` against the real registry.
   - `test_no_unknown_tool_in_safety_tiers` — `check_unknown_tool_safety_tiers(tool_safety_tiers=<real dict>)`
     returns `[]` against the real registry.
   - `test_search_web_is_read_only` — explicit named assertion:
     `<real dict>["search_web"] == "READ_ONLY"` (per Design §4's stated requirement to check
     `search_web` specifically, not just the generic coverage check).

### Method

Pseudocode only (per `skills/python-design/SKILL.md` — no production code blocks):

```
"""tests/test_tool_safety_tiers.py
Safety-tier coverage tests against the real config/agent.toml [tool_safety_tiers]
table, complementing test_startup_routing_drift.py's synthetic-registry unit tests."""

import tomllib
from pathlib import Path

from shared.tool_routing_validation import (
    check_tool_safety_tiers,
    check_unknown_tool_safety_tiers,
)


def _real_tool_safety_tiers() -> dict[str, str]:
    path = Path(__file__).parent.parent / "config" / "agent.toml"
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    return cfg["tool_safety_tiers"]


class TestRealAgentTomlSafetyTiers:
    def test_no_registered_tool_missing_safety_tier(self) -> None:
        msgs = check_tool_safety_tiers(tool_safety_tiers=_real_tool_safety_tiers())
        assert msgs == []

    def test_no_unknown_tool_in_safety_tiers(self) -> None:
        msgs = check_unknown_tool_safety_tiers(tool_safety_tiers=_real_tool_safety_tiers())
        assert msgs == []

    def test_search_web_is_read_only(self) -> None:
        assert _real_tool_safety_tiers()["search_web"] == "READ_ONLY"
```

### Details

- Deliberately does not duplicate `test_startup_routing_drift.py`'s synthetic-stub test cases
  (missing-tool-reported, all-present-empty, empty-config-skips) — those already prove the
  function's *logic* is correct in isolation; this new file's job is proving the *real config*
  currently satisfies that logic, which is a distinct, previously-untested claim.
- If either real-config assertion (`test_no_registered_tool_missing_safety_tier` or
  `test_no_unknown_tool_in_safety_tiers`) fails at implementation time, that is a genuine finding
  about `config/agent.toml`'s current state, not a bug in this test — report it rather than
  loosening the assertion.
- No production code or config is modified by this item; purely additive test file.

## Validation plan

| Check | Command | Target |
|---|---|---|
| New test | `uv run pytest tests/test_tool_safety_tiers.py -v` | all 3 cases pass against real `config/agent.toml` |
| Format/lint | `uv run ruff format tests/ && uv run ruff check tests/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Regression | `uv run pytest tests/test_startup_routing_drift.py tests/test_tool_registry.py -v` | no regressions |
| Full suite | `uv run pytest -v` | no new failures |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥ 90% on changed lines |
