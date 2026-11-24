## Goal
Make GitHub configuration parsing strict and fail-fast: strict booleans, positive pagination limits,
NaN/infinity rejection, and canonical/deduplicated `allowed_repos` entries rejected at startup when
malformed (REQ-006 shared strict config helpers; REQ-007 shared `owner/repo` identity).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/mcp_servers/github/github_models_config.py` (Plan Phase 7), plus two existing
  tests the new parsing invalidates (Step 3a findings, see Compatibility).
- `scripts/mcp_servers/github/github_service_security.py` is a reference, not a target: its
  `_clamp_per_page`, non-canonical-allowlist branch, and `server.per_page_bounds` posture check stay
  in place as defense-in-depth.

## Assumptions
- `shared.config_utils.get_typed` and `get_non_negative_number` are the helpers to reuse;
  `get_non_negative_number` rejects bools, NaN, infinity, and negatives but **accepts 0** as the
  documented "no limit" convention (`scripts/shared/config_utils.py:105-133`).
- `0 = disabled/unlimited` is the existing meaning of `max_file_size_kb` (`github_service_security.py:118-119`)
  and `max_file_read_size_kb` (`config/github_mcp_server.toml` comment "0 = unlimited"), so only the
  two pagination keys need a GitHub-specific `> 0` rule.
- `default_per_page` is absent from `config/github_mcp_server.toml`, so the `> 0` and ordering rules
  must hold for the `DEFAULT_PER_PAGE = 10` default (line 24).
- Runtime allowlist comparison (`_assert_allowed_repo`, `github_service_security.py:89-95`) already
  uses `shared.repo_identity.normalize_repo_key`.

## Design decisions
- Booleans switch from `bool(d.get(...))` (lines 66-67, which accepts the strings `"false"` and
  `"0"` as `True`) to `get_typed(d, key, bool, "a boolean", default=...)`, matching how
  `allow_global_search` (68-70) is already read.
- Pagination limits become `get_non_negative_number(...)` (rejects NaN/infinity/negatives/bools), and
  `load` adds the GitHub-specific rule `value > 0` for `default_per_page` and `max_per_page` plus
  `default_per_page <= max_per_page`; the check is raised as `ValueError` from `load` in the same
  style as the existing `protected_branches` rule (lines 90-93), while `from_dict` stays usable for
  unit tests (documented in its docstring, which already states that an empty list stays valid for
  unit tests).
- `allowed_repos` handling: `from_dict` canonicalizes each `owner/repo` entry with
  `shared.repo_identity.normalize_repo_key` and deduplicates it deterministically
  (`sorted(set(...))`); `load` rejects entries whose shape is malformed (not a string, not exactly one
  `/`, or an empty part) with a `ValueError` naming them. Malformed entries currently reach runtime
  and fail per call (`github_service_security.py:89-95`); after this row they never start the server.
- The runtime non-canonical branch and the `server.per_page_bounds` posture check are kept: startup
  rejection is an earlier gate, not a replacement (that file is not in the frozen table).

## Alternatives considered
- Rejecting malformed `allowed_repos` entries inside `from_dict`: rejected — `from_dict` is the
  documented test seam for synthetic configs (its own docstring), and the Plan Design places shape
  rejection in `load` next to the existing `protected_branches` fail-fast rule.
- Keeping `bool(d.get(...))` and validating afterwards: rejected — the coercion is the defect
  (`"false"` -> `True`), and REQ-006 names `get_typed(..., bool, ...)` explicitly.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_config.py`

### Procedure
1. Add `from shared.repo_identity import normalize_repo_key` to the import block.
2. `allow_force_push` (66) and `require_pr_review` (67): `get_typed(d, key, bool, "a boolean",
   default=False / True)`.
3. `max_file_size_kb` (59-61) and `max_file_read_size_kb` (62-64): both via
   `get_non_negative_number(d, key, int, "an integer", default=0)`.
