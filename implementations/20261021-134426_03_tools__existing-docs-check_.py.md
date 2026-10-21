## Goal
Extend an existing docs checker with report-only (Warning) enumeration-generalization detection: flag removed list items (bullets, table rows, backtick identifiers) that have no counterpart in a docs diff's replacement text, so non-universal-word enumeration generalizations that drop a concrete requirement are caught mechanically.

## Scope
- Modify exactly one existing docs checker, named in Phase 1 after evaluating which tool is the correct extension point (UNK-02). The name is not fixed at plan-freeze time and is added to the Plan's `Implementation Target Files` before this row is implemented.
- Add report-only (Warning) detection only; introduce no blocking gate.
- Keep `tools/TOOL_DESCRIPTIONS.md` in sync if the tool's documented capability changes.

## Assumptions
- The owner's decision is recorded before this executes (Plan REQ-001); this procedure documents the "mechanical" branch so it can be applied once decided.
- The routing policy ("extend the existing tool, do not write a new one-off script") and `AGENTS.md` Global Rule 7 hold; if they do not, this row is out of scope until the Plan is amended.
- A low-value/high-false-positive result on a real diff supports recording an accepted limit instead (the `docs/00_governance/governance_04_documentation-checks.md` row).

## Design decisions
- Extend the selected existing docs tool rather than adding a new one-off script (routing.md "When to run which tool"; AGENTS.md Global Rule 7).
- Start report-only (Warning) and require passing on the current corpus (Constraints).

## Alternatives considered
- Recording an accepted limit + manual step instead: out of scope for this row — that is the `prompts/08_document-sync.md` and `docs/00_governance/governance_04_documentation-checks.md` rows.
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`tools/<existing-docs-check>.py` (name selected in Phase 1; see Method)

### Procedure
1. Confirm the owner's decision is recorded (REQ-001). If absent, stop and report; do not infer.
2. Phase 1 selection (UNK-02): evaluate the mechanical approach on a real past docs diff; record the false-positive and miss rate. Select the existing docs tool to extend and add it to the Plan's `Implementation Target Files` before implementing this row.
3. Add report-only (Warning) detection of removed list items with no counterpart in the replacement text.
4. Add unit tests with a fixture diff containing a generalization without universal wording.
5. Pass lint, type check, and bandit; update `tools/TOOL_DESCRIPTIONS.md` if the documented capability changed.

### Method
- Identify the correct extension point among the existing docs checkers (see `routing.md` canonical tool inventory). The generic diff/compression comparison, if any, is the preferred hook; otherwise add a new report-only check function to the selected tool.
- Implement: for a docs diff, collect removed list items (bullets, table rows, backtick identifiers) and flag any removed item with no textual counterpart in the replacement text, emitted at Warning level.
- Do not introduce a blocking gate; the check must pass (no failures) on the current corpus.

### Details
- Verified at planning time: no `tools/*.py` currently implements the universal-word heuristic or any enumeration-generalization check; the gap is "no mechanism exists", not a weak heuristic.
- The exact tool path is unknown until Phase 1; until it is added to the Plan's `Implementation Target Files`, this row names the placeholder `tools/<existing-docs-check>.py`. If implementing requires a file not listed in `Implementation Target Files`, that is an additional-target-file discovery — stop and report `Blocked` per the workflow.

## Compatibility considerations
- The tool is used by CI/pre-commit; `tools/TOOL_DESCRIPTIONS.md` must stay in sync, and the check must not fail on the existing corpus.

## Security considerations
Report-only (Warning) detection over local docs diffs; no secrets, network, or access changes.

## Rollback considerations
Revert the commit that edits the selected tool and its tests; revert the `TOOL_DESCRIPTIONS.md` update if present.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Extended docs checker | Live baseline + fixture diff | `uv run python tools/<checker>.py`; unit test with a non-universal-word generalization fixture | Report-only (Warning); passes on current corpus |
| Changed tool | Lint / type / security | `uv run ruff check`, `uv run mypy`, `uv run bandit` | Pass |
| `tools/TOOL_DESCRIPTIONS.md` | Tool-description sync | `uv run python tools/check_tool_descriptions_sync.py` | Pass |

## Completion criteria
- The selected existing docs checker reports (Warning) enumeration generalizations with no counterpart in the replacement text.
- Fixture-diff unit test covers a non-universal-word generalization; live runs pass on the current corpus.
- `ruff`, `mypy`, `bandit` pass; `check_tool_descriptions_sync.py` passes if the tool description changed.
- No blocking gate introduced.

## Out of Scope
- Adding a new one-off script against the routing policy.
- Introducing a blocking gate.
- Editing any `docs/` content in the same change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Select the existing docs tool to extend (UNK-02) via a real-diff FP/miss evaluation | Pending | — | — | Added to Plan Implementation Target Files before implementing this row |
| 2 | Add report-only (Warning) enumeration-generalization detection + fixture tests | Pending | — | — | Branch selected by owner decision (REQ-001) |
| 3 | Run lint/type/bandit and `check_tool_descriptions_sync.py` | Pending | — | — | Depends on step 2 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (mechanical / manual / record-limit) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (evaluate on a real diff; record FP/miss rate) and `REQ-003` (extend the existing tool with report-only detection) — add enumeration-generalization detection to an existing docs checker
- **Source issue**: `issues/20261021-100336_compressverify_detect-enumeration-generalization-without-universal-wording-after-docs-compression.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-124107_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-134426
- **Related target files**: `tools/<existing-docs-check>.py`
