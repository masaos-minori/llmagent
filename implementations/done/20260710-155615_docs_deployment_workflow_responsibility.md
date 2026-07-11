# Implementation: document workflow-artifact deployment responsibilities

## Goal

Document, in `docs/02_deployment.md`, the exact workflow-artifact responsibility split across `deploy.sh` → `init_db.sh` → `setup_services.sh`, add a deployment checklist and failure/remediation table, and state that the workflow definition is a mandatory artifact with no disable/bypass mode. Add a one-line responsibility comment to each script's workflow-related block.

## Scope

**In:**
- `docs/02_deployment.md`: extend §2.2, §2.3, §3.1 with workflow-specific bullets; add new §3.2/§3.3 (checklist + failure-mode table)
- `deploy/deploy.sh`, `deploy/init_db.sh`, `deploy/setup_services.sh`: one-line header comment above each workflow-related block, cross-referencing the doc

**Out:**
- No behavior change to any script — comments only
- No README.md update, no separate runbook file (per plan's Out-of-Scope)

## Assumptions

1. This documents the end state after all six prerequisite implementation docs in this session land: `implementations/done/20260710-154614_*`, `implementations/done/20260710-154648_*`, `implementations/done/20260710-154712_*`, `implementations/done/20260710-154751_*`, `implementations/done/20260710-154825_*`, `implementations/20260710-155320_*`/`20260710-155345_*` (metadata/checksum), `implementations/20260710-155420_*`/`20260710-155445_*`/`20260710-155505_*` (schema version). At doc-writing/implementation time, the exact `[FATAL]`/error message strings should be copied verbatim from the actually-implemented scripts, not re-derived from this doc.
2. `docs/02_deployment.md` (confirmed present, unsplit, 208+ lines) is the correct target — its existing §2.2 (line 137), §2.3 (line 153), §3.1 (line 195) already document `deploy.sh`/`setup_services.sh`/`init_db.sh` at a general level.
3. No `README.md` change is made (per plan's Out-of-Scope framing as "Optional").

## Implementation

### Target files

`docs/02_deployment.md`, `deploy/deploy.sh`, `deploy/init_db.sh`, `deploy/setup_services.sh`

### Procedure

1. In `docs/02_deployment.md`, after the existing "deploy.sh does:" bullet list in §2.2 (after line ~146), insert:
   ```markdown
   **Workflow artifact responsibilities (deploy.sh):**
   - Checks that `config/workflows/default.json` exists — aborts before any copy if missing
   - Validates the workflow definition (parseable JSON, required fields/stages/retry-policy) via `python -m agent.workflow.validate`
   - Copies `config/workflows/` to `/opt/llm/config/workflows/`
   - Prints workflow name, version, stage list, and SHA256 checksums (source and deployed); aborts if the checksums differ

   The workflow definition is a **mandatory** deployment artifact. There is no disable, fallback, or workflow-optional mode.
   ```
2. In §2.3, before the existing bash block (after the "MCP servers... auto-start" line, around line 155-156), insert:
   ```markdown
   **Workflow pre-flight responsibilities (setup_services.sh):**
   - Re-checks that the deployed workflow definition (`/opt/llm/config/workflows/default.json`) exists and re-validates it
   - Re-checks that `workflow.sqlite` exists with all required tables and a matching schema version
   - Services (Event Bus, LLM, MCP) are started **only if** all workflow checks pass — a failure here aborts before any service is spawned
   ```
3. In §3.1, after the existing bash block (after line ~203), insert:
   ```markdown
   **Workflow schema responsibilities (init_db.sh):**
   - Creates `workflow.sqlite` and its required tables (`tasks`, `attempts`, `processed_events`, `artifacts`, `approvals`) via `create_workflow_schema()`
   - Applies incremental schema migrations (idempotent — safe to re-run)
   - Verifies all 5 required tables exist after initialization; aborts if any are missing
   - Records the current workflow schema version in `workflow_schema_version`
   ```
4. After §3.1's new content, before "## Related Documents" (line ~204), insert two new subsections:
   ```markdown
   ### 3.2 Workflow deployment checklist

   - [ ] `config/workflows/default.json` exists in the repository before running `deploy.sh`
   - [ ] `bash deploy/deploy.sh` completes with a printed workflow Name/Version/Stages/SHA256 block and no `[FATAL]` errors
   - [ ] `bash deploy/init_db.sh` reports all 5 workflow tables present and the expected schema version recorded
   - [ ] `bash deploy/setup_services.sh` passes its pre-flight workflow checks before any service starts

   ### 3.3 Workflow deployment failure modes

   | Symptom | Failing script | Remediation |
   |---|---|---|
   | `[FATAL] Missing required workflow definition` | `deploy.sh` | Add `config/workflows/default.json` to the repository before deploying |
   | `[FATAL] Invalid workflow definition ...` | `deploy.sh` | Fix the JSON per the printed validation error (missing field, duplicate stage ID, invalid retry policy, etc.) |
   | `[FATAL] Deployed workflow definition checksum does not match source` | `deploy.sh` | Re-run `deploy.sh`; investigate why the copy was not byte-identical (disk/filesystem issue) |
   | `Workflow schema missing table '<name>'` / `[FATAL] Workflow database schema is missing or incomplete` | `init_db.sh` or `setup_services.sh` | Run `bash deploy/init_db.sh` to (re-)create the workflow schema |
   | `Workflow schema version mismatch` | `init_db.sh` (agent startup) or `setup_services.sh` | Run `bash deploy/init_db.sh` to apply pending migrations and record the current version |
   ```
5. In each of `deploy/deploy.sh`, `deploy/init_db.sh`, `deploy/setup_services.sh`, add a one-line comment above each workflow-related block, e.g.:
   ```bash
   # Workflow: existence + content validation (see docs/02_deployment.md §2.2)
   ```
   with the section reference adjusted per script (`§2.2` for deploy.sh, `§3.1` for init_db.sh, `§2.3` for setup_services.sh).
6. Run `python -m tools.check_docs_consistency` and `bash -n` on all three scripts.

### Method

Direct doc-section insertion at confirmed line locations, plus one-line comments above already-existing blocks in the three scripts — no restructuring of any file.

### Details

- Exact `[FATAL]` message text in the failure-mode table must match the actually-implemented scripts verbatim (per Assumption 1) — if any prerequisite implementation's message wording differs from this doc's draft (e.g. from `implementations/20260710-155420_*`/`155445_*`/`155505_*` etc.), update the table to match the real strings, not the other way around.
- Comments are placed above blocks, never altering executable lines, so `bash -n` and script behavior are unaffected.

## Validation plan

```bash
python -m tools.check_docs_consistency
bash -n deploy/deploy.sh deploy/init_db.sh deploy/setup_services.sh
grep -n "mandatory" docs/02_deployment.md
grep -n "Workflow deployment checklist\|Workflow deployment failure modes" docs/02_deployment.md
```

Expected outcome: `check_docs_consistency` passes; all three scripts still parse cleanly after comment-only edits; the doc states the workflow definition is mandatory with no bypass, and each script's responsibility appears once without duplicated/conflicting wording.
