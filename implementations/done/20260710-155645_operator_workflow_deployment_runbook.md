# Implementation: "Workflow Deployment Runbook" operator section

## Goal

Add an operator-focused runbook — one section per failure scenario with diagnosis and copy-pasteable recovery commands — covering all workflow-mandatory deployment/startup failure modes, and cross-link `docs/02_deployment.md` to it instead of duplicating content.

## Scope

**In:**
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`: add a new "Workflow Deployment Runbook" section, immediately after the existing "## Workflow Startup Validation" section (lines 25-50) and before "## MCP Server Reload and Restart Semantics" (line 53)
- `docs/02_deployment.md`: one cross-reference line pointing to the new runbook section

**Out:**
- No duplication of the summary checklist/failure-table already added by `implementations/20260710-155615_docs_deployment_workflow_responsibility.md`'s §3.2/§3.3 — this is the deeper, per-scenario runbook
- No code change

## Assumptions

1. Depends on the same prerequisite implementation docs as `implementations/20260710-155615_docs_deployment_workflow_responsibility.md` (deploy.sh/init_db.sh/setup_services.sh checks, validator CLI, schema versioning) — copy-pasteable commands and message text must match those scripts' actual final wording once implemented.
2. Target file is confirmed (via direct read) to be `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md` — the successor of the plan's originally-named `docs/05_agent_10_operations-and-observability-validation-and-troubleshooting.md`, after this session's concurrent doc-splitting. It already contains "## Workflow Startup Validation" (line 25) confirming `workflow_mode` is a rejected config key with no disable path, and "## MCP Server Reload and Restart Semantics" (line 53) directly after it.

## Implementation

### Target files

`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`, `docs/02_deployment.md`

### Procedure

1. In `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`, immediately after line 50 (the "...restarting the agent." sentence ending the "Workflow Startup Validation" section) and its trailing `---` at line 51, before line 53's "## MCP Server Reload and Restart Semantics", insert:
   ```markdown
   ## Workflow Deployment Runbook

   Workflow is a **mandatory** deployment artifact — there is no config setting, environment
   variable, or deploy flag to disable or bypass it. Every failure mode below has a concrete
   recovery path; none of them involve "turning workflow off."

   ### Quick validation commands

   ```bash
   # Validate a workflow definition file directly (does not start any service)
   PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json

   # Check workflow DB schema tables and version (against the deployed DB)
   sqlite3 /opt/llm/db/workflow.sqlite ".tables"
   sqlite3 /opt/llm/db/workflow.sqlite "SELECT * FROM workflow_schema_version ORDER BY applied_at DESC;"
   ```

   ### Missing `config/workflows/default.json`

   **Symptom:** `deploy.sh` prints `[FATAL] Missing required workflow definition: config/workflows/default.json` and exits before copying anything.

   **Recovery:**
   ```bash
   git checkout HEAD -- config/workflows/default.json   # restore from version control
   bash deploy/deploy.sh                                 # re-run deployment
   ```

   ### Invalid workflow JSON (parse error)

   **Symptom:** `deploy.sh` (or the validator CLI directly) prints `[FATAL] Invalid workflow definition ...: <JSON parse error>`.

   **Recovery:** Fix the reported JSON syntax error, then re-validate before re-deploying:
   ```bash
   PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json
   ```

   ### Missing required stages

   **Symptom:** The validator reports `required stages missing: <names>`.

   **Recovery:** Ensure the workflow definition's `stages` array includes objects with `id` values `plan`, `execute`, and `verify` (each also carrying `description`, `timeout_sec`, `retryable`).

   ### Invalid retry policy

   **Symptom:** The validator reports one of: `retry_policy.max_attempts must be >= 1`, `retry_policy.backoff must be one of: exponential, fixed`, or `retry_policy.backoff_sec must be >= 0`.

   **Recovery:** Correct the named `retry_policy` field per the message, then re-validate.

   ### Missing or incomplete `workflow.sqlite`

   **Symptom:** `init_db.sh` or `setup_services.sh` prints `Workflow database schema is missing or incomplete.` naming one or more missing tables.

   **Recovery:**
   ```bash
   bash deploy/init_db.sh   # (re-)creates workflow.sqlite; safe to re-run (idempotent)
   ```

   ### Schema version mismatch

   **Symptom:** Agent startup or `setup_services.sh` reports `Workflow schema version mismatch: expected <X>, found <Y>`.

   **Recovery:**
   ```bash
   bash deploy/init_db.sh   # applies pending migrations and records the current version
   ```

   ### Workflow definition update requires a restart

   **Symptom:** A new `config/workflows/default.json` was deployed, but the running agent does not pick it up.

   **Explanation:** The workflow definition is validated and loaded exactly once, at agent boot (`StartupOrchestrator._check_workflow_definition()` in `agent/startup.py`, then `Orchestrator.__init__()`). It is **not** a hot-reloadable setting — `/reload` does not apply to it.

   **Recovery:** Deploy the new definition (`deploy.sh`), then fully restart the agent process. There is no partial-update path.

   ---
   ```
   (The trailing `---` matches the file's existing section-separator convention, keeping "## MCP Server Reload and Restart Semantics" visually separated as before.)
2. In `docs/02_deployment.md`, add one cross-reference line (coordinate with `implementations/20260710-155615_docs_deployment_workflow_responsibility.md`'s edits to the same file so both land as a single combined change, not two independent edits): after the new §3.3 failure-mode table, add:
   ```markdown
   For detailed diagnosis and recovery commands per failure mode, see [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook).
   ```
3. Run `python -m tools.check_docs_consistency` to confirm no broken links.

### Method

Direct section insertion at a confirmed line boundary (between two existing `##` sections) — no restructuring of the surrounding file. One additional cross-reference line in a sibling doc.

### Details

- All quoted `[FATAL]`/`RuntimeError` message strings must be verified against the actually-implemented scripts/functions (`implementations/20260710-155320_*`, `20260710-155345_*` for validate.py/deploy.sh metadata; `20260710-155420_*`, `20260710-155445_*`, `20260710-155505_*` for schema version) at the time this doc change is applied — if wording differs from what's drafted here, the doc must match the real implementation, not vice versa.
- `<X>`/`<Y>` in the "Schema version mismatch" scenario are literal placeholders matching the actual `RuntimeError`/`[FATAL]` message format (`expected {WORKFLOW_SCHEMA_VERSION!r}, found {actual_version!r}`) — kept as placeholders since real values vary per deployment, not replaced with a fixed example.

## Validation plan

```bash
python -m tools.check_docs_consistency
grep -n "Workflow Deployment Runbook" docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
grep -n "Workflow Deployment Runbook" docs/02_deployment.md
```

Expected outcome: `check_docs_consistency` passes; the runbook section appears between "Workflow Startup Validation" and "MCP Server Reload and Restart Semantics"; `docs/02_deployment.md` links to it without duplicating its content; every command in the runbook is copy-pasteable with no unresolved placeholders beyond the documented `<X>`/`<Y>` literal-format markers.
