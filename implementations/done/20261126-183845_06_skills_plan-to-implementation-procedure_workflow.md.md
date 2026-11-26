## Goal
- Reference the unchanged-since skip in Step 3a of `skills/plan-to-implementation-procedure/workflow.md`, size neutral (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the edits below in this one file. Out of scope: any other section, and `tools/check_skill_size_baseline.txt` (no ceiling is raised).

## Assumptions
- Verified in Step 3a: the file is 34876 B, equal to its ceiling; Step 3a starts at "### Step 3a: Verify the Plan's claims (adversarial verification)". The edit set below was applied to a copy and measured: 34876 B now, 34853 B after, so the file stays within its ceiling.
- Every old text below was checked to occur exactly once in the file. Procedure 01 creates the tool before this document runs (`seq` order).

## Design decisions
- Only redundant wording is tightened and no rule is removed; the added text is the shortest form that states the skip and names the tool (Plan D-4, D-6).

## Alternatives considered
- Raise the ceiling: rejected, the baseline only shrinks. Put the text in an edge file: not a Plan target.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Record `wc -c skills/plan-to-implementation-procedure/workflow.md` (34876 expected).
2. Apply each edit below: replace the old text (copied exactly, line breaks as in the file) with the new text.
3. Run `wc -c` again: the size MUST be at most 34876 B (the ceiling; about 34853 B is expected); if it is larger, tighten another repeated phrase in the same file without changing a rule, or stop and report (do not raise the ceiling).
4. Re-read the changed section once to confirm every rule is intact.

Edit 1, old text:

```text
Background never checked — verifying each via `rg`/Read. See `rules/ai-execution.md`,
section "Tool Usage".
```

new text:

```text
Background never checked — verifying each via `rg`/Read. See `rules/ai-execution.md`,
section "Tool Usage". Apply its unchanged-since skip: `uv run python tools/check_evidence_freshness.py check {plan_path}`.
```

Edit 2, old text:

```text
If this correction is made while processing row K (K > 1), check whether any
already-generated document for rows 1..K-1 relied on the now-corrected claim. If one
does: amend that earlier document in the same cycle when the fix is bounded and does
not require re-investigating that row's dependencies or tests; otherwise, flag it in
the progress report and the Plan's Execution Status as needing re-verification before
Step 4's move — MUST NOT silently leave a stale earlier document unflagged. Scope this
check to the corrected claim only, not a full re-verification of every prior row.
```

new text:

```text
If this correction is made while processing row K (K > 1), check whether any document
already generated for rows 1..K-1 relied on the corrected claim. If one did: amend it in
the same cycle when the fix is bounded and needs no re-investigation of that row's
dependencies or tests; otherwise flag it in the progress report and the Plan's Execution
Status as needing re-verification before Step 4's move — MUST NOT silently leave it stale.
Scope this check to the corrected claim, not a full re-verification of every prior row.
```

Edit 3, old text:

```text
If this correction requires reverting a prior edit to `plans/{filename}.md`, see
`rules/workflow-lifecycle.md` Plan-Document Correction Handling for whether `AGENTS.md`
Rollback Directive applies (it does not) — and, if a revert is nonetheless performed,
see the timestamp-marker preservation requirement in Step 3b.
```

new text:

```text
To revert a prior edit to `plans/{filename}.md`, see `rules/workflow-lifecycle.md`
Plan-Document Correction Handling (`AGENTS.md` Rollback Directive does not apply) and, if a
revert is performed, the timestamp-marker preservation requirement in Step 3b.
```

Edit 4, old text:

```text
Treat the Plan's descriptions of current source-code behavior as claims (it may have gone stale since approval). Apply
`rules/ai-execution.md` Adversarial Verification (Base) before writing
Procedure/Method/Details for a row:
```

new text:

```text
Treat the Plan's descriptions of current source-code behavior as claims (they may have gone
stale since approval). Apply `rules/ai-execution.md` Adversarial Verification (Base) before
writing Procedure/Method/Details for a row:
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-185118 | 20261126-185118 | wfeff004: full suite 15778 passed, 3 failed (known tests/mcp_servers/git failures); dry run on a scratch copy of the wfeff003 Plan at revision 27a17cb51: unchanged 15, changed 9 |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` "When to run which tool" | Completed | 20261126-185118 | 20261126-185118 | wfeff004: full suite 15778 passed, 3 failed (known tests/mcp_servers/git failures); dry run on a scratch copy of the wfeff003 Plan at revision 27a17cb51: unchanged 15, changed 9 |

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
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
