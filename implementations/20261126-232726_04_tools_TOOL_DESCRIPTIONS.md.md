## Goal

Register the new checker in the tool inventory so the inventory-drift gate passes (REQ-004 — the checker is
registered in the tool inventory).

## Scope
**Release unit**: taxonomy mechanism

## Assumptions

- Confirmed in Step 3a: `rules/tool-gates.md` requires every `tools/` script to be registered in
  `tools/TOOL_DESCRIPTIONS.md`, and the file has two parts that both need the entry — the short inventory
  table (e.g. `check_conftest_integrity.py` at `:131`) and the detailed description section (`:251`).

## Design decisions

- The detailed entry states the checker is read-only and that its exit code is gated, matching the wording
  convention of the neighboring entries.

## Alternatives considered

- N/A: documentation-only row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure

- Add `check_test_taxonomy.py` to the inventory table with category `Test` and a one-line description.
- Add the detailed entry: what it reads, the three rule violations, the baseline exemption, the report mode,
  and that it is read-only.

### Method

- Match the existing table column order and the single-paragraph description style.

### Details

- The entry must name the gate, since the gate definition (document 05) and the CI lint step (document 07)
  reference the same command.

## Compatibility considerations

- `tools/check_tool_descriptions_sync.py` also fails when a CI workflow or pre-commit hook references an
  unregistered tool, so the entry must be added in the same commit as the checker and the CI step.

## Security considerations

- N/A: documentation-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Static — `uv run python tools/check_tool_descriptions_sync.py`.
- Documentation gates (`rules/tool-gates.md`): `check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_japanese.py`.

## Completion criteria

- The inventory and the detailed section both name `check_test_taxonomy.py`, and the drift check reports no
  finding.

## Out of Scope

- The checker implementation (document 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the inventory entry per Procedure/Method/Details | Pending | — | — | |
| 3 | Run the documentation gates named in `rules/tool-gates.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (tool-inventory registration)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
