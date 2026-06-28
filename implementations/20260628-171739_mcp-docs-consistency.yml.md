# Implementation and Test Procedure: MCP Docs Consistency CI Workflow

## Goal

Create a GitHub Actions workflow that runs `scripts/check_mcp_docs_consistency.py` on every push/PR to the main branch, automatically detecting MCP documentation drift.

## Scope

**In-Scope**:
- Create `.github/workflows/mcp-docs-consistency.yml`
- Configure CI to run the existing consistency check script

**Out-of-Scope**:
- Modifying the consistency check script (already complete)
- Fixing pre-existing documentation warnings

## Assumptions

1. GitHub Actions is available for this repository
2. The repo uses standard GitHub-hosted runners (ubuntu-latest)
3. No external dependencies are needed — the script uses only Python stdlib
4. CI should run on push to main and on pull requests targeting main

## Implementation

### Target file

`.github/workflows/mcp-docs-consistency.yml`

### Procedure

1. Create `.github/` directory if it does not exist
2. Create `.github/workflows/` directory if it does not exist
3. Write the workflow YAML file

### Method

Create a standalone GitHub Actions workflow that:
- Triggers on `push` to `main` and `pull_request` targeting `main`
- Uses `ubuntu-latest` runner
- Runs Python 3.10+ (no pip install needed — script uses only stdlib)
- Executes `python scripts/check_mcp_docs_consistency.py --all` from the repo root
- Fails the workflow if the script exits non-zero

### Details

```yaml
name: MCP Docs Consistency Check

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  mcp-docs-consistency:
    name: MCP Docs Consistency
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Run MCP docs consistency check
        run: |
          python scripts/check_mcp_docs_consistency.py --all
```

## Validation plan

| Check | Tool/Method | Target |
|---|---|---|
| Script runs without errors | `python scripts/check_mcp_docs_consistency.py --all` | Exit 0 after warnings addressed |
| Workflow YAML syntax valid | `python -c "import yaml; yaml.safe_load(open('.github/workflows/mcp-docs-consistency.yml'))"` | No parsing errors |
| CI runs on PR | Push test branch, open PR to main | Workflow appears in Actions tab |
| CI fails on drift | Introduce a deliberate inconsistency (e.g., invalid startup_mode), push | Workflow fails with exit code 1 |
