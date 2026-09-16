## Goal

Fix `RAG-006`'s dangling `NC-026` reference and add a removal-placeholder-reference policy note to `docs/00_governance_03_issue-and-uncertainty-management.md`, since this Plan's own verification confirmed exactly one true dangling reference exists in the current document and the source issue's second claimed reference (`EVENTBUS-001 → EVENTBUS-003`) does not exist anywhere in the current document.

## Scope

- Correct `RAG-006`'s `Related: NC-026 (superseded — see Part 2 removal)` field — `NC-026` has no heading and no removal placeholder anywhere in Part 2 (confirmed dangling with no trace), so rewrite it to make the missing trace explicit rather than implying a verifiable placeholder exists.
- Document the removal-placeholder-reference policy in the governance document (state whether a `Related`/`Target` field may cite a removed entry's ID, and if so, require the removal-placeholder paragraph to exist and be named so the checker can classify it Warning rather than Blocking).

## Assumptions

- A systematic scan of every `Related`/`Related NC`/`Target` line against every heading ID and placeholder-prose ID found exactly one true dangling reference in the current document: `RAG-006`'s `Related: NC-026`.
- The source issue's claimed `EVENTBUS-001 → EVENTBUS-003` dangling reference does not exist anywhere in the current document: `grep -n "EVENTBUS-003"` returns zero matches, and EVENTBUS-001's full entry has no `Related` field at all.
- All other `Related` values either cite ADR document numbers (a different, file-existence-based validation excluded from this Plan) or resolve to an existing heading, including references to already-removed entries that do have a placeholder (e.g. `CI-009`'s `Related: CI-001`).

## Design decisions

- Rewrite `RAG-006`'s `Related` field to explicitly state that the cited ID cannot be resolved — neither as a heading nor as a removal placeholder — rather than leaving it as a misleading "superseded — see Part 2 removal" annotation.
- Add the removal-placeholder-reference policy as a brief prose note near the Part 1 closing summary where the closing-summary consistency check is described.

## Alternatives considered

- Leaving `RAG-006`'s `Related: NC-026` unchanged — rejected because the source issue's own rule (REQ-001(e)) requires this to be classified as Blocking, not silently left as a soft "superseded" annotation.

## Implementation
### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate `RAG-006`'s entry in Part 1 (approximately line 128-145 based on Reference Files evidence).
2. Find the `Related:` field within RAG-006's entry.
3. Replace `Related: NC-026 (superseded — see Part 2 removal)` with a statement that the cited ID cannot be resolved — neither as a heading nor as a removal placeholder.
4. Locate the Part 1 closing summary section (near the end of Part 1, after the last `#### ` heading).
5. Add a brief prose note documenting the removal-placeholder-reference policy before the closing summary sentence.

### Method

Current state: RAG-006's `Related:` field reads approximately:
```markdown
- **Related**: NC-026 (superseded — see Part 2 removal)
```

Required replacement:
```markdown
- **Related**: NC-026 — unresolved; no corresponding `#### NC-026` heading exists in Part 2 and no removal-placeholder paragraph naming NC-026 was found during this Plan's systematic scan.
```

The removal-placeholder-reference policy note should be added as a brief prose paragraph before the Part 1 closing summary sentence, stating something like:
```markdown
**Removal-placeholder-reference policy**: A `Related`/`Target` field may cite a removed entry's ID only when a removal-placeholder paragraph exists for that ID; without such a placeholder, the citation is treated as a dangling reference (Warning severity if the placeholder exists but no heading, Blocking if neither exists).
```

### Details

The exact wording of both changes should be reviewed against the current document structure at implementation time to ensure alignment with existing conventions. The policy note should be concise — one sentence — and placed immediately before the closing summary sentence so readers encounter it while reading about closing-summary consistency.

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The policy note cross-references the new conformance checker's referential-integrity rules — proper ownership routing via the Governance Verification Matrix.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If the policy note is found to duplicate an existing convention, simply remove it. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Documentation structural check | `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` | Passes with no new findings |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Needs Confirmation registry check | `uv run python tools/check_needs_confirmation_inventory.py` | Passes; NC-036 correctly registered |
| `tests/rag/test_rag_pipeline_service.py` | Existing unit test (evidentiary basis for NC-036's Evidence field) | `uv run pytest tests/rag/test_rag_pipeline_service.py -k test_json_parse_error_calls_set_fallback_reason` | Passes |

## Completion criteria

- Exactly one tracking entry exists (NC-036), and ADR-010 was not amended.
- The entry cites ADR-010 Decision #9, `scripts/rag/pipeline_service.py::call_rag_service()`, and `test_json_parse_error_calls_set_fallback_reason` by name.
- The entry has a named owner (@data-eng, not Unassigned).
- No behavior change was made to the RAG fallback path.
- `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` passes clean.
- `uv run python tools/check_needs_confirmation_inventory.py` passes; NC-036 correctly registered.

## Out of scope

- Amending `docs/adr/ADR-010-rag-fallback.md` — this Plan's own investigation found the "intentional vs. unintended" classification genuinely ambiguous, requiring owner/architect input.
- Registering a Part 1 Known Issue (document-code-mismatch) — not taken for the same reason.
- Changing `scripts/rag/pipeline_service.py::call_rag_service()` or its tests.
- Revisiting CI-004's closure.
- Reviewing other ADR-010 decisions.

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260915-200449_gov03_add-conformance-and-referential-integrity-checks-for-the-issue-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-151710_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-151710
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
