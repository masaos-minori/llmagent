## Goal
- Reference the unchanged-since skip in Step 3a of `skills/code-implementation/workflow.md`, size neutral (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the edits below in this one file. Out of scope: any other section, and `tools/check_skill_size_baseline.txt` (no ceiling is raised).

## Assumptions
- Verified in Step 3a: the file is 42113 B against its ceiling 42118 B; Step 3a starts at "### Step 3a: Verify the procedure's claims (adversarial verification)". The edit set below was applied to a copy and measured: 42113 B now, 42113 B after, so the file stays within its ceiling.
- Every old text below was checked to occur exactly once in the file. Procedure 01 creates the tool before this document runs (`seq` order).

## Design decisions
- Only redundant wording is tightened and no rule is removed; the added text is the shortest form that states the skip and names the tool (Plan D-4, D-6).

## Alternatives considered
- Raise the ceiling: rejected, the baseline only shrinks. Put the text in an edge file: not a Plan target.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Record `wc -c skills/code-implementation/workflow.md` (42113 expected).
2. Apply each edit below: replace the old text (copied exactly, line breaks as in the file) with the new text.
3. Run `wc -c` again: the size MUST be at most 42118 B (the ceiling; about 42113 B is expected); if it is larger, tighten another repeated phrase in the same file without changing a rule, or stop and report (do not raise the ceiling).
4. Re-read the changed section once to confirm every rule is intact.

Edit 1, old text:

```text
inconsistent with a sibling procedure document or the source Plan. See `rules/ai-execution.md`, section "Tool Usage".
```

new text:

```text
inconsistent with a sibling procedure or the source Plan. See `rules/ai-execution.md`, section "Tool Usage". Apply its unchanged-since skip: `uv run python tools/check_evidence_freshness.py check {procedure_path}`.
```

Edit 2, old text:

```text
Step 2's stale detector already aborted on a missing symbol, import,
or cited line range, so this step covers what pattern matching cannot — check via
`rg`/Read whether the behavior, call path, and dependencies the procedure describes still
match current source, and whether any stated assumption or scope boundary is stale or
inconsistent with a sibling procedure document or the source Plan.
```

new text:

```text
Step 2's stale detector already aborted on a missing symbol, import, or cited line range,
so this step covers what pattern matching cannot — check via `rg`/Read whether the
behavior, call path, and dependencies the procedure describes still match current source,
and whether any assumption or scope boundary is stale or inconsistent with a sibling
procedure or the source Plan.
```

Edit 3, old text:

```text
If adversarial verification, or the implementation itself, reveals that the current
file's required change conflicts with, or invalidates an assumption of, an
already-processed file's change in the same Multi-file-processing batch, stop and
report `Blocked: cross-file conflict with {earlier file} — {description}` rather than
proceeding. MUST NOT implement around the conflict silently. This is a per-file `Blocked`
outcome, not a batch-wide stop — the current file's cycle ends here, its Execution
Status row for this Step is marked `Blocked`, and Multi-file processing continues per
its Dependency order rule (it does not stop the whole batch, but it does stop the
remaining procedures of the same Plan until the user decides).
```

new text:

```text
If adversarial verification, or the implementation itself, shows that the current file's
change conflicts with, or invalidates an assumption of, an already-processed file's change
in the same Multi-file-processing batch, stop and report `Blocked: cross-file conflict
with {earlier file} — {description}`; MUST NOT implement around it silently. This is a
per-file `Blocked` outcome, not a batch-wide stop — the current file's cycle ends here,
its Execution Status row for this Step is marked `Blocked`, and Multi-file processing
continues per its Dependency order rule (it stops only the remaining procedures of the
same Plan until the user decides).
```

### Method
- Exact-string edits only; no other line changes.

### Details
- The statement of the skip names `tools/check_evidence_freshness.py` so a stale-detector-style check can resolve it after procedure 01.

## Compatibility considerations
- The skip applies only when a Plan records an `Evidence revision`; Plans without one are verified in full as today.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py` (no ceiling raised); the pre-commit hook "Check skills/rules/prompts file references resolve" on commit; the documentation-only checkers of `rules/tool-gates.md` for the file.

## Completion criteria
- All edits are applied, the rules read as before plus the skip statement, and the size check passes.

## Out of Scope
- The tool, the template, and the other rule files (procedures 01 and 03 to 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261126-151439_wfeff004_evidence-sha-carryover.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-182520_wfeff004_evidence-sha-carryover.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-183845
- **Related target files**: `skills/code-implementation/workflow.md`
