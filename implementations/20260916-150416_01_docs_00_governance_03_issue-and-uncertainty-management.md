## Goal

Replace the EVENTBUS-001, EVENTBUS-002, and CI-003 full entries in `docs/00_governance_03_issue-and-uncertainty-management.md` with prose placeholders, removing undefined Status values and converging on the single retained convention.

## Scope

- Replace EVENTBUS-001 entry (lines ~168-181) with a prose placeholder citing collision-detection evidence and residual-risk note.
- Replace EVENTBUS-002 entry (lines ~183-202) with a prose placeholder per Option A, naming the resolution date and `docs/eventbus/03_replay_operations.md` as the specifying document.
- Replace CI-003 entry (lines ~273-290) with a prose placeholder citing `test_apply_config_dict_exercises_real_registry_and_no_discovery_call` by name and preserving the `mcpagent04` re-evaluation trigger.
- Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` after all three edits and confirm it passes.

## Assumptions

- The three entries exist at approximately the line ranges specified in the Plan.
- The established prose-placeholder convention follows the pattern used by RAG-003, RAG-004, DESIGN-1, SHARED-001, EVENTBUS-008, CI-001, CI-004, CI-005, CI-006.
- All three entries are fully resolved and can be replaced without losing actionable information.

## Design decisions

- Use the existing prose-placeholder pattern verbatim — do not introduce a new format.
- Each placeholder must cite concrete evidence (resolution date, specific test/function name, etc.) so a future reader does not need Git history to understand why the entry was removed.
- Do not modify any other document — ADR-003's stale cross-reference is out of scope.

## Alternatives considered

- Creating a new "Resolved Entries" section — rejected because the Plan's intent is to use the existing prose-placeholder convention already established by nine other entries.

## Implementation
### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate the EVENTBUS-001 entry (approximately lines 168-181).
2. Replace the EVENTBUS-001 full entry with a prose placeholder following the established pattern.
3. Locate the EVENTBUS-002 entry (approximately lines 183-202).
4. Replace the EVENTBUS-002 full entry with a prose placeholder per Option A.
5. Locate the CI-003 entry (approximately lines 273-290).
6. Replace the CI-003 full entry with a prose placeholder citing the test by name.
7. Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm it passes.

### Method

#### EVENTBUS-001 Placeholder (replace lines ~168-181)

Current entry structure:
```markdown
- **EVENTBUS-001**: [full entry with Status: Mitigated, fields outside template]
```

Required replacement:
```markdown
**EVENTBUS-001**: Resolved. Collision detection via `ValueError` on duplicate offsets was implemented in `scripts/eventbus/db.py::migrate_legacy_offsets()` (confirmed: lines 578-656). Legacy migration only — the live ACK path is unaffected. Its absence from the active list is the correct, policy-compliant state — do not create a `#### EVENTBUS-001` heading.
```

#### EVENTBUS-002 Placeholder (replace lines ~183-202)

Current entry structure:
```markdown
- **EVENTBUS-002**: [full entry with Status: resolved, extra fields]
```

Required replacement:
```markdown
**EVENTBUS-002**: Resolved. Resolution confirmed by `docs/eventbus/03_replay_operations.md` (JSON response schema `{total, limit, offset, items}` confirmed: lines 44-66). Its absence from the active list is the correct, policy-compliant state — do not create a `#### EVENTBUS-002` heading.
```

#### CI-003 Placeholder (replace lines ~273-290)

Current entry structure:
```markdown
- **CI-003**: [full entry with Status: Mitigated, Recommended Action contradiction]
```

Required replacement:
```markdown
**CI-003**: Resolved. Resolution confirmed by `tests/agent/services/test_config_reload.py::test_apply_config_dict_exercises_real_registry_and_no_discovery_call` (confirmed: line 480). Re-evaluate if `mcpagent04` support is added. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-003` heading.
```

### Details

Each placeholder follows the same four-part structure:
1. "Resolved." statement
2. Evidence citation (specific function, test, or document with line references)
3. Contextual note (legacy migration only / re-evaluation trigger)
4. "Its absence from the active list is the correct, policy-compliant state — do not create a `#### {ID}` heading."

The exact line numbers should be verified at edit time against the current file content before making replacements.

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The placeholders preserve enough context from the original entries so that a future reader can understand why each was closed without consulting Git history.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If a placeholder is found to omit critical context, revert to the original entry and correct the placeholder text. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Documentation quality | `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` | Passes with no new findings |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual vocabulary re-scan | `grep -n "^\- \*\*Status\*\*:" docs/00_governance_03_issue-and-uncertainty-management.md` | Every line shows `open`, `investigating`, or `deferred` |
| `tests/agent/services/test_config_reload.py` | Existing unit test (evidentiary basis for CI-003) | `uv run pytest tests/agent/services/test_config_reload.py -k test_apply_config_dict_exercises_real_registry_and_no_discovery_call` | Passes |

## Completion criteria

- No entry in Part 1 of `docs/00_governance_03_issue-and-uncertainty-management.md` carries a `Status` value absent from `open`/`investigating`/`deferred`.
- No remaining full entry in Part 1 carries fields outside the 16-field template.
- `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` passes clean.
- `grep -n "^\- \*\*Status\*\*:" docs/00_governance_03_issue-and-uncertainty-management.md` confirms every remaining value is one of `open`, `investigating`, or `deferred`.

## Out of scope

- Amending `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`'s stale "Known Issues" cross-reference to CI-003 — recommended as a separate follow-up.
- Implementing `mcpagent04`.
- Changing `/replay` behavior or authoring its documentation.
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260915-200057_gov02_enforce-a-single-status-vocabulary-and-entry-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-150416_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-150416
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
