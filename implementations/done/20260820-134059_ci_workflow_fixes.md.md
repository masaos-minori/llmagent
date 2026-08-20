# Implementation Procedure: Fix CI Workflow Invocations for Docs Consistency Checker

## Goal
Fix three GitHub Actions workflow files that invoke deleted per-domain scripts (`check_overview_docs_consistency.py`, `check_deployment_docs_consistency.py`, `check_rag_docs_consistency.py`) to instead call the consolidated `tools/check_docs_consistency.py --domain <domain>`.

## Scope
- Target files:
  - `.github/workflows/overview-docs-consistency.yml`
  - `.github/workflows/deployment-docs-consistency.yml`
  - `.github/workflows/rag-docs-consistency.yml`
- Change `run:` step to invoke `python tools/check_docs_consistency.py --domain <overview|deployment|rag>`

## Assumptions
- The per-domain scripts (`check_overview_docs_consistency.py`, etc.) no longer exist (deleted in prior consolidation)
- The consolidated `tools/check_docs_consistency.py` supports `--domain` argument with choices `overview`, `deployment`, `rag`
- Workflow YAML structure otherwise unchanged

## Design decisions
- Simple one-line `run:` command change per workflow
- Preserve all other workflow configuration (triggers, permissions, etc.)
- Domain argument matches the workflow name

## Implementation
### Target files
1. `.github/workflows/overview-docs-consistency.yml`
2. `.github/workflows/deployment-docs-consistency.yml`
3. `.github/workflows/rag-docs-consistency.yml`

### Procedure
For each workflow file:
1. Read the file
2. Locate the `run:` step that invokes the deleted per-domain script
3. Replace with `python tools/check_docs_consistency.py --domain <domain>`

### Method
Direct YAML editing with exact line matching

### Details
**`.github/workflows/overview-docs-consistency.yml`:**
```yaml
# OLD:
- name: Check overview docs consistency
  run: python tools/check_overview_docs_consistency.py

# NEW:
- name: Check overview docs consistency
  run: python tools/check_docs_consistency.py --domain overview
```

**`.github/workflows/deployment-docs-consistency.yml`:**
```yaml
# OLD:
- name: Check deployment docs consistency
  run: python tools/check_deployment_docs_consistency.py

# NEW:
- name: Check deployment docs consistency
  run: python tools/check_docs_consistency.py --domain deployment
```

**`.github/workflows/rag-docs-consistency.yml`:**
```yaml
# OLD:
- name: Check RAG docs consistency
  run: python tools/check_rag_docs_consistency.py

# NEW:
- name: Check RAG docs consistency
  run: python tools/check_docs_consistency.py --domain rag
```

## Compatibility considerations
- No change to workflow triggers, permissions, or other steps
- Consolidated script must support `--domain` argument (verified in plan)
- CI will now run the model reference check if implemented

## Security considerations
- None — CI configuration only

## Rollback considerations
- Git revert of modified workflow files

## Validation plan
- Manual YAML syntax check
- `uv run python tools/check_docs_consistency.py --domain overview` (x3) executes without "script not found" error
- CI workflow syntax valid (`yamllint` or GitHub Actions validation)

## Out of scope
- `agent-docs-consistency.yml` and `mcp-docs-consistency.yml` (out of scope per plan Risks)
- Adding new checks to the consistency checker (separate procedure)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221506_require.md
- Source plan: plans/20260819-174858_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-134059
- Related target files: .github/workflows/overview-docs-consistency.yml, .github/workflows/deployment-docs-consistency.yml, .github/workflows/rag-docs-consistency.yml