# test_get_cfg_error_path failure: fallback RAG config defaults conflict with its own validation

## Priority
High

## Summary
`tests/agent/test_rag_get_cfg.py::TestRagPipelineGetCfg::test_get_cfg_error_path`
expects `resolve_rag_config` to fall back to an empty `RagConfigImpl` (with
`llm_url == ""`, `embed_url == ""`) when the config loader raises. Instead it
raises `ValueError: RAG config requires non-empty llm_url, embed_url when
use_search=True`, because `scripts/rag/config_resolution.py`'s own
`_DEFAULTS_FOR_ALL` sets `use_search: True` by default while leaving
`llm_url`/`embed_url` empty — the fallback defaults self-contradict the
validation the same function applies right after.

## Background
`resolve_rag_config` (`scripts/rag/config_resolution.py`) has a fallback path:
if no config is loadable (missing file, or the given `config_loader` raises
`FileNotFoundError`/`ValueError`), it fills in `_ALL_FIELDS` from
`_DEFAULTS_FOR_ALL` and proceeds to validate. `_DEFAULTS_FOR_ALL["use_search"]`
is `True`, but `llm_url`/`embed_url` are not given non-empty defaults, so the
subsequent "critical fields required when `use_search=True`" check
(lines ~146-155) always fires for the pure-fallback case.

## Problem
Confirmed by direct reproduction
(`uv run pytest tests/agent/test_rag_get_cfg.py::TestRagPipelineGetCfg::test_get_cfg_error_path -v`):
```
scripts/rag/config_resolution.py:155: in resolve_rag_config
    raise ValueError(
E   ValueError: RAG config requires non-empty llm_url, embed_url when use_search=True
```
The test passes a `config_loader` that always raises `ValueError("no file")`,
expecting the function to swallow that and return a safe, disabled-search
config. Reading `scripts/rag/config_resolution.py` directly confirms the
fallback path (`_raw_cfg = {}` then filled from `_DEFAULTS_FOR_ALL`) always
produces `use_search=True` with empty `llm_url`/`embed_url`, which the
validation added later in the same function (lines ~146-155) then rejects.
Either the fallback defaults or the test's expectation is wrong; this issue
does not itself determine which.

## Reason for Change
Uncovered via a full `uv run pytest tests/` run while syncing to
`origin/master` via the `git-commit-and-sync` skill. This is a config
fallback path meant to keep the agent usable when RAG configuration is
unavailable — if it now always raises instead of degrading gracefully, that
is a behavior regression for a genuinely no-file/misconfigured deployment,
not just a test-only issue.

## Implementation Intent
Resolve the self-contradiction in `scripts/rag/config_resolution.py`. Two
plausible directions (pick whichever matches the intended fallback
contract):
- **Fix the defaults**: change `_DEFAULTS_FOR_ALL["use_search"]` to `False`
  (search-disabled) for the no-config-available fallback case, so the
  "non-empty when use_search=True" validation is naturally satisfied by
  falling back to search-disabled instead of raising.
- **Fix the test**: if raising is the intended, newer behavior (fail loudly
  rather than silently run with search disabled when config is broken),
  update `test_get_cfg_error_path` to assert the `ValueError` is raised
  instead of asserting a fallback `RagConfigImpl`.
Do not pick between these without confirming which matches the surrounding
system's operational expectations (e.g. does anything currently rely on
`resolve_rag_config` never raising during startup?) — see Unresolved
Questions.

## Target Files or Areas
- `scripts/rag/config_resolution.py` (`_DEFAULTS_FOR_ALL`, `resolve_rag_config`)
- `tests/agent/test_rag_get_cfg.py` (`test_get_cfg_error_path`)

## Required Changes
- Decide and implement one of the two directions in Implementation Intent.
- If defaults change: re-run the full `test_rag_get_cfg.py` file and
  `tests/rag/` to confirm no other test relies on `use_search=True` being the
  fallback default.
- If the test changes: update its assertions and docstring to describe the
  new expected (raising) behavior, and check whether any caller of
  `resolve_rag_config` needs a try/except added around it if it can now
  raise where it previously didn't (or already handled that — verify).

## Constraints
Whichever direction is chosen, do not leave the current
self-contradictory state (defaults that always trip their own immediately-
following validation) — that is the actual bug regardless of which side is
"correct."

## Acceptance Criteria
- [ ] `uv run pytest tests/agent/test_rag_get_cfg.py -v` passes
- [ ] `uv run pytest tests/rag/ -q` shows no new regressions
- [ ] The chosen behavior (silent fallback vs. explicit raise) is consistent
  between `_DEFAULTS_FOR_ALL` and the validation logic in
  `resolve_rag_config`, and documented in the docstring/comment for
  `resolve_rag_config` if not already clear

## Testing Expectations
`uv run pytest tests/agent/test_rag_get_cfg.py -v` (targeted), plus
`uv run pytest tests/rag/ -q` for a regression check across the RAG suite,
and a check of any startup code path that calls `resolve_rag_config` without
a surrounding try/except if the raise-based direction is chosen.

## Documentation Impact
If the raise-based direction is chosen: check `docs/05_agent/*.md` and any
RAG-related startup docs for whether they describe `resolve_rag_config` as
non-raising/always-safe, and correct that description per
`rules/coding.md`'s "Documentation notes — Current behavior classification"
(likely "Implementation fix required" or "Documentation fix required"
depending on which side changes).

## Out of Scope
- Do not investigate or fix any other file's test failures (filed
  separately: eventbus issues, orchestrator integration issue).
- Do not change `RagConfigValidator`'s general validation rules beyond the
  specific `use_search`/`llm_url`/`embed_url` interaction described here.

## Dependencies
N/A: none

## Unresolved Questions
- Which behavior is actually intended for a missing/unreadable RAG config at
  startup: silently disable search (test's current expectation) or fail
  loudly (current implementation's actual behavior)? This needs a decision
  from whoever owns the RAG startup/config-resolution contract before
  Required Changes can proceed — this issue intentionally does not decide it.

## AI Implementation Instruction
Do not silently pick a direction — if the deciding context (Unresolved
Questions) isn't available, stop and ask rather than guessing which side is
"correct." Whichever direction is confirmed, make the minimal change to
remove the self-contradiction; do not rewrite `resolve_rag_config`'s broader
validation logic beyond what's needed here.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260917-111003
- **Related target files**: scripts/rag/config_resolution.py, tests/agent/test_rag_get_cfg.py
