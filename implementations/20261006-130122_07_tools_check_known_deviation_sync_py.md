## Goal

Stop `tools/check_known_deviation_sync.py` from parsing the `## Related Documents` ->
`### Known Issues` subsection, after confirming no Known Issue ID lives only in that
subsection, and update its docstrings (`REQ-004`: the tool reports the same findings
before and after for the Known Issue IDs cited in `## Known Deviations`; the `### Known
Issues` subsection is no longer parsed; AC-4).

## Scope

- **In-Scope**: `tools/check_known_deviation_sync.py` — drop the `### Known Issues`
  subsection parsing in `parse_adr_references`, update the module docstring and the
  inline comment referencing the subsection, and remove the now-dead `signal is None`
  branch in `cross_check`. And its test file `tests/tools/test_check_known_deviation_sync.py`
  (its own row).
- **Out-of-Scope**: the 20 ADR bodies; other tools.

## Assumptions

- **UNK-03 confirmed before editing.** A scan found no Known Issue ID that lives only in
  an old `### Known Issues` subsection (only ADR-name-shaped tokens). This step MUST
  re-run the tool before and after to prove findings are unchanged (AC-4).
- `## Known Deviations` remains the sole source of Known Issue IDs with a resolved/open
  signal.

## Design decisions

- Remove the `### Known Issues` block from `parse_adr_references` so only `## Known
  Deviations` bullets are parsed (they carry the `resolved-like`/`open-like` signal).
- Remove the now-unreachable `if ref.signal is None: continue  # Related Documents
  mention: dangling check only.` branch in `cross_check`, since no parsed ref will carry
  `signal=None` anymore.
- Update the module docstring (which describes parsing both sections) and the inline
  comment at the signal-handling site.

## Alternatives considered

- Keeping the subsection parsing but neutralizing it — rejected: the plan requires the
  subsection to no longer be parsed; leaving dead parse code contradicts the change.

## Implementation

### Target file

`tools/check_known_deviation_sync.py`

### Procedure

1. **Baseline run.** Run `uv run python tools/check_known_deviation_sync.py` and record
   its findings (file, line, ID, severity). This is the "before" evidence for AC-4.
2. **Confirm no sole-cited ID.** Verify none of the baseline findings depends on an ID
   that appears ONLY in a `### Known Issues` subsection. (UNK-03 scan already found none;
   the before/after comparison in step 6 is the proof.)
3. **Drop the subsection parsing.** In `parse_adr_references` (current lines 316-329),
   remove the `known_issues = _section_body(doc.lines, "### Known Issues", 3)` block and
   its reference-append loop. Keep the `## Known Deviations` block (lines 291-314)
   unchanged.
4. **Remove the dead signal branch.** In `cross_check` (current lines 359-360), remove
   the `if ref.signal is None: continue` branch (now unreachable) and its comment.
5. **Update docstrings/comments.** Update the module docstring (current lines 4-5, which
   describe parsing `## Known Deviations` AND the `### Known Issues` subsection) to
   describe only `## Known Deviations`. Remove/adjust the inline comment at the former
   signal-handling site (line 124 area) that references the subsection.
6. **After run.** Re-run `uv run python tools/check_known_deviation_sync.py` and confirm
   the findings are IDENTICAL to the baseline run (AC-4). Any difference means an ID lived
   only in the removed subsection — move it to `## Known Deviations` first (per the plan)
   and re-run.

### Method

- Read `check_known_deviation_sync.py`: module docstring (lines 1-12),
  `parse_adr_references` (lines 285-330), `cross_check` (lines 338-375).
- Perform steps 3-5.
- Run the tool before (step 1) and after (step 6); diff the outputs.

### Details

- `parse_adr_references` currently appends `AdrReference(..., section="Related Documents
  > Known Issues", signal=None)` for the subsection; remove that path.
- `cross_check` line 359-360: `if ref.signal is None:\n    continue  # Related Documents
  mention: dangling check only.` — remove.

## Compatibility considerations

- Callers: CI, `.pre-commit-config.yaml`, `tests/tools/`. No production-runtime import.
- `governance_04` documents this tool (its own row); keep its description consistent
  (drop the `### Known Issues` reference).

## Security considerations

N/A: static documentation-checker behavior change.

## Rollback considerations

Revert `tools/check_known_deviation_sync.py` (and its test file) to the pre-this-change
commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `check_known_deviation_sync.py` | Before/after equivalence | Run the tool before (step 1) and after (step 6); diff output | Findings identical; no newly-dangling `## Known Deviations` ID |
| `check_known_deviation_sync.py` | Unit: `## Known Deviations` handling unchanged | `uv run pytest tests/tools/test_check_known_deviation_sync.py -q -p no:cacheprovider -p no:randomly` | Passes |
| Changed tool file | Static analysis | `uv run ruff format` / `uv run ruff check --fix` / `uv run mypy` / `uv run bandit` | Clean |

## Completion criteria

- `parse_adr_references` parses only `## Known Deviations`; the `### Known Issues`
  subsection is no longer parsed.
- The before/after tool runs produce identical findings (AC-4).
- Docstrings no longer describe parsing the subsection.
- Unit tests and static analysis pass.

## Out of scope

- The 20 ADR bodies; other tools; `governance_04` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-004 / AC-4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | test_check_known_deviation_sync.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy/bandit + pytest |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | governance_04 description (separate row) |

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
- **Requirement ID**: `REQ-004` — `check_known_deviation_sync.py` reports identical findings before/after; `### Known Issues` no longer parsed (AC-4)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `tools/check_known_deviation_sync.py`
