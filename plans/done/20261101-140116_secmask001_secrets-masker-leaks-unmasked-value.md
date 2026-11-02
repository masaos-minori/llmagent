## Goal
- Extend the secrets masker so that unquoted and quoted colon-separated `key: value` secrets (YAML or log style) for the existing key names are masked like their `key=value` forms, and record an explicit, tested decision for whitespace-containing and multi-line values, without changing the `_mask_secrets(text: str) -> str` signature or any call site.

## Priority
Medium

## Scope
- **In-Scope**:
  - New `SECRET_PATTERNS` coverage for `key: value` and `key: "value"` / `key: 'value'` for the existing key names (password, passwd, pwd, api_key / api-key / apikey, secret, token).
  - A decision and implementation (or a recorded decision to leave out) for values that contain whitespace and for multi-line values.
  - Tests for the new forms, the regression forms, and a no-false-positive case; updating the one existing test that pins the pattern count.
  - Updating the operator-facing description of the masker's shapes (it exists and becomes stale; see Documentation Impact).
- **Out-of-Scope**:
  - `scripts/agent/diagnostic_store.py`'s own secret-detection regex (tracked by `issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md`).
  - `scripts/agent/tool_result_formatter.py::mask_args()` key-name-based audit masking (tracked by `issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md`).
  - Any change to the set of sensitive key names beyond adding colon-separated matching for the same keys.
  - Any change to the substitution logic (`m.group(1) + "***MASKED***"`), the function signature, or any call site (`startup_mcp_starter`, `http_lifecycle_errors`, `http_lifecycle_health_checker`, `shared/retry_helper`).
  - The 512-character `stderr_full[-512:]` truncation in `http_lifecycle_errors` that can cut a secret mid-value before masking (not raised by the Issue).
- **Dependencies**: This Plan comes first in its group. `issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md` (consolidating `diagnostic_store.py`'s allowlist with this module's patterns) and `issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md` depend on this Plan landing first; neither is a prerequisite of this Plan. The earlier masker work in `issues/done/` is closed. No sequencing dependency on another active Plan (Step 8b overlap check: see Assumptions).

## Background
`scripts/agent/secrets_masker.py::_mask_secrets()` runs before subprocess stderr and exception text are logged, to keep credentials out of persisted logs. The original truncation leak (`m.group()[:10] + "***MASKED***"`) is already fixed: the substitution keeps the key group and replaces only the value. Earlier masker work: `issues/done/20261004-160514_secmask001_secrets-masker-leaves-short-secret-values-unmasked.md`, `issues/done/20261013-162325_agmask01_*`, `issues/done/20261017-123248_mask01_*`. The residual gap is colon-separated, whitespace-containing and multi-line coverage.

## Problem
Verified by a direct run of the pure-regex module (Step 2): `_mask_secrets("password: hunter2")` and `_mask_secrets("token: abc123")` return the input unchanged; `access_token: abc`, `X-Api-Key: abc`, `api_key: 'abc def'` and `password: "two words"` are also unchanged. `password=two words` becomes `password=***MASKED*** words`, and `password=line1\nline2` becomes `password=***MASKED***\nline2`, because the `key=value` patterns use `(\S+)`. Existing `key=value`, Authorization, Bearer and quoted-JSON-key forms work.

## Reason for Change
Colon-separated forms are common in YAML and log lines, and subprocess stderr tails (which can be multi-line) flow through this masker into persisted logs, so credentials in those forms still reach logs.

## Implementation Intent
Add pattern(s) for colon-separated forms that reuse the existing key-name alternation and the existing group-1 / group-2 substitution, place them so existing patterns (notably `Authorization:` and `Bearer`) still apply to their own shapes, and resolve the whitespace / multi-line question narrowly (see Design and UNK-01).

