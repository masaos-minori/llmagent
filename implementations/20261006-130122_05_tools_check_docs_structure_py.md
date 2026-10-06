## Goal

Change `tools/check_docs_structure.py` so that (1) ADRs no longer must carry a body
`## Related Documents` section, (2) a reintroduced body `## Related Documents` block is
reported in any document at any level, and (3) `check_adr_related_coverage` is redefined
to scan body `.md` references instead of the removed body block — without weakening any
existing check (`REQ-003`: the structure check no longer requires `## Related Documents`
for ADRs, reports a reintroduced body block in an ADR at any level, validates the
`related` format, and leaves no check weakened; AC-3).

## Scope

- **In-Scope**: `tools/check_docs_structure.py` (drop the ADR requirement, extend
  body-block detection to ADRs, redefine `check_adr_related_coverage`, update docstrings)
  and its test file `tests/tools/test_check_docs_structure.py` (its own row).
- **Out-of-Scope**: `tools/manage_frontmatter.py` and `tools/check_docs_quality.py`
  (Reference Files — read only, do not modify); the 20 ADR bodies; other tools.

## Assumptions

- **Prerequisite `rel001` has landed.** The current `check_docs_structure.py` is the
  pre-`rel001` state. `rel001` strengthens the body-block detection to catch a
  `## Related Documents`-type block at any nesting level. Every change below is a delta
  ON TOP OF `rel001`'s landed diff. `rel001` MUST be implemented and validated before
  this step (hard ordering dependency from the plan).
- `_is_adr()` (`"10_adr" in path.parts`) is unchanged and still used by
  `check_docs_quality.py`.
- `check_adr_related_coverage` stays meaningful because ADR bodies still reference
  documents via contextual prose (UNK-05).

## Design decisions

- In `check_tail_sections`, remove the `if _is_adr(path): <require ## Related Documents>
  else: <flag body block>` split. Replace it with a single body-block detection that runs
  for every document (ADR and non-ADR), reporting any body `## Related Documents` /
  `Related Docs` / `Related Chapters` heading at any level (using `rel001`'s
  strengthened detection). Keep the `## Keywords` presence check unchanged.
- Redefine `check_adr_related_coverage` to iterate `_BODY_REF_RE` over the whole body
  (front-matter-delimited) instead of scoping scans to `_RELATED_HEADING_RE` headings
  (there is no body block to delimit a section anymore). Coverage semantics are
  preserved: front matter `related:` must cover every document the ADR body references.
  Keep the check only while ADR bodies actually contain `.md` references (UNK-05).

## Alternatives considered

- Dropping `check_adr_related_coverage` entirely — rejected: UNK-05 recommends redefining
  it so coverage stays verifiable while ADR bodies reference documents.
- Weakening the check by only flagging self-references — rejected: AC-3 requires no check
  be weakened; format/target/self-ref/dup checks stay.

## Implementation

### Target file

`tools/check_docs_structure.py`

### Procedure

1. **Confirm `rel001` has landed first.** Do not start until `rel001` is implemented and
   its CI structure check passes. Verify the current file is post-`rel001` (the
   body-block detection already catches the block at any level for non-ADR docs).
2. **Drop the ADR requirement.** In `check_tail_sections` (current lines 196-198),
   remove the `if _is_adr(path): if not re.search(r"^## Related Documents", ...)`
   branch that emits `missing '## Related Documents' section`.
3. **Extend body-block detection to ADRs.** Replace the `else` branch (current lines
   199-204) so the body-block detection runs for ALL documents, not only non-ADR ones.
   Use the `rel001` strengthened detection (any level). Emit a message stating that no
   document may carry a body `## Related Documents`-type section and that cross-references
   belong in front matter `related:`. Keep the trailing `## Keywords` presence check
   (current lines 205-206) applying to every document.
