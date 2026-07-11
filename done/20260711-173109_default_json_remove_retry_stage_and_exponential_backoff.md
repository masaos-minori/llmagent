# Implementation: `config/workflows/default.json` — Remove Dead `retry` Stage and `exponential` Backoff

## Goal

Remove the dead `retry` stage entry from the `stages` array (confirmed: `WorkflowEngine.run()` never invokes `_run_stage(task, "retry", ...)`, and `_REQUIRED_STAGES` already excludes it) and correct the `plan`/`execute` stage `description` fields to state what actually runs in each stage, closing the gap between the declared schema and confirmed runtime behavior.

## Scope

**In scope:**
- `config/workflows/default.json`: remove the `retry` entry from `stages`; rewrite `plan.description` and `execute.description`.

**Out of scope:**
- `retry_policy.backoff` value itself — already `"fixed"` in this file; no change needed here (the accepted-values narrowing happens in `workflow_loader.py`, separate doc).
- Any Python source change.
- Bumping `version` — not required unless step 7 of the plan's Implementation steps (checking `02_deployment-part1.md`'s schema-version tracking from commit `29562c46`) finds a hard content-hash dependency; that check is out of scope for this file-level doc and belongs to whichever phase covers deployment docs (not part of this plan's explicit file list, so no doc is created for it here — flag at implementation time per plan Design §1).

## Assumptions

- Confirmed via `scripts/agent/workflow/workflow_engine.py::run()` (lines 118-130): only `"plan"`, `"execute"` (via `_run_execute_with_retry()`), and `"verify"` are ever passed to `_run_stage()`. No code path references a `retry`-labeled `StageDefinition`.
- `scripts/agent/workflow/workflow_loader.py::_REQUIRED_STAGES = {"plan", "execute", "verify"}` already excludes `retry`, so removing it from `default.json` remains schema-valid.
- `plan_fn()` (orchestrator.py:195-196) is a deliberate no-op; memory injection and mode classification run inside `execute_fn()` via `_process_turn()` (orchestrator.py:436-437). The current `plan` stage description ("Prepare RAG context and memory injection") is factually wrong; the corrected description must attribute that work to `execute` instead.
- This is a config-content-only change (JSON), not a Python source change.

## Implementation

### Target file

`config/workflows/default.json`

### Procedure

1. Read the current file content in full.
2. Remove the `retry` object from the `stages` array entirely (do not leave an empty placeholder).
3. Replace `plan.description` with text stating: idempotency/bookkeeping stage only, no LLM call; memory injection and mode classification happen in the execute stage.
4. Replace `execute.description` with text stating: memory injection, mode classification, LLM call, and tool execution loop.
5. Leave `verify`'s description, all `timeout_sec`/`retryable` fields, and `retry_policy` (`max_attempts`, `backoff`, `backoff_sec`) unchanged.
6. Leave `name` and `version` unchanged unless the deployment-schema check (plan Implementation step 7) determines a version bump is required — that determination is out of scope for this document.

### Method

Direct JSON text edit (3 stages → 3 stages, i.e. removing one array element and editing two string fields). No schema/structural change beyond the array shrink. Target resulting content:

```json
{
  "name": "default",
  "version": "1.0.0",
  "stages": [
    {
      "id": "plan",
      "description": "Idempotency/bookkeeping stage only; no LLM call. Turn-start audit logging happens before the engine runs; memory injection and mode classification happen in the execute stage.",
      "timeout_sec": 30,
      "retryable": false
    },
    {
      "id": "execute",
      "description": "Memory injection, mode classification, LLM call, and tool execution loop",
      "timeout_sec": 120,
      "retryable": true
    },
    {
      "id": "verify",
      "description": "Result validation and loop guard check",
      "timeout_sec": 10,
      "retryable": false
    }
  ],
  "retry_policy": {
    "max_attempts": 3,
    "backoff": "fixed",
    "backoff_sec": 1
  }
}
```

### Details

- Preserve valid JSON formatting/indentation consistent with the file's current style.
- Do not touch `retry_policy` fields — only the `stages` array and the two description strings change.
- After editing, confirm the file still parses as valid JSON (e.g. via the loader's own parse step at validation time — see Validation plan).

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `default.json`:

| Check | Tool | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_workflow_loader.py tests/test_workflow_engine.py tests/test_workflow_models.py -v` | All pass, including the new/updated test asserting `stages` == `{"plan", "execute", "verify"}` (no `retry`) |
| Startup validation | `uv run python -m scripts.agent.startup` (or the validated CLI entry point from commit `29562c46`'s `validate.py`) against `config/workflows/default.json` | Passes schema validation with the new stage list |
| Regression | `uv run pytest tests/ -k "workflow" -q` | No new failures |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Manual grep | `grep -rn "exponential" config/ scripts/ docs/` | No matches remain outside historical/archival records |
| Manual grep | `grep -rn "\"retry\"" scripts/ docs/` | No structural consumer other than `WorkflowLoader`/`WorkflowEngine` depends on a 4-element `stages` array |
