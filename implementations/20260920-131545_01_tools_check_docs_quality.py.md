## Goal
Add a cross-file section comparison pass to `check_content_similarity` in
`tools/check_docs_quality.py` (REQ-001), so a section copied verbatim into
a second document is flagged, while leaving the existing within-file pass's
code, output, and message format byte-for-byte unmodified. Add a scoped
noise mitigation (REQ-003) only if the mandatory full-tree review (Step 2 of
this document's Execution Status) finds one is actually needed.

## Scope
In scope: `check_content_similarity` (lines 484-512) only — add a second,
independent loop after the existing within-file loop; do not touch the
existing loop's lines at all. Out of scope: any other function in this
file, `_extract_sections`, `_compute_section_similarity` (reused
unchanged), and `check_docs_content_policy.py`.

## Assumptions
Per Plan Design: keeping the existing within-file loop's source lines
completely untouched (not even adding a caching side-effect inside it) is
worth the minor cost of a second file-read+section-extraction pass for the
new cross-file loop, since it makes the "existing output is unchanged"
guarantee structural rather than something that must be verified by
careful review of a shared/modified loop.

## Design decisions
Add a second, fully separate loop after the existing within-file loop's
`return issues` is NOT yet reached — i.e., insert the new loop between the
existing loop and the function's final `return issues` statement. The new
loop: (1) builds its own `doc_sections: list[tuple[DocFile, list[dict]]]`
by re-reading each file and calling `_extract_sections` again (accepted,
negligible re-parse cost — see Plan Design's performance rationale); (2)
compares every section of `doc_sections[a]` against every section of
`doc_sections[b]` for all `a < b` (each unordered file pair considered
exactly once); (3) reuses `_compute_section_similarity` with its default
threshold, unchanged; (4) reports a finding at `doc_b`'s section line,
naming both files and both headings, distinguishing the message from the
within-file format.

## Alternatives considered
- Caching `sections` from the existing loop via a side-effect line added
  inside it — rejected per Plan Assumptions: the current design (a fully
  separate second pass) makes "the existing loop is unmodified" a property
  of the diff itself, not something a reviewer must reason about
  separately; the minor extra re-parse cost is acceptable at this corpus's
  size (Plan baseline: ~1.87s for the whole tool).
- Comparing all sections against all sections in one triple-nested loop
  (docs × docs × sections) without the `a < b` ordering guard — rejected:
  would produce each cross-file pair twice (once as `(a,b)`, once as
  `(b,a)`), doubling findings for the same pair with no added value.

## Implementation
### Target file
tools/check_docs_quality.py

### Procedure
1. Locate `check_content_similarity` (confirmed at line 488) and its
   existing `return issues` (confirmed at line 512).
2. Insert, between the end of the existing `for doc in files:` loop and the
   `return issues` line, the following new code:
   ```python
   doc_sections: list[tuple[DocFile, list[dict]]] = []
   for doc in files:
       try:
           content = doc.path.read_text(encoding="utf-8")
       except OSError:
           continue
       doc_sections.append((doc, _extract_sections(content)))

   for a in range(len(doc_sections)):
       doc_a, sections_a = doc_sections[a]
       for b in range(a + 1, len(doc_sections)):
           doc_b, sections_b = doc_sections[b]
           for sec_a in sections_a:
               if not sec_a["body"]:
                   continue
               for sec_b in sections_b:
                   if not sec_b["body"]:
                       continue
                   if _compute_section_similarity(sec_a["body"], sec_b["body"]):
                       issues.append(
                           Issue(
                               doc_b.rel_path,
                               sec_b["line"],
                               "WARNING",
                               f"Content similarity detected between "
                               f"{doc_a.rel_path}#'{sec_a['heading']}' and "
                               f"{doc_b.rel_path}#'{sec_b['heading']}'",
                           )
                       )
   ```
3. Update the function's docstring to mention the new cross-file
   capability, e.g. append: `"Also flags sections across different
   documents whose body text overlaps above the same threshold (e.g. a
   governance rule copied verbatim into a second document — see
   docs/00_governance_01_documentation-policy.md's 'Merge Conditions' vs.
   docs/00_governance_04_documentation-checks.md's 'Merge Condition
   Validation' for a confirmed real-world example)."`
4. **Mandatory full-tree review** (not a code edit): run `uv run python
   tools/check_docs_quality.py` against the full `docs/` tree. Confirm the
   within-file finding count is still 206 (Plan AC-2) and the 3 confirmed
   governance sections now produce a cross-file finding (Plan AC-1).
   Manually review the full new cross-file finding list for noise (Plan
   UNK-01) — count how many findings look like genuine rule duplication
   vs. generically-similar-by-design content (e.g. repeated "Related
   Documents"/"Keywords" sections, boilerplate scaffolding).
5. **Conditional mitigation** (REQ-003 — only if step 4's review finds the
   noise level unacceptable): add a small heading-name exclusion check
   inside the new loop's `sec_a`/`sec_b` iteration, e.g.:
   ```python
   _GENERIC_HEADING_DENYLIST = frozenset({"related documents", "keywords"})
   ...
   for sec_a in sections_a:
       if not sec_a["body"] or sec_a["heading"].strip().lower() in _GENERIC_HEADING_DENYLIST:
           continue
       ...
   ```
   Choose the exact denylist entries (or a minimum-body-length filter
   instead/in addition) based on what step 4's actual review found — do
   not add this speculatively if step 4's noise level is already
   acceptable. Record the outcome (mitigation added, or "no mitigation
   needed") in this document's Execution Status Notes for Step 1.

### Method
One `Edit` call for the new loop insertion (step 2), one `Edit` call for
the docstring update (step 3) — both independently revertable. Steps 4-5
are verification/conditional-implementation actions, not a single
predetermined Edit — step 5's exact diff depends on step 4's findings.

### Details
Do not modify the existing within-file loop (lines 494-510 approximately,
the `for doc in files: ... for i in range(len(sections)): for j in
range(i+1, len(sections)): ...` block) in any way — not even to add a
caching side-effect, per Design decisions. Do not modify `_extract_sections`
or `_compute_section_similarity`. Do not modify any other `check_*`
function or `main()`'s registration list (`check_content_similarity` is
already registered via `@register_core_check` and needs no re-registration
for this additive capability).

## Compatibility considerations
Report-only (`WARNING` severity), consistent with the existing
registration. No change to the tool's CLI or exit-code behavior. This is
not a public API in the runtime sense — a standalone report-only script.

## Security considerations
N/A: pure text scanning of local Markdown files, no external input, no code
execution, no secret-handling path.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit
reverting the Method edits — no data migration or state change is
involved. The new loop and the conditional mitigation (if added) are each
independently revertable without affecting the existing within-file loop.

## Validation plan
- `uv run python tools/check_docs_quality.py` full-tree (Plan AC-1, AC-2,
  UNK-01 — see Procedure step 4).
- `time uv run python tools/check_docs_quality.py` full-tree (Plan AC-3 —
  compare against the ~1.87s baseline).
- `uv run ruff format tools/check_docs_quality.py`, `uv run ruff check
  tools/check_docs_quality.py`, `uv run mypy tools/check_docs_quality.py`.
- `uv run radon cc tools/check_docs_quality.py -s`, `uv run vulture
  tools/check_docs_quality.py --min-confidence 80`, `uv run bandit
  tools/check_docs_quality.py` — compare `check_content_similarity`'s
  complexity grade against the Plan's baseline (currently B(8); some
  increase is expected and acceptable given the added loop, per Plan
  Validation plan's "does not regress unreasonably" framing, not a fixed
  numeric ceiling).
- See the sibling test-file procedure for unit-test-level validation.

## Completion criteria
The new cross-file loop exists, is additive relative to the untouched
within-file loop, and is wired with no separate registration step needed;
running the tool produces the Plan's expected findings (AC-1, AC-2) with no
material performance regression (AC-3); `ruff`/`mypy`/`radon`/`vulture`/
`bandit` report no new issue beyond an expected, reasonable complexity
increase.

## Out of scope
- The 2-3 unit tests for the cross-file path and the extended regression
  test — tracked in the sibling
  `tests/tools/test_check_docs_quality.py` procedure document (REQ-002).
- Any `docs/*.md` file edit to fix a finding this extended check produces.
- `check_docs_content_policy.py` and `tools/TOOL_DESCRIPTIONS.md`.

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
- **Requirement ID**: `REQ-001`, `REQ-003` — cross-file comparison pass and conditional mitigation
- **Source issue**: issues/20260920-115531_docdup01tool_detect-cross-file-section-duplication-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-121316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-131545
- **Related target files**: tools/check_docs_quality.py