## Requirements
- `REQ-001`: Unquoted `key: value` for the existing key names is masked (`password: hunter2`, `token: abc123` become `password: ***MASKED***`, `token: ***MASKED***`), case-insensitively, including keys with a prefix such as `access_token` or `X-Api-Key`, matching the way the existing `key=value` patterns already match key suffixes.
- `REQ-002`: Quoted colon form (`key: "value"`, `key: 'value'`) is masked, including a quoted value that contains whitespace (the whole quoted value, no part of it survives).
- `REQ-003`: Record and implement a decision for unquoted values that contain whitespace and for multi-line values (mask to end of line / to a delimiter, or explicitly leave them out with the decision documented in tests and docs), per UNK-01. The existing `key=value` behavior and the capture-group substitution remain unchanged unless the decision explicitly changes the pinned `token=abc def` expectation.
- `REQ-004`: Existing forms keep working: short and long `key=value` values, Authorization header (scheme preserved), standalone Bearer, quoted-JSON-key forms; ordinary text with no secret is returned unchanged (no false positive on the existing non-secret sample).
- `REQ-005`: The signature `_mask_secrets(text: str) -> str`, the substitution logic, and all call sites are unchanged; no new sensitive key names are added.
- `REQ-006`: The operator-facing description of the masker's masked shapes is updated to match the final behavior.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/secrets_masker.py | Extend `SECRET_PATTERNS` with colon-form coverage and the UNK-01 decision | Colon-separated, quoted-colon and (per decision) whitespace / multi-line values are not matched today | REQ-001, REQ-002, REQ-003, REQ-005 / AC-1, AC-2, AC-3, AC-6 | `SECRET_PATTERNS` holds 6 patterns, none with a `:` separator except the quoted-JSON-key and `Authorization:` ones; direct run showed `password: hunter2` and `token: abc123` unchanged (checked in Step 2) | tests/agent/test_secrets_masker.py | Verified |
| tests/agent/test_secrets_masker.py | Add colon / quoted-colon / whitespace / multi-line / regression / no-false-positive tests; update the pattern-count assertion and the whitespace expectation if the decision changes them | `test_pattern_count_grew_by_exactly_one` asserts `len(SECRET_PATTERNS) == 6`, so adding any pattern fails it; `test_masks_secret_values` pins `token=abc def` -> `token=***MASKED*** def` (checked in Step 2) | REQ-001, REQ-002, REQ-003, REQ-004 / AC-1, AC-2, AC-3, AC-4, AC-5 | File exists, classes `TestMaskSecrets` and `TestJsonSecretMasking` (checked in Step 2) | tests/agent/test_secrets_masker.py itself | Verified |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Update the "Secret Masking in MCP Subprocess Failure Reports" section | It states the masker "masks three shapes" (key=value, Authorization, standalone Bearer) and omits the quoted-JSON shape already added; it will be stale after this change (checked in Step 2) | REQ-006 / AC-7 | Section heading "Secret Masking in MCP Subprocess Failure Reports" exists in the file (checked in Step 2); the Issue's "no documentation describes the masker" claim is wrong | N/A: documentation (run the docs checkers named in the Validation plan) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/startup_mcp_starter.py | Call site: masks `str(e)` before logging the first-attempt failure; must stay unchanged | REQ-005 |
| scripts/agent/http_lifecycle_errors.py | Call site: masks `stderr_full[-512:]` (can be multi-line) in `HttpStartupError.__str__` | REQ-003, REQ-005 |
| scripts/agent/http_lifecycle_health_checker.py | Call site: masks `stderr_full[:500]` in the early-exit log | REQ-005 |
| scripts/agent/shared/retry_helper.py | Call site: wrapper `_mask_secrets` delegating to the masker; masks the already-masked message a second time, so masking must be idempotent on `***MASKED***` | REQ-004, REQ-005 |
| tests/agent/test_http_lifecycle_command_validator.py | Call-site test `test_masked_secrets_in_stderr` (`password=secret123\napi_key=abc123`) must still pass | REQ-004 |
| docs/00_index.md | "Document References by Task" routing for the docs row and the docs checkers | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001): `password: hunter2` and `token: abc123` are masked like their `key=value` forms; `access_token: abc` and `X-Api-Key: abc` are masked; none of the secret value characters appear in the output.
- AC-2 (REQ-002): `api_key: 'abc def'` and `password: "two words"` are masked in full.
- AC-3 (REQ-003): the UNK-01 decision is implemented and pinned by tests for an unquoted whitespace value and a multi-line value; no value matched by a `SECRET_PATTERNS` pattern appears, in whole or in part, in the output.
- AC-4 (REQ-004): all pre-existing tests in the masker test module still pass, apart from the pattern-count assertion and (only if the decision requires it) the `token=abc def` expectation, both updated in the same change; `Authorization: Bearer <t>` keeps the scheme and masks the token, and `token: Bearer <t>` leaves no part of `<t>` in the output.
- AC-5 (REQ-004): ordinary text with no secret (the existing non-secret stderr sample, plus prose such as a log line with no known key) is returned unchanged; applying `_mask_secrets` twice equals applying it once.
- AC-6 (REQ-005): `git diff` shows the `_mask_secrets` body, signature and all four call-site modules unchanged and no new key names.
- AC-7 (REQ-006): the docs section lists the final masked shapes accurately and passes the docs checkers.

## Tests
- Unit tests in `tests/agent/test_secrets_masker.py` (REQ-001): parametrized unquoted colon forms across all key names, case variants and prefixed keys.
- Unit tests (REQ-002): quoted colon forms with single and double quotes and a whitespace-containing quoted value.
- Unit tests (REQ-003): unquoted whitespace value and multi-line value per the UNK-01 decision.
- Regression tests (REQ-004): the existing short / long `key=value`, Authorization, Bearer and JSON cases; no-false-positive sample; ordering case `token: Bearer abc`; idempotence.
- Call-site regression (REQ-004): `tests/agent/test_http_lifecycle_command_validator.py`, `tests/agent/test_startup_mcp_starter.py`, `tests/agent/test_http_lifecycle*.py` run unchanged.

## Documentation Impact
Required (REQ-006): `docs/*.md` describes the masker's shapes today (the Issue's "N/A" claim is incorrect). Update the target doc listed in `Implementation Target Files` (reached via `docs/00_index.md` "Document References by Task", Agent row) so it lists the final shapes, including the quoted-JSON shape it already omits. Run the docs checkers from `routing.md` Tools after the edit.

## Assumptions
- The "colon form" scope is the existing key names only (Issue Constraint); keys with a prefix such as `access_token` are matched the same way the existing `key=value` patterns match them (no word boundary), which is a judgment carried over from the existing patterns, falsifiable by the AC-1 test.
- Path A: 3 target files, no signature or interface change, no schema change; `SECRET_PATTERNS` is module-internal (only the masker's own test imports it).
- Unquoted `key: value` matching can mask the word after a prose colon (for example `Invalid token: expired` becomes `Invalid token: ***MASKED***`); this is accepted over-masking for a security masker, falsifiable by the AC-5 prose test and revisited under UNK-01.
- Step 8b: `tools/check_plan_target_overlaps.py` reports no overlap naming this Plan (the 20 findings concern only the four workflow-engine Plans `wftaskapi001`, `wfrecovery001`, `wflease001`, `wfretry001`); no compatibility or sequencing judgment is needed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How far whitespace and multi-line coverage should go for unquoted values without false positives on ordinary text (mask to end of line, to a delimiter, or leave out); Issue "Unresolved Questions" calls it an owner design choice | No owner decision; no data on typical stderr line shapes | Owner decides at `plan-to-implementation-procedure` time. Default if no decision: implement REQ-001 and REQ-002 (quoted values cover whitespace deterministically) and record in tests and docs that unquoted whitespace / multi-line values are intentionally left out, as the Issue permits ("or record the decision to leave them out") | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/secrets_masker.py | Modify | Medium (four masking call sites in startup and lifecycle error paths; behavior of masked text changes) | N/A | N/A | Deployed runtime file under `scripts/agent/`: takes effect only after a deploy (hand-off to `skills/deploy/SKILL.md`) |
| tests/agent/test_secrets_masker.py | Modify | Low | N/A | N/A | None: tests are not deployed |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Modify | Low | N/A | N/A | None: docs are not deployed |

## Design
- Path A (Step 3): 3 target files, no public/runtime interface change, no schema change. Baseline: `radon cc` on the masker reports `_mask_secrets` rank A (2); `vulture` and `bandit` runs show no findings on the target (the findings elsewhere are pre-existing and unrelated); the diff-cover baseline needs a full-suite run and is deferred to the implementation phase, which must reach the threshold in `rules/toolchain.md`.
- Approach: add pattern(s) reusing the existing key alternation `(?:password|passwd|pwd|api[_-]?key|apikey|secret|token)` with `\s*:\s*` and `(\S+)` for unquoted values, and a quoted variant capturing up to the matching quote for whitespace-containing quoted values. Keep the substitution `m.group(1) + "***MASKED***"`.
- Ordering decision: because patterns run sequentially on the same string, a colon pattern that masks the word after `token:` would turn `token: Bearer abc` into `token: ***MASKED*** abc` and the later Bearer pattern would then not match `Bearer`, leaking `abc`. The implementation must place or shape the colon pattern(s) so no part of such a value survives (AC-4); this is a design constraint for the procedure phase, not new scope.
- `Authorization:` is not among the key names, so `Authorization: Bearer abc` is still handled by its own pattern; the colon patterns must not break scheme preservation.
- Alternatives for UNK-01: (a) quoted-only whitespace coverage and leave unquoted whitespace out (default, lowest false-positive risk); (b) mask to end of line for unquoted values (covers multi-line only line by line, risks over-masking trailing text); (c) mask to a delimiter. Compatibility impact: (b)/(c) change the pinned `token=abc def` expectation.
- Patterns are not combined across keys beyond the shared alternation, so the existing `test_pattern_count_grew_by_exactly_one` assertion is updated, not deleted, to the new count.

## Implementation steps
1. **Phase 1: Tests first (revertable alone)**
   - [ ] Add failing tests for colon, quoted-colon, prefixed-key, whitespace / multi-line (per UNK-01), ordering `token: Bearer abc`, no-false-positive and idempotence cases (REQ-001, REQ-002, REQ-003, REQ-004; tests/agent/test_secrets_masker.py)
2. **Phase 2: Core logic**
   - [ ] Extend `SECRET_PATTERNS` with the colon and quoted-colon patterns and implement the UNK-01 decision, leaving the substitution lambda and signature unchanged (REQ-001, REQ-002, REQ-003, REQ-005; scripts/agent/secrets_masker.py)
   - [ ] Update the pattern-count assertion (and the `token=abc def` expectation only if UNK-01 changes it) (REQ-003, REQ-004; tests/agent/test_secrets_masker.py)
3. **Phase 3: Documentation**
   - [ ] Update the "Secret Masking in MCP Subprocess Failure Reports" section to list the final shapes (REQ-006; docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the validation sequence in the Validation plan; confirm call-site tests pass; hand off to `skills/deploy/SKILL.md` for the `scripts/` change (prerequisite: the change is committed and pushed first; deploying is the user's decision) (REQ-005; scripts/agent/secrets_masker.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py | Unit | `uv run pytest tests/agent/test_secrets_masker.py` | All new and regression tests pass |
| Call sites | Integration (regression) | `uv run pytest tests/agent/test_http_lifecycle_command_validator.py tests/agent/test_startup_mcp_starter.py` plus `tests/agent/test_http_lifecycle*.py` | Pass unchanged (REQ-004, REQ-005) |
| scripts/agent/secrets_masker.py | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml` per `rules/toolchain.md` | Clean |
| scripts/agent/secrets_masker.py | Size gate | `uv run python tools/check_module_size.py` | Pass |
| scripts/agent/secrets_masker.py | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` per `rules/toolchain.md` | At or above threshold |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Docs checks | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` | Pass |

## Risks
- **Risk**: A colon pattern that matches before the Bearer / Authorization patterns leaves part of a value unmasked (`token: Bearer abc`) → **Mitigation**: AC-4 ordering test; place or shape patterns accordingly; idempotence test.
- **Risk**: Over-masking of prose like `Invalid token: expired` obscures diagnostics (likelihood Medium) → **Mitigation**: accepted for a security masker; AC-5 pins the no-secret samples; UNK-01 owner decision can narrow it.
- **Risk**: Catastrophic backtracking or slowdown from a new quoted or multi-line pattern on large stderr tails (likelihood Low; tails are 512 or 500 characters) → **Mitigation**: use bounded, non-nested quantifiers; add a large-input test.
- **Risk**: `test_pattern_count_grew_by_exactly_one` and the `token=abc def` test pin current behavior and fail on change (likelihood High) → **Mitigation**: both are in the test target row and updated in the same change.
- **Risk**: Sequencing with `diagmask001` / `maskargs001`, which depend on this Plan's final pattern set (likelihood Medium) → **Mitigation**: implement this Plan first; recorded in Scope Dependencies.
- **Risk**: The `scripts/` change takes effect only after deploy → **Mitigation**: Phase 4 hand-off to `skills/deploy/SKILL.md` after commit and push.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: colon, quoted-colon, whitespace / multi-line, ordering, no-false-positive tests (tests/agent/test_secrets_masker.py) | In Progress | — | — |  |
| 2 | Core logic: extend `SECRET_PATTERNS`, UNK-01 decision, update pinned tests (scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py) | In Progress | — | — |  |
| 3 | Documentation: update the masker section (docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md) | In Progress | — | — |  |
| 4 | Deployment and verification: validation sequence, call-site tests, deploy hand-off (scripts/agent/secrets_masker.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-132558_02_tests_agent_test_secrets_masker.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261102-132558_01_scripts_agent_secrets_masker.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-132558_03_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-140116
- **Related target files**: scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (colon form); direct run | scripts/agent/secrets_masker.py | 2 | AC-1 | Tests: unquoted colon forms | Confirmed by repository evidence |
| REQ-001 | Issue Testing Expectations (colon-separated form) | tests/agent/test_secrets_masker.py | 1 | AC-1 | Tests: unquoted colon forms | Explicit in issue |
| REQ-002 | Issue Implementation Intent (`key: "value"`); direct run | scripts/agent/secrets_masker.py | 2 | AC-2 | Tests: quoted colon forms | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (colon form with quotes) | tests/agent/test_secrets_masker.py | 1 | AC-2 | Tests: quoted colon forms | Explicit in issue |
| REQ-003 | Issue Required Changes (whitespace / multi-line decision); Unresolved Questions | scripts/agent/secrets_masker.py | 2 | AC-3 | Tests: whitespace / multi-line | Needs confirmation |
| REQ-003 | Pinned `token=abc def` expectation in the existing test module | tests/agent/test_secrets_masker.py | 1, 2 | AC-3 | Tests: whitespace / multi-line | Confirmed by repository evidence |
| REQ-004 | Issue Testing Expectations (regression, no false positive); retry_helper double masking | tests/agent/test_secrets_masker.py | 1, 2 | AC-4, AC-5 | Tests: regression, ordering, idempotence | Derived from confirmed evidence |
| REQ-005 | Issue Constraints; AI Implementation Instruction | scripts/agent/secrets_masker.py | 2, 4 | AC-6 | Validation plan: call-site tests, `git diff` check | Explicit in issue |
| REQ-006 | `agent_10_01` section states "three shapes" (Issue Documentation Impact says N/A) | docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | 3 | AC-7 | Validation plan: docs checkers | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-132558 -->