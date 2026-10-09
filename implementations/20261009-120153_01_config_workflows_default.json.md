## Goal

Implement **REQ-002**: set `require_approval: true` in the bundled `config/workflows/default.json`, so the shipped default workflow satisfies the mandatory approval policy.

## Scope

Modify `config/workflows/default.json` only. Reference read only: `scripts/agent/workflow/workflow_loader.py` (the loader that now enforces this; seq 02).

## Assumptions

- `default.json` is the only workflow file under `config/workflows/` (confirmed).
- The value is a JSON boolean at line 25: `"require_approval": false`.

## Design decisions

- Flip the existing `false` literal to `true` in place; do not add a comment or restructure the JSON.

## Alternatives considered

- Adding a new key or moving `require_approval`: rejected — the key already exists at the top level; only its value changes.

## Implementation
### Target file
`config/workflows/default.json`

### Procedure
Change the `require_approval` value from `false` to `true`.

### Method
1. Open `config/workflows/default.json`.
2. On line 25, replace:
   ```json
   "require_approval": false
   ```
   with:
   ```json
   "require_approval": true
   ```
3. Preserve indentation and trailing formatting.

### Details
- The file's other keys are unchanged. `workflow_loader._validate()` (seq 02) now requires this to be `true`, so this edit is what keeps the shipped config valid.

## Compatibility considerations

- Any startup test that asserts the default workflow had `require_approval: false` must be updated. None is expected (only this file sets the bundled default).

## Security considerations

- This is the data-side half of closing AGENT-001: the loader enforces the rule (seq 02) and this file complies with it.

## Rollback considerations

- Restore `"require_approval": false`. Reverting alone is insufficient — the loader change (seq 02) must also be reverted, else the default workflow fails to load.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `default.json` | File check + startup load | pytest / read | `require_approval: true`; loads OK |

## Completion criteria

- `config/workflows/default.json` line 25 reads `"require_approval": true`.
- The default workflow loads without `WorkflowLoadError`.

## Out of scope
- Loader logic (seq 02). Documentation (seq 03-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Set `require_approval: true` in default.json | Completed | — | 20261009-122445 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261009-122445 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261009-122445 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261009-122445 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: `issues/done/20261007-154046_approval01_enforce-approval-policy-in-configuration-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-161457_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-120153
- **Related target files**: `config/workflows/default.json`