4. `default_per_page` (71-73) and `max_per_page` (74): `get_non_negative_number(...)` with the same
   defaults (`DEFAULT_PER_PAGE`, `100`).
5. `allowed_repos` (50-52): map each entry through `normalize_repo_key(*entry.split("/"))` when the
   entry is a string containing exactly one `/`; keep non-string entries unchanged so `load` can
   report them rather than `from_dict` crashing on them.
6. In `load` (79-94), after the existing `protected_branches` rule, add three fail-fast checks that
   raise `ValueError` naming the offending key or entries: `default_per_page > 0 and max_per_page > 0`;
   `default_per_page <= max_per_page`; every `allowed_repos` entry canonical (`is_canonical_repo_key`).
7. Update the `load` docstring to state the new startup rules alongside the existing ADR-004 rule.

### Method
- `from_dict` parses and normalizes; `load` decides whether the parsed config may start the server.
- Canonicalization uses the shared helper rather than a local `lower()` so the config, the guard, the
  API slug, and the audit record keep naming one identity (REQ-007).

### Details
- `is_canonical_repo_key` (used by the `load` check) already encodes the policy: exactly one
  separator, both parts non-empty, no upper-case characters.
- Dedup must be order-independent: `sorted(set(...))`, so the same set of entries always yields the
  same list (T-04 asserts determinism).

### Companion test files
- `tests/mcp_servers/github/test_github_config_strict_parsing.py` (new)
  - Procedure: T-04 cases — `allow_force_push = "false"` and `require_pr_review = "0"` rejected;
    `max_per_page`/`default_per_page` of `0`, `-1`, `float("nan")`, `float("inf")` rejected at `load`;
    `default_per_page > max_per_page` rejected; `allowed_repos` entries `"owner/"`, `"/repo"`,
    `"a/b/c"`, `123` rejected at `load`; `"Owner/Repo"` and `"owner/repo"` normalize to one canonical
    entry in sorted order.
  - Validation: `uv run pytest tests/mcp_servers/github/test_github_config_strict_parsing.py` (T-04).

## Compatibility considerations
- Behavior change to record in seq 19: a `github-mcp` process that today starts with a reversed
  `default_per_page`/`max_per_page` pair (reported only by the `server.per_page_bounds` posture check,
  `github_service_security.py:501-513`) now refuses to start.
- Behavior change: `allowed_repos` entries that previously produced a per-call
  `GitHubAuthorizationError` now stop startup. Existing `config/github_mcp_server.toml`
  (`allowed_repos = ["masaos-minori/llmagent"]`, `max_per_page = 100`, no `default_per_page` key,
  `max_file_read_size_kb = 0`) satisfies every new rule.
- Tests that build `GitHubConfig(...)` directly (`tests/mcp_servers/github/test_github_security_validation.py`,
  `test_github_health_posture.py`) bypass `from_dict`/`load` and are unaffected.
- Deployment restart is required for the new startup rules to take effect (Plan Phase 8 hand-off;
  user approval gate).
- Step 3a findings (two existing tests invalidated by the new parsing, both adjusted in this row):
  - `tests/mcp_servers/github/test_github_mcp_service.py::test_negative_max_disables_check` asserted a
    negative `max_file_size_kb` was accepted and disabled the size guard. `get_non_negative_number`
    rejects negatives at parse time, so the case is now `test_negative_max_is_rejected_at_parse_time`;
    `0` remains the documented "no limit" value and its test is unchanged.
  - `tests/mcp_servers/github/test_service_security.py::TestGetRepoBoundary::test_non_canonical_allowlist_entry_is_reported_instead_of_never_matching`
    built the non-canonical entry through `from_dict`, which now canonicalizes it, so the runtime guard
    never saw it. The test now constructs `GitHubConfig(allowed_repos=["Org/Repo"])` directly, which
    keeps the runtime non-canonical branch covered as the defense-in-depth gate this row keeps.
