## Goal

Extend `tests/tools/test_check_docs_structure.py` so it covers the post-migration ADR
behaviour of `tools/check_docs_structure.py` (REQ-003 / AC-3): the new top-level ADR
structure (`## Related ADRs` + `## Implementation References`, no body `## Related
Documents`) is accepted; a reintroduced body `## Related Documents` block in an ADR is
reported; `related: []` is accepted; and the existing format/target/self-reference/
duplicate cases remain covered.

## Scope

- **In-Scope**: `tests/tools/test_check_docs_structure.py` — update `TestRelatedSectionRules`
  and `TestAdrRelatedCoverage`, add the new ADR-structure / `related: []` / reintroduced-block
  cases, and refresh the section banner comment. And the tool under test
  `tools/check_docs_structure.py` (its own row; the test changes are a delta on its change).
- **Out-of-Scope**: the other two tool test files; the tool source itself.

## Assumptions

- **rel001 has landed before these tests run.** The "reintroduced body block in an ADR is
  reported" behaviour comes from `rel001`'s extended any-level body-block detection; the
  current pre-`rel001` state does not report an ADR body block. Run this suite only after
  `rel001`'s `check_docs_structure.py` change is applied.
- `check_adr_related_coverage` is redesigned (see UNK-05, the `check_docs_structure.py` row)
  to scan body `.md` references rather than the removed `## Related Documents` section. The
  coverage tests must exercise the new scanning path.

## Design decisions

- Flip `TestRelatedSectionRules.test_adr_without_related_documents_is_reported`: an ADR
  without any Related Documents section now PASSES (the requirement is dropped).
- Add a case asserting an ADR that *does* carry a body `## Related Documents` block is
  reported (the extended detection).
- Add a case asserting the new top-level structure passes `check_tail_sections`.
- Add a `related: []` acceptance case via `validate_file` / `check_related_links`.
- Rewrite `TestAdrRelatedCoverage` fixtures to place the referenced document names as body
  `.md` references (backtick/link forms) rather than inside a `## Related Documents` block,
  matching the UNK-05 redesign.
- Update the banner comment at lines 626-628 ("ADR requires the block") to the new rule.

## Alternatives considered

- Leaving `test_adr_without_related_documents_is_reported` as-is — rejected: it would fail
  once the requirement is dropped; it must flip to "passes".
- Keeping the `## Related Documents` fixtures in `TestAdrRelatedCoverage` — rejected: they
  encode the removed section; the redesigned check scans the body, so fixtures must too.

## Implementation

### Target file

`tests/tools/test_check_docs_structure.py`

### Procedure

1. **Flip the ADR-missing assertion.** In `TestRelatedSectionRules`, change
   `test_adr_without_related_documents_is_reported` so an ADR without a body `## Related
   Documents` section asserts `check_tail_sections(...) == []` (it now passes).
2. **Add the reintroduced-block case.** In `TestRelatedSectionRules`, add
   `test_adr_with_body_related_documents_block_is_reported`: an ADR whose body contains a
   `## Related Documents` heading is reported (message references `## Related Documents`).
   Place the ADR under a `10_adr/` tmp path so `_is_adr()` matches.
3. **Add the new-structure-passes case.** In `TestRelatedSectionRules`, add
   `test_new_adr_structure_accepted`: an ADR with top-level `## Related ADRs` and `##
   Implementation References` (and no body `## Related Documents`) passes
   `check_tail_sections(...) == []`.
4. **Add the `related: []` case.** Add a test (e.g. in `TestBasenameIndexResolution` or a
   small new class) that builds an ADR with `related: []` and asserts
   `check_related_links(doc, text, index) == []` and that `validate_file(...)` reports no
   format error.
5. **Rewrite `TestAdrRelatedCoverage`.** Change `_ADR_BODY` / `_adr_content` so the
   referenced document names appear as body `.md` references (backtick `` `a.md` `` and link
   `[b](b.md)` forms) anywhere in the body instead of inside `## Related Documents`. Keep
   the four existing assertions (missing body reference reported; covered ADR passes;
   non-ADR skipped; bad YAML skipped) and the `validate_file` coverage-gap test, adjusting
   fixtures so the body references resolve through the redesigned scanner.
6. **Update the banner comment** (lines 626-628) from "ADR requires the block; non-ADR must
   use front matter" to reflect that no body Related Documents section is required and a
   reintroduced one is reported.

### Method

- Read `test_check_docs_structure.py` lines 626-713 (`TestRelatedSectionRules`,
  `TestAdrRelatedCoverage`) and the import block (lines 19-32).
- Apply steps 1-6.
- Run the suite after `rel001`'s `check_docs_structure.py` change lands.

### Details

- Current failing-to-flip line 643-644: `assert issues == ["ADR-001-x.md: missing '## Related Documents' section"]`.
- `check_tail_sections` signature: `check_tail_sections(doc: DocFile, content: str) -> list[str]`.
- `check_related_links` signature: `check_related_links(doc, text, index, check_duplicates=False) -> list[str]`.
- `check_adr_related_coverage` signature: `check_adr_related_coverage(adr, content, index) -> list[str]` — after UNK-05 it scans body `.md` references.
- Existing `_ADR_BODY` (lines 630-633) embeds `` `a.md` `` etc. inside `## Related Documents`; move those references into plain body text.

## Compatibility considerations

- These tests target `tools/check_docs_structure.py`; they must be updated together with
  that tool's change (same coordinated commit). Do not run them against the pre-`rel001`
  tool — the reintroduced-block case would not pass.

## Security considerations

N/A: test-only change.

## Rollback considerations

Revert `tests/tools/test_check_docs_structure.py` to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_check_docs_structure.py` | Unit: new ADR structure accepted, old block reported, `related: []` accepted, format/target/self-ref/dup | `uv run pytest tests/tools/test_check_docs_structure.py -q -p no:cacheprovider -p no:randomly` | New cases pass; existing cases still pass |
| Changed tool file | Static analysis | `uv run ruff` / `uv run mypy` / `uv run bandit` on `check_docs_structure.py` | Clean |

## Completion criteria

- An ADR without a body `## Related Documents` section passes; one with such a block is
  reported.
- The new top-level `## Related ADRs` / `## Implementation References` structure passes.
- `related: []` is accepted.
- `TestAdrRelatedCoverage` exercises the redesigned body-reference scan.
- Format/target/self-reference/duplicate cases still pass.

## Out of scope

- The other two tool test files; the tool source itself (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261007-144916 | 20261007-144916 | REQ-003 / AC-3 (after rel001) Archive as completed: required coverage fulfilled by rel001/rel002 commits (suite passes). Procedure steps diverged from landed implementation. |
| 2 | Add or update tests per Validation plan | Completed | 20261007-144916 | 20261007-144916 | test_check_docs_structure.py Coverage present in current tests; see Notes for step 1. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261007-144916 | 20261007-144916 | ruff/mypy/bandit + pytest Full suite EXIT=0 (8087 passed, 20 skipped). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261007-144916 | 20261007-144916 | N/A: no docs/00_index.md task-scope mapping for tests/tools/ |

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
- **Requirement ID**: `REQ-003` — new ADR structure accepted, reintroduced block reported, `related: []` accepted (AC-3)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `tests/tools/test_check_docs_structure.py`