# Implementation: Update compatibility-remnant checks for Shared/DB schema cleanup

## Goal

Add detection rules for patterns eliminated by Shared/DB schema cleanup to `scripts/checks/check_no_compat.py`, preventing reintroduction.

## Scope

- COMPAT_PATTERNS: Add stale reference patterns
  - workflow_schema.py (file reference)
  - db.workflow_schema (module import)
  - python -m db.workflow_schema (execution command)
  - 07_ref-sqlite.md (deleted document reference)
  - 07_spec_db.md (deleted document reference)
  - DOCMISS-01, UNDOC-03, TYPE-01, DESIGN-01, UNIMPL-01 (deprecated issue IDs)
  - .read eventbus/schema.sql (Event Bus direct SQL load)
  - Reference to eventbus/schema.sql as schema initialization source
- DEFAULT_ALLOWLIST: Add necessary files (this file itself, plans/, requires/ etc.)
- NOT added to COMPAT_PATTERNS:
  - retry_count (intentionally deprecated but retained)
  - messages.tool_call_id (intentionally retained and used)

## Assumptions

1. check_no_compat.py can detect new patterns by adding regex to COMPAT_PATTERNS dict
2. plans/ directory is not a scan target (only scripts/, docs/, tests/) so no allowlist needed
3. requires/done/ directory is not a scan target so no allowlist needed
4. workflow_schema.py pattern is sufficiently covered by `db.workflow_schema` import regex
5. This file itself (check_no_compat.py) is included in DEFAULT_ALLOWLIST so no false positives

## Implementation

### Target file

- scripts/checks/check_no_compat.py: Add 8 new patterns to COMPAT_PATTERNS, update DEFAULT_ALLOWLIST if needed

### Procedure

#### Phase 1: Current state verification

- Run `uv run python -m scripts.checks.check_no_compat` to confirm current pass/fail
- Check if check_no_compat is registered in .pre-commit-config.yaml

#### Phase 2: Add patterns to COMPAT_PATTERNS

Add the following 8 patterns:

1. `"workflow_schema.py reference"`: `r"db/workflow_schema\.py"` (this file itself is excluded via allowlist)
2. `"db.workflow_schema import"`: `r"from\s+db\.workflow_schema\s+import"`
3. `"import db.workflow_schema"`: `r"import\s+db\.workflow_schema\b"`
4. `"python -m db.workflow_schema"`: `r"python\s+-m\s+db\.workflow_schema"`
5. `"07_ref-sqlite.md reference"`: `r"07_ref-sqlite\.md"`
6. `"07_spec_db.md reference"`: `r"07_spec_db\.md"`
7. `"stale issue ID"`: `r"(?:DOCMISS-01|UNDOC-03|TYPE-01|DESIGN-01|UNIMPL-01)"`
8. `"eventbus schema.sql direct load"`: `r"\.read\s+eventbus/schema\.sql"`

#### Phase 3: Update DEFAULT_ALLOWLIST

- Run `uv run python -m scripts.checks.check_no_compat`
- If false positives appear, add to allowlist

#### Phase 4: Test

- Temporarily insert stale reference into test file and confirm detection
- Remove reference and confirm pass

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| New pattern detection | Insert stale reference in temp file and run | exit code 1 (detected) |
| Clean state | `uv run python -m scripts.checks.check_no_compat` | All checks passed |
| Format | `ruff format --check scripts/` | No diff |
| Lint | `ruff check scripts/` | 0 errors |
| Type check | `mypy scripts/` | No new type errors |