4. **Redefine `check_adr_related_coverage`** (current lines 325-349+). Remove the
   `_RELATED_HEADING_RE.finditer(body)` heading loop and the per-heading `_BODY_REF_RE`
   scan bounded by the next `## ` heading. Instead, scan `_BODY_REF_RE` over the whole
   front-matter-delimited body once, collecting each referenced basename, and flag any
   referenced basename that is not in the `related:` `covered` set (same self-name and
   `basename_index` filters as now). If the body contains no `.md` references, return no
   missing entries.
5. **Update docstrings.** Update the module docstring and
   `check_adr_related_coverage`'s docstring to describe the body-reference scan instead of
   the removed body block.

### Method

- Read `check_docs_structure.py` lines 183-210 and 320-360 to confirm current structure
  (`_RELATED_HEADING_RE` at 184-186, `_BODY_REF_RE` at 187, `check_tail_sections` at
  194-207, `check_adr_related_coverage` at 325-349+).
- Make the four edits above.
- **Read (do not modify) Reference Files** to confirm no breakage: `tools/manage_frontmatter.py`
  (`_RELATED_HEADING_RE` + `merge-related` keep their own contract, unchanged) and
  `tools/check_docs_quality.py` (`_is_adr()` usage unaffected by the restructure).

### Details

- Current `check_tail_sections`:
  ```python
  if _is_adr(path):
      if not re.search(r"^## Related Documents", content, re.MULTILINE):
          issues.append(f"{path.name}: missing '## Related Documents' section")
  else:
      for match in _RELATED_HEADING_RE.finditer(strip_fenced_code(content)):
          issues.append(
              f"{path.name}: non-ADR document must not carry a body "
              f"'{match.group(0)}' section; use front matter 'related:'"
          )
  ```
  becomes a single detection path over `strip_fenced_code(content)` for every document.
- `check_adr_related_coverage` currently scopes each `_BODY_REF_RE` scan to the region
  between a `_RELATED_HEADING_RE` heading and the next `## ` heading; replace that with a
  single pass over the front-matter-delimited body.

## Compatibility considerations

- Callers: `.github/workflows/governance-docs-consistency.yml`, `.pre-commit-config.yaml`,
  `tests/tools/`. No production-runtime module imports the tool.
- `manage_frontmatter.py` and `check_docs_quality.py` are Reference Files — read to
  confirm consistency, do not modify them here.
- The CI structure check (made blocking by `rel001`) must still pass over the migrated
  ADRs (AC-6).

## Security considerations

N/A: static documentation-checker behavior change.

## Rollback considerations

Revert `tools/check_docs_structure.py` (and its test file) to the post-`rel001`,
pre-this-change commit. The change is additive to `rel001`; reverting restores the old
ADR requirement.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `check_docs_structure.py` | Unit: new ADR structure accepted, old `## Related Documents` block reported in an ADR at any level, fenced-code ignored, `related: []` accepted, format/target/self-ref/dup cases | `uv run pytest tests/tools/test_check_docs_structure.py -q -p no:cacheprovider -p no:randomly` | New cases pass; existing cases still pass |
| Changed tool file | Static analysis | `uv run ruff format` / `uv run ruff check --fix` / `uv run mypy` / `uv run bandit` (per `routing.md` "Adding a new tool") | Clean |
| Full docs-tooling suite | Integration | `uv run python tools/check_docs_structure.py` + `check_docs_quality.py` | Pass |

## Completion criteria

- `check_docs_structure.py` no longer requires `## Related Documents` for ADRs.
- A reintroduced body `## Related Documents` block in an ADR is reported at any level.
- `check_adr_related_coverage` covers documents referenced by the ADR body via `.md`
  references; no format/target/self-ref/dup check was removed or weakened.
- All unit tests and static analysis pass.

## Out of scope

- `manage_frontmatter.py`, `check_docs_quality.py` (read-only Reference Files).
- The 20 ADR bodies; other tools; the CI workflow file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-003 / AC-3 — implement rel001 first |
| 2 | Add or update tests per Validation plan | Pending | — | — | test_check_docs_structure.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy/bandit + pytest |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: `REQ-003` — `check_docs_structure.py` no longer requires `## Related Documents` for ADRs, reports a reintroduced body block at any level, weakens no check (AC-3)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `tools/check_docs_structure.py`
