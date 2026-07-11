# Implementation: fix stale `workflow_mode` table, path-pairing, and cross-links

## Goal

Fix the one genuinely stale documentation section still describing `workflow_mode` as a live 3-valued config option, confirm source/deployed path pairing in the deployment doc, and add cross-links between deploy-time validation, loader validation rules, and startup-validation/runbook documentation.

## Scope

**In:**
- `docs/01_overview-arch-02-pipelines.md` (successor of the plan's originally-named `docs/01_overview-arch-pipelines.md`, confirmed via direct grep — the doc-splitting session renamed it): replace the stale "`workflow_mode` の3種" table at lines 66-72
- `docs/02_deployment.md`: confirm both source and deployed paths appear paired in the workflow-responsibilities text added by `implementations/20260710-155615_docs_deployment_workflow_responsibility.md`
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md` (successor of `docs/05_agent_03_turn-processing-flow-workflow-engine.md`, confirmed via direct grep): add a cross-link after "### Workflow Loader Validation Rules" (line 95-105)
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`: add a pointer from "## Workflow Startup Validation" (line 25) to the loader validation rules

**Out:**
- No blanket "workflow definition file" → "required workflow deployment artifact" terminology swap — every other occurrence already reads unambiguously as mandatory (per plan Assumption 2); only this one Design section introduces the defined term
- No re-documentation of `workflow_mode`/`workflow_require_approval` removal — already correctly documented in `docs/05_agent_08_01_configuration-loading-agent-config.md` and `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
- No code change

## Assumptions

1. Both of the plan's originally-named target files (`docs/01_overview-arch-pipelines.md`, `docs/05_agent_03_turn-processing-flow-workflow-engine.md`) no longer exist — this session's concurrent doc-splitting activity renamed them to `docs/01_overview-arch-02-pipelines.md` and `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md` respectively (confirmed by direct `grep -rln` for the target content — `workflow_mode の3種` and `Workflow Loader Validation Rules` — at implementation-design time). This is the exact scenario anticipated by the plan's Risk section ("locate the current successor file... at implementation time").
2. Depends on `implementations/20260710-155615_docs_deployment_workflow_responsibility.md` (deployment doc workflow-responsibilities text) and `implementations/20260710-155645_operator_workflow_deployment_runbook.md` (runbook section + anchor) being implemented first, so the cross-link anchors (`#workflow-deployment-runbook`) exist.

## Implementation

### Target files

`docs/01_overview-arch-02-pipelines.md`, `docs/02_deployment.md`, `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`

### Procedure

1. In `docs/01_overview-arch-02-pipelines.md`, replace lines 66-72:
   ```markdown
   **workflow_mode の3種**

   | workflow_mode | 動作 | 失敗時挙動 |
   |---|---|---|
   | `auto` (デフォルト) | ワークフロー定義が存在すれば有効化 | ロード失敗は警告ログで継続 |
   | `required` | ワークフロー定義が必須 | ロード失敗は `RuntimeError` で起動中断 |
   | `disabled` | 常にダイレクト実行 | ワークフローを完全バイパス |
   ```
   with:
   ```markdown
   **ワークフローは常時必須(モード設定なし)**

   `workflow_mode` は設定キーとして存在しない(`build_agent_config()` の `_FORBIDDEN_KEYS` に含まれ、設定すると `ConfigLoadError` で起動不可)。ワークフロー定義 (`config/workflows/default.json` としてデプロイされる **required workflow deployment artifact**) は常に必須であり、存在しない・不正な場合は起動前に `RuntimeError` で中断する。ダイレクト実行へのフォールバックや、ワークフローを無効化する経路は一切存在しない。

   詳細: [02_deployment.md §Workflow deployment checklist](02_deployment.md) / [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook)
   ```
2. In `docs/02_deployment.md`, when applying `implementations/20260710-155615_docs_deployment_workflow_responsibility.md`'s §2.2 addition, confirm (or adjust) the opening sentence so both paths appear together, e.g.:
   ```markdown
   The workflow definition is a **required workflow deployment artifact**:
   source `config/workflows/default.json` → deployed to `/opt/llm/config/workflows/default.json`.
   ```
   in place of (or immediately preceding) that plan's "The workflow definition is a **mandatory** deployment artifact..." sentence, so no single bullet mentions only one path in isolation.
3. In `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md`, immediately after line 105 (the "`retry_policy.backoff_sec` must be >= 0" bullet ending the "Workflow Loader Validation Rules" list) and before the `---` at line 107, insert:
   ```markdown

   See also: [02_deployment.md](02_deployment.md) for deploy-time validation of these same rules,
   and the [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook)
   for recovery steps when a rule is violated.
   ```
4. In `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`, within the existing "## Workflow Startup Validation" section (lines 25-50), immediately after line 45 ("...check.") and before the "**Note:**" paragraph at line 47, insert:
   ```markdown

   For the exact validation rules applied, see
   [05_agent_03_03 §Workflow Loader Validation Rules](05_agent_03_03_turn-processing-flow-workflow-engine.md#workflow-loader-validation-rules).
   ```
5. Run `python -m tools.check_docs_consistency`.
6. Re-grep `docs/` for `workflow_mode` and confirm every remaining hit describes it as removed/forbidden.

### Method

Direct, targeted edits at confirmed (successor) file/line locations — no mechanical find-replace across the doc set, per the plan's explicit Out-of-Scope decision.

### Details

- The successor filenames (`01_overview-arch-02-pipelines.md`, `05_agent_03_03_turn-processing-flow-workflow-engine.md`) were confirmed via direct content grep at design time, not assumed from the plan's original (now-stale) filenames — the plan's own Risk section anticipated exactly this renaming.
- "required workflow deployment artifact" is introduced as a defined term only in the two locations the Design section specifies (the `01_overview-arch-02-pipelines.md` replacement and the `02_deployment.md` opening sentence) — not propagated elsewhere, per the plan's Out-of-Scope decision against a blanket terminology swap.

## Validation plan

```bash
python -m tools.check_docs_consistency
grep -rn "workflow_mode" docs/
grep -n "required workflow deployment artifact" docs/01_overview-arch-02-pipelines.md docs/02_deployment.md
grep -n "Workflow Deployment Runbook\|Workflow Loader Validation Rules" docs/05_agent_03_03_turn-processing-flow-workflow-engine.md docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
```

Expected outcome: `check_docs_consistency` passes; every `workflow_mode` occurrence in `docs/` describes it as removed/rejected, none as a selectable live option; both paths appear paired in `docs/02_deployment.md`'s opening workflow statement; the two new cross-links resolve to existing, correctly-anchored sections in their target files.