- Implementation note (procedure step 5): the dedup is implemented as a module-level
  `_normalize_allowed_repos()` helper rather than a literal `sorted(set(...))`, because a plain
  `sorted(set(...))` raises `TypeError` when a config mixes strings with non-strings (`123`), which the
  same step requires `from_dict` to survive. Canonicalizable entries are lower-cased, deduplicated and
  sorted; malformed entries are kept unchanged in input order so `load` can name them.

## Security considerations
- Startup rejection turns silently weak postures (reversed pagination bounds, unmatchable allowlist
  entries, `"false"`-as-true booleans) into a failure to start, consistent with the ADR-004 fail-closed
  stance already documented in `load`.

## Rollback considerations
- Revert this Phase 7 commit: `from_dict`/`load` return to permissive parsing; no data is migrated.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_config_strict_parsing.py` (T-04, companion).
- `uv run pytest tests/mcp_servers/github/test_github_mcp_service.py` (the existing `from_dict` tests at
  `tests/mcp_servers/github/test_github_mcp_service.py:863-881` pass only well-typed values and must
  keep passing).
- `uv run pytest tests/mcp_servers/github/test_github_security_validation.py tests/mcp_servers/github/test_github_health_posture.py`.
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/github/ -c pyproject.toml`,
  `uv run lint-imports` (T-06).

## Completion criteria
- `GitHubConfig.from_dict({"allow_force_push": "false", ...})` raises; `load` raises for each malformed
  case listed in the companion test procedure.
- `load()` on the shipped `config/github_mcp_server.toml` still succeeds (regression check).
- `allowed_repos` in a loaded config is canonical and sorted with duplicates removed.

## Out of Scope
- `github_service_security.py` posture checks and `_clamp_per_page` (unchanged), docs row (seq 19),
  config file content changes (none required by this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Switch booleans, size keys, and pagination keys to the strict shared helpers | Completed | 20261124-213502 | 20261124-213502 | REQ-006 Changed: scripts/mcp_servers/github/github_models_config.py, tests/mcp_servers/github/test_github_mcp_service.py, tests/mcp_servers/github/test_service_security.py. |
| 2 | Canonicalize/deduplicate `allowed_repos` in `from_dict` | Completed | 20261124-213502 | 20261124-213502 | REQ-007 _normalize_allowed_repos(): normalize_repo_key + dedup, sorted canonical + malformed in input order. |
| 3 | Add the three `load` fail-fast rules and update its docstring | Completed | 20261124-213502 | 20261124-213502 | REQ-006, REQ-007 Three load rules added after the protected_branches rule; load docstring states them. |
| 4 | Add companion tests `tests/mcp_servers/github/test_github_config_strict_parsing.py` (T-04) | Completed | 20261124-213502 | 20261124-213502 | tests/mcp_servers/github/test_github_config_strict_parsing.py: 38 T-04 cases, incl. the shipped-config load regression. |
| 5 | Run the validation sequence (`rules/toolchain.md`) for this file | Completed | 20261124-225226 | 20261124-225226 | ruff format/check, mypy pass; tests/mcp_servers/github/ = 396 passed. bandit/lint-imports/module-size and the full-suite run are the end-of-batch run. End-of-batch run (rules/toolchain.md, Batch mode): full pytest 13959 passed / 5 skipped / 6 errors; all 6 errors are the pre-existing tests/tools/test_append_plan_work_items.py contract mismatch (issues/20261124-155017_qa001_append-plan-attr-mismatch.md), none in this batch's files. ruff format+check, mypy, lint-imports, check_module_size, bandit, check_docstrings (after adding the em-dash separator to scripts/mcp_servers/request_contract.py), and diff-cover --fail-under 90 Pass. pre-commit run --all-files fails only on 14 pre-existing procedure-length findings in implementations/20261124-122732_* (issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md); check_workitem_structure --file on this batch's documents reports no findings. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006` (strict shared config helpers), `REQ-007` (canonical `allowed_repos` identity and deterministic dedup)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/github_models_config.py`, `tests/mcp_servers/github/test_github_config_strict_parsing.py`