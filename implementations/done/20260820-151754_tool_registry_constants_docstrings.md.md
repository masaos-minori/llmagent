# Implementation Procedure: Correct ToolRegistry/tool_constants docstrings to reflect verified production usage

## Goal
Update the module/class docstrings in `scripts/shared/tool_registry.py` and `scripts/shared/tool_constants.py` so they name every verified production consumer of `ToolRegistry` and the `tool_constants.py` frozensets (not just drift/config validation), and reconcile `docs/04_mcp_03_02_tool-registry.md` with the corrected docstrings — with no runtime behavior change.

## Goal
Update the module/class docstrings in `scripts/shared/tool_registry.py` and `scripts/shared/tool_constants.py` so they name every verified production consumer of `ToolRegistry` and the `tool_constants.py` frozensets (not just drift/config validation), and reconcile `docs/04_mcp_03_02_tool-registry.md` with the corrected docstrings — with no runtime behavior change.

## Scope
- Target files:
  - `scripts/shared/tool_registry.py`: module docstring (lines 2-28) — add the `agent.tool_policy.classify_operation_type()` fail-safe membership-check consumer alongside the existing drift-detection framing
  - `scripts/shared/tool_constants.py`: module docstring (lines 4-18) — replace the inaccurate "fallback/compatibility... never the first-checked source" closing paragraph with per-consumer statements
  - `docs/04_mcp_03_02_tool-registry.md`: reconcile the inaccurate "ToolRegistry はルーティング判断には一切使われない" sentence (line 138) and the opening paragraph's "ドリフト検出用のシードデータ" framing (line 20) with the corrected docstrings

## Assumptions
- The requirement's verified line numbers and call-site claims are accurate as of current `master` HEAD
- No behavior change is required or permitted; every acceptance criterion is satisfied by docstring/doc text edits alone
- `docs/04_mcp_03_02_tool-registry.md` is the correct (and only) doc file that needs reconciliation

## Design decisions
### Sequencing dependency (must be honored by implementation phase):
This plan's implementation must **not start before** the implementation of `plans/20260819-182209_plan.md` (source requirement `requires/done/20260818-223342_require.md`, which deletes the dead `RuntimeToolRegistry.is_side_effect()`/`classify_operation_type()` methods) is complete. Reason: this plan's `tool_constants.py` docstring rewrite states, as a factual claim, that "the only other candidate classifier (`RuntimeToolRegistry.is_side_effect()`) had zero production callers and is being removed as dead code" — sourced from that requirement's own conclusion. If that deletion has not yet landed, the corrected docstring's claim about the *current* state of the codebase would be describing a still-open removal as done, which is itself a fresh docstring-accuracy defect of the same kind this requirement exists to fix. The implementer must check `plans/done/` for `20260819-182209_plan.md` before writing the final wording.

This plan has **no dependency** on `plans/20260819-181912_plan.md` (the `ToolRouteResolver` dead-argument removal) — that plan does not touch `tool_registry.py`, `tool_constants.py`, or their docstrings, and this plan's text does not reference `ToolRouteResolver`'s constructor arguments.

### Docstring content design:
1. `scripts/shared/tool_registry.py` module docstring: replace the single-role sentence with two enumerated roles:
   (a) drift-detection input for `McpToolDiscoveryService` (`validate_routing_against_live`, `validate_routing_against_config`) and config drift checks (`check_tool_safety_tiers`, etc. via `production_config_validator.py` and `repl_health.py`);
   (b) the fail-safe "is this a known tool at all" membership check consulted by `agent.tool_policy.classify_operation_type()` (`scripts/agent/tool_policy.py:69`) to distinguish `OperationType.READ` from `OperationType.UNKNOWN` on the live risk-classification path.
   Add one sentence recording the maintain-vs-abolish decision as resolved (maintain), citing `repl_health.py`, `mcp_tool_discovery.py`, and `production_config_validator.py` as the active wiring evidence. Leave the "Ownership model" bullet list and the "Drift detection" function list untouched — only the opening role-description paragraph changes.

2. `scripts/shared/tool_constants.py` module docstring: replace the closing "fallback/compatibility... never the first-checked source" paragraph with three per-consumer statements (registry seed = one-time import-time seed, not a fallback; side-effect detection = sole first-checked classifier used by `ToolExecutor.execute()`; risk classification = direct first-checked WRITE/DELETE/EXECUTE/API_WRITE tiers). Keep the existing "Not a routing fallback source" sentence about live `/v1/tools` discovery — that sentence is independently accurate and orthogonal to the paragraph being replaced. No new validators are added for the two new fields; the existing `StrEnum`/`frozenset` machinery is unchanged.

3. `docs/04_mcp_03_02_tool-registry.md`: adjust the opening paragraph (line 20) and the closing paragraph of the "`RuntimeToolRegistry` とライブ検出" section (line 138) to add the `tool_policy.py:69` consumer, mirroring the corrected `tool_registry.py` docstring's two-role framing, so the doc and code agree. This doc edit is explicitly in scope per the requirement's Implementation instructions #4 and Acceptance criteria.

## Implementation steps
1. **Phase 1 — Preparation**
   - [ ] Confirm `plans/20260819-182209_plan.md` has landed (check `plans/done/` for the file and, if needed, `git log -- scripts/shared/runtime_tool_registry.py` for the deletion commit) before starting. If not yet landed, word the `tool_constants.py` docstring's dead-code reference in the not-yet-removed form described in Design, and re-check before the final commit.
   - [ ] Re-confirm current line numbers in `scripts/shared/tool_registry.py`, `scripts/shared/tool_constants.py`, `docs/04_mcp_03_02_tool-registry.md` immediately before editing (they may have shifted since this plan's verification pass).

2. **Phase 2 — Core docstring edits**
   - [ ] Edit `scripts/shared/tool_registry.py` module docstring per Design step 1.
   - [ ] Edit `scripts/shared/tool_constants.py` module docstring per Design step 2.
   - [ ] Edit `docs/04_mcp_03_02_tool-registry.md` lines 20 and 138 per Design step 3.

3. **Phase 3 — Deployment/verification (mandatory)**
   - [ ] No `deploy/deploy.sh` change needed — no file added/removed under `scripts/`, so confirm via `git diff --stat` after implementation that no new/removed top-level module needs a `deploy.sh` line.
   - [ ] Run the full validation sequence per `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, pytest, diff-cover, pre-commit) before considering the change complete.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/tool_registry.py` (`MemoryConfig.__post_init__`) | Unit — direct construction with each of 4 invalid values | `uv run pytest tests/agent/test_config*.py -v -k memory` | `ValueError` raised for each invalid field, matching build-path messages |
| `scripts/agent/config_builders.py` (`build_agent_config`, `_build_memory_config`, `_build_llm_config`) | Unit/integration — toml override values | `uv run pytest tests/agent/test_config*.py -v -k "build or reload"` | `agent_memory_max_startup_snippets`, `llm_compress_temperature`, `llm_compress_max_tokens` reach their respective dataclasses; reload still raises `ConfigReloadValidationError` for invalid `MemoryConfig` toml values |
| `scripts/agent/memory/injection.py` (`InjectionPolicy`) | Unit — default parity | `uv run pytest tests/agent/test_memory*.py -v -k min_importance` | `InjectionPolicy().min_importance == MemoryConfig().memory_min_importance == 0.3` |
| `scripts/agent/factory.py` (`_build_history_manager`) | Unit — compression params sourced from config | `uv run pytest tests/agent/test_factory*.py -v -k compress` | Custom toml value reaches `HistoryManager`'s compression call; default preserves `0.3`/`300` |
| Repo-wide | Full regression | `uv run pytest` | No new failures |
| Repo-wide | Lint/type/arch/security gate | `uv run ruff check scripts/`, `uv run mypy scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | All pass, no new findings |
| Repo-wide | Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% on changed lines |
| Repo-wide | Final gate | `uv run pre-commit run --all-files` | Passes |

## Risks
- **Risk**: Removing the inline `ConfigReloadValidationError` raises in `_build_memory_config` (item 4) could silently change the exception type surfaced to `/reload` callers if the reload path's error handling specifically matches on `ConfigReloadValidationError` rather than a broader `Exception`/`ValueError` catch (likelihood: medium — this is exactly the kind of behavior change the source requirement's Acceptance criteria warns against: "No existing test regresses"). **Mitigation**: before removing the inline raises, grep `config_reload.py`/`repl_health.py`/related test files for `except ConfigReloadValidationError` to confirm the catch is broad enough (e.g. wraps the whole `build_agent_config` call) that a `ValueError` from `MemoryConfig.__post_init__` is still caught and reported the same way; if the catch is narrow, either widen it or wrap the `_build_memory_config` call site to convert `ValueError` -> `ConfigReloadValidationError` explicitly, as noted in Design/Implementation step 3.
- **Risk**: Wiring `agent_memory_max_startup_snippets` (item 1) changes behavior for any operator whose toml already sets this key expecting it to be silently ignored (likelihood: low — a key that has always been inert is unlikely to be deliberately set to a non-default value in production config, but cannot be ruled out without checking deployed `config/agent.toml`). **Mitigation**: grep `config/agent.toml` and any `config/*.toml.example` files for `agent_memory_max_startup_snippets` before implementing; if present with a non-default value, flag to the maintainer for explicit confirmation that the newly-effective value is intended.
- **Risk**: Removing now-unused `_COMPRESS_TEMPERATURE` / `_COMPRESS_MAX_TOKENS` module constants (item 6) could break an external test or doc that imports them directly (likelihood: low). **Mitigation**: Phase 6's stale-reference sweep (`rg "_COMPRESS_TEMPERATURE|_COMPRESS_MAX_TOKENS" scripts/ docs/ tests/`) covers `scripts/` and `docs/`; extend the same grep to `tests/` before removing the constants.
- **Risk**: This plan's scope determination (items 2/3 already resolved, items 1/4/5/6 remaining) rests on this cycle's source-reading; if a *third*, still-more-recent cycle already addressed items 1, 4, or 6 between this plan's authoring and its implementation, the plan could become partially redundant again (likelihood: low given no other `requires/`, `plans/`, or `implementations/` file currently references `issues/20260817_07_issue.md` beyond the two cycles already found in this session). **Mitigation**: re-run `grep -rl "20260817_07" requires/done/*.md plans/done/*.md implementations/done/*.md` at the start of the implementation phase to catch any newer cycle before starting work.

## Traceability
- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/done/20260818-215146_require.md
- Source plan: plans/20260819-182458_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-151754
- Related target files: scripts/shared/tool_registry.py, scripts/shared/tool_constants.py, docs/04_mcp_03_02_tool-registry.md