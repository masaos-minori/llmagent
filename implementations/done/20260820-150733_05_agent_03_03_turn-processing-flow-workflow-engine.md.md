# Implementation Procedure: Define workflow-level `require_approval` production policy and lifecycle

## Goal
Resolve the standing "Needs Confirmation / 未決事項" note on `WorkflowDef.require_approval`'s production default by stating an explicit, decided policy: a per-operation-category approval-requirement table, documented local-development exceptions, a fully specified approval lifecycle (approve / reject / expire / missing / cancel / resume), and config enforcement — plus the minimal code change needed to make the expiration behavior actually work as documented.

## Scope
- Target files: 
  - `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md`
  - `docs/00_governance_07_needs-confirmation-inventory.md`
  - `docs/02_deployment.md`
  - `docs/01_overview-arch-02-pipelines.md`
  - `config/workflows/default.json`
  - `scripts/agent/workflow/workflow_engine.py`
  - `scripts/agent/workflow/approval_ops.py`
  - `scripts/agent/workflow/models.py`
  - `tests/agent/workflow/test_workflow_engine.py`
  - `docs/00_governance_07_needs-confirmation-inventory.md`

## Assumptions
- The "Needs Confirmation / 未決事項" note is still live in `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md` (confirmed present verbatim, twice — the file appears to contain duplicated content blocks)
- No documentation mentions `_APPROVAL_TTL_HOURS` / the 24-hour approval expiration window
- `config/workflows/default.json`'s `require_approval` is currently `false`, with no per-environment override file/mechanism in `config/workflows/`
- The approval gate (`WorkflowEngine._gate_approval`) currently never checks `expires_at` — this is a real gap, not just a doc gap

## Design decisions
- **Category-conditional policy**: Not a blanket `true`/`false`. Production deployments whose default workflow can reach any category marked "Yes" below MUST set `require_approval: true` in their deployed `config/workflows/*.json`. The bundled `config/workflows/default.json` ships `require_approval: false` for local development; per-environment override files are the documented mechanism for production to opt in.
- **Category mapping** (workflow-level approval required in production):
  - File writes: Conditional (only if task also performs a "Yes" category)
  - File deletion: Yes
  - Shell execution: Yes
  - Git commits/pushes: Yes (for push; commit-only may rely on tool-level gate)
  - GitHub changes: Yes (for merge/push; conditional for issue/PR creation)
  - CI/CD execution: Yes
  - Database maintenance: Gap — flagged, no tool exists yet
- **Local-dev exceptions**: Local/development deployments MAY leave `require_approval: false` for all categories, because tool-level pre-execution approval remains active
- **Lifecycle**: Approve/reject/missing unchanged. Expire (new): when `_gate_approval()` finds expired pending record, mark status `"expired"`, call `request_approval()` again to re-request. Cancel: unsupported by design; `/reject` is sole termination path. Resume: unchanged.
- **Config enforcement**: `config/workflows/default.json` keeps `require_approval: false` (local-dev default). Per-environment override files (e.g., `config/workflows/production.json`) are the documented mechanism for production to opt in.

## Implementation steps
1. **Phase 1 — Code (small, testable in isolation)**
   - Add `is_expired(approval: ApprovalRecord) -> bool` to `scripts/agent/workflow/approval_ops.py`
   - Update `WorkflowEngine._gate_approval()` in `scripts/agent/workflow/workflow_engine.py` to detect expired `pending` record, mark it `"expired"`, and call `request_approval()` again to re-request
   - Update the `status` field comment on `ApprovalRecord` in `scripts/agent/workflow/models.py:34` to include `expired`
   - Add `test_expired_pending_approval_is_re_requested` to `tests/agent/workflow/test_workflow_engine.py`, using a fabricated past `expires_at`
   - Re-run existing approve/reject/pending tests to confirm no regression

2. **Phase 2 — Documentation**
   - Replace both occurrences of the Needs-Confirmation note in `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md` with the decided policy text, the 7-category table, local-dev exceptions, and the full lifecycle
   - Add cross-link lines in `docs/02_deployment.md` (~line 183) and `docs/01_overview-arch-02-pipelines.md` (~line 69)
   - Add `NC-018` to `docs/00_governance_07_needs-confirmation-inventory.md` with `status: resolved`, linking to the updated section

3. **Phase 3 — Validation & deployment check**
   - Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy, lint-imports, bandit, targeted + full pytest, diff-cover
   - Confirm `deploy/deploy.sh` needs no changes
   - Confirm `config/workflows/default.json` is unchanged and its `require_approval: false` value is consistent with the documented local-dev-default policy

## Validation plan
- Unit tests: `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` — all existing tests pass; new expiry test passes
- Static: `uv run mypy scripts/`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/agent/workflow/ -c pyproject.toml`
- Doc consistency: `uv run check-mcp-docs` — no broken links / drift introduced by the new cross-links
- Coverage: `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — ≥90% on changed lines
- Pre-commit: `uv run pre-commit run --all-files` — passes

## Risks
- Expanding `ApprovalRecord.status` to include `"expired"` could break callers assuming only `pending|approved|rejected` — mitigated by grepping all `.status ==` / `status=` usages on `ApprovalRecord` before merging
- Documenting a "per-environment override file" convention without implementing an environment-selection loader leaves a documentation/capability gap — mitigated by wording the doc as a recommended operational convention layered on the existing `workflow_loader.py` API
- The duplicated content blocks in `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md` could leave a stale copy if only one occurrence is replaced — mitigated by grepping for the exact Needs-Confirmation sentence before and after editing

## Traceability
- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/done/20260818-222125_require.md
- Source plan: plans/20260819-180036_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-150733
- Related target files: docs/05_agent_03_03_turn-processing-flow-workflow-engine.md, docs/00_governance_07_needs-confirmation-inventory.md, docs/02_deployment.md, docs/01_overview-arch-02-pipelines.md, config/workflows/default.json, scripts/agent/workflow/workflow_engine.py, scripts/agent/workflow/approval_ops.py, scripts/agent/workflow/models.py, tests/agent/workflow/test_workflow_engine.py, docs/05_agent_06_04_tool-execution-and-approval-canonical.md (referenced), docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md (referenced)