## Goal
Fix `REQ-002`: extend `tools/check_compat_shims.py` with an ADR-ID-keyed prohibited-pattern
table, so a pattern an Accepted ADR explicitly prohibits is flagged when found in `scripts/`.

## Scope
Modify exactly `tools/check_compat_shims.py`: add a new ADR-scoped pattern table and a
check function that runs it, alongside (not replacing) the existing `COMPAT_PATTERNS`/
`check_compat_patterns()`. No other file is modified by this row.

## Assumptions
- At least one real, literal prohibition exists in Accepted ADR text that can be seeded now
  without speculation: ADR-001 states (confirmed by reading
  `docs/adr/ADR-001-workflow-engine-mandatory.md` lines 47-48) "Workflow無効化モードを設けない"
  (no workflow-disable mode) and "Workflowを迂回する直接実行経路を設けない" (no direct
  execution path bypassing Workflow) — these are Decision-level prohibitions, not
  aspirational language, and are the first candidate for the seeded table.
- Per the Plan's Implementation intent §2 ("Seed the table only from patterns an implementer
  can point at in ADR text, not speculative rules"): identifying the concrete *code* pattern
  name/regex that would violate ADR-001's prohibition (e.g. a config flag or code path name
  actually used in `scripts/` for bypassing Workflow, if one is ever introduced) is
  implementation work for this row, not pre-decided by this document — do not invent a
  regex without first checking whether `scripts/` already has terminology to anchor it to
  (e.g. `rg -i "skip.?workflow|bypass.?workflow|workflow.?disable"` scripts/ as a starting
  search), and document the ADR passage the seeded pattern maps to.

## Design decisions
Per `skills/DESIGN.md` Avoid implementation-reference duplication: reuse
`COMPAT_PATTERNS`'s existing dict-of-`{name: regex}` shape and `check_compat_patterns()`'s
line-by-line scan/allowlist logic — add a second, ADR-keyed dict (e.g.
`ADR_PROHIBITED_PATTERNS: dict[str, tuple[str, str]]` mapping a pattern name to
`(adr_id, regex)`) and a sibling check function, rather than conflating the two pattern
families into one dict (their failure messages need to cite different things: a
compat-cleanup rationale vs. an ADR ID and its cited passage).

## Alternatives considered
- A separate sibling tool (`tools/check_adr_prohibited_patterns.py`) instead of extending
  `check_compat_shims.py`: the Plan's own Implementation intent explicitly allows either
  ("extend `check_compat_shims.py` (or add a sibling tool)"); extending is chosen here since
  the file-scan/allowlist infrastructure is identical and a second near-duplicate scanner
  would violate `skills/DESIGN.md` Avoid implementation-reference duplication.

## Implementation
### Target file
`tools/check_compat_shims.py`

### Procedure
Add an ADR-scoped prohibited-pattern table and a check function that scans `scripts/` for
matches, reporting the ADR ID and pattern name on a hit — wired into the same `main()`/
`check_all()` entry point as the existing compat-pattern check.

### Method
1. Confirm at least one seedable pattern by re-reading the cited ADR-001 passage in full
   context (not just the two-line Decision bullets) and searching `scripts/` for any
   existing terminology that would anchor a literal regex (per Assumptions).
2. Add `ADR_PROHIBITED_PATTERNS` alongside the existing `COMPAT_PATTERNS`, keyed by pattern
   name, each entry carrying its source ADR ID.
3. Add `check_adr_prohibited_patterns(content, filepath, allowlist) -> list[str]`, mirroring
   `check_compat_patterns()`'s structure (line-by-line scan, allowlist check, one issue
   string per match) but citing the ADR ID in the issue message.
4. Wire the new check into `check_all()` alongside `check_compat_patterns()`.

### Details
- `check_compat_patterns()` (`tools/check_compat_shims.py` line 153) and `COMPAT_PATTERNS`
  (line 24) were re-read in full; the new function mirrors this structure exactly, changing
  only the pattern source and issue-message format (ADR ID instead of a bare pattern name).
- No Plan-level inconsistency was found for this row.

## Compatibility considerations
Additive change to `tools/check_compat_shims.py` — the existing `COMPAT_PATTERNS`/
`check_compat_patterns()`/`check_all()` behavior for the current compat-cleanup patterns is
unchanged; the new check runs alongside it.

## Security considerations
Read-only static pattern-matching against `scripts/` source text; no code execution.

## Rollback considerations
Trivially revertable: remove the added dict and function, and the `check_all()` wiring line.
No other file depends on this addition until the `.pre-commit-config.yaml` row is
implemented.

## Validation plan
- `uv run python tools/check_compat_shims.py` against the current repository — expect zero
  false positives (no seeded pattern currently present in `scripts/`, confirmed by the
  search in Method step 1).
- `uv run pytest tests/tools/test_check_compat_shims.py -v` — add a case asserting the new
  ADR-scoped check fires on a synthetic match and is silent otherwise, alongside existing
  `COMPAT_PATTERNS` test cases.

## Completion criteria
The extended tool flags a seeded ADR-prohibited pattern when present in `scripts/`, cites
the ADR ID in its output, and produces zero false positives against current, correct
content; the existing compat-pattern check's behavior is unchanged.

## Out of scope
`tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`,
`.pre-commit-config.yaml`, `.github/workflows/ci.yml`,
`docs/00_governance_04_documentation-checks.md` — each covered by its own implementation
procedure document for this same Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm a seedable ADR-001 pattern via `scripts/` search | Pending | — | — | |
| 2 | Add `ADR_PROHIBITED_PATTERNS` and check function | Pending | — | — | |
| 3 | Add tests under `tests/tools/` | Pending | — | — | |
| 4 | Run against live repository; confirm zero false positives | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (Per-ADR prohibited-pattern registry)
- **Source issue**: `issues/20260901-183941_gv014ci_adr-compliance-ci-check-for-gv-014.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-220712_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-111416
- **Related target files**: `tools/check_compat_shims.py`
