## Goal
Close REQ-004's one remaining literal-fidelity gap: add a test case using a
literal `category:`-only front matter fixture (missing `area`) to
`tests/tools/test_check_docs_structure.py`, which already covers the
schema-validation behavior functionally but not with this exact fixture shape.

## Scope
- **In-Scope**: `tests/tools/test_check_docs_structure.py` — one new test
  method added to `TestSchemaComplianceRequiredFields`.
- **Out-of-Scope**: `tools/check_docs_structure.py` (already fully implements
  `check_schema_compliance()` — no code change needed, per this Plan's own
  2026-09-03 correction to REQ-001/002); `tools/TOOL_DESCRIPTIONS.md` (already
  documents `--schema` — no change needed, REQ-005); any of this test file's
  6 already-passing tests — unmodified by this row;
  `.github/workflows/governance-docs-consistency.yml` (seq 03 of this Plan).

## Assumptions
- `tests/tools/test_check_docs_structure.py` already exists (re-verified
  2026-09-03 by direct `Read`) with `TestSchemaComplianceRequiredFields` (3
  tests: compliant-passes, missing-required-field via omitted `related:`,
  missing-front-matter early-return) and `TestSchemaComplianceEnums` (3 tests:
  area-outside-enum, area-inside-enum, status-outside-enum) — added by commit
  `309a9ab10`, then separately extended the same day with `TestCheckSize` and
  `TestValidateFileSchemaOptIn` by an unrelated Plan's own implementation cycle
  (the `MAX_SIZE` raise). None of the existing 6+ tests use a literal
  `category:` key anywhere in a fixture.
- `check_schema_compliance()` has no `additionalProperties`-style check — it
  only checks `schema.required_fields` presence and enum membership (re-verified
  2026-09-03 by direct `Read` of `tools/check_docs_structure.py:90-131`) — so a
  fixture carrying `category: agent` with no `area:` key produces exactly the
  same "missing required 'area' field" finding as any other `area:`-less
  fixture; the new test's value is in matching REQ-004's exact named fixture
  shape, not in exercising new code paths.

## Design decisions
- **The new test is added to `TestSchemaComplianceRequiredFields`**, not a new
  class, since it exercises the same "required field presence" check path as
  that class's other two tests — it differs only in fixture content, not in
  which function or code path it targets.
- **The test asserts `"area" in i for i in issues` (checking the message
  mentions the missing field), not `len(issues) == 1`**, matching
  `test_missing_required_field_is_flagged`'s own assertion style exactly, for
  consistency within the same test class.
- **The docstring explains why this test exists despite testing behavior
  already covered generically** (per Assumptions: `category:`'s presence is
  irrelevant to the check's logic) — so a future reader does not mistake this
  for redundant test bloat; it exists specifically to close REQ-004's literal
  fixture-wording gap, not to add new coverage.

## Alternatives considered
- **Skip this addition entirely, treating the existing
  `test_missing_required_field_is_flagged` as sufficient proof of REQ-004's
  intent** — considered, rejected: REQ-004's own wording explicitly names "a
  `category:`-only block missing `area`" as one of the two required fixtures;
  since implementing this exact, cheap addition costs one small test method
  and closes the gap definitively, there is no reason to leave the literal
  wording unmet when the fix is this inexpensive.
- **Rewrite `test_missing_required_field_is_flagged` to use a `category:`-only
  fixture instead of adding a new test** — rejected: that would remove
  coverage for the "omitted `related:` field" case (a different, also-valid
  missing-required-field scenario) rather than adding coverage, net-reducing
  the file's test surface instead of closing a gap additively.

## Implementation
### Target file
`tests/tools/test_check_docs_structure.py`

### Procedure
1. Re-read the file in full immediately before editing to reconfirm no drift
   (done above; confirmed identical to this Plan's re-verified evidence).
2. Insert the new test method into `TestSchemaComplianceRequiredFields`,
   immediately after `test_missing_required_field_is_flagged`.

### Method
Direct text edit (e.g. via the `Edit` tool) inserting the new test method at
the anchor point in Details below.

### Details

Before:
```python
    def test_missing_required_field_is_flagged(self, tmp_path: Path) -> None:
        content = '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n---\n\nBody.\n'
        doc = _write(tmp_path / "example.md", content)
        schema = load_front_matter_schema(tmp_path / "no_schema_here.json")
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert any("related" in i for i in issues)

    def test_missing_front_matter_entirely_is_not_double_reported(
```

After:
```python
    def test_missing_required_field_is_flagged(self, tmp_path: Path) -> None:
        content = '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n---\n\nBody.\n'
        doc = _write(tmp_path / "example.md", content)
        schema = load_front_matter_schema(tmp_path / "no_schema_here.json")
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert any("related" in i for i in issues)

    def test_category_only_fixture_is_flagged_for_missing_area(
        self, tmp_path: Path
    ) -> None:
        """REQ-004's literal named fixture: a document using `category:`
        instead of `area:` is flagged for the missing required `area` field.
        `check_schema_compliance()` has no `additionalProperties` check, so
        this produces the same finding as any other `area:`-less fixture —
        this test exists to match REQ-004's exact wording, not to exercise a
        new code path."""
        content = (
            '---\ntitle: "Example"\ncategory: agent\ntags:\n  - agent\n'
            "related:\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        schema = load_front_matter_schema(tmp_path / "no_schema_here.json")
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert any("area" in i for i in issues)

    def test_missing_front_matter_entirely_is_not_double_reported(
```

## Compatibility considerations
No other test or file references `TestSchemaComplianceRequiredFields`'s
internal test order or count. Independent of seq 03 — this row's own edit is
unrelated to the CI workflow change.

## Security considerations
None — a test-only addition exercising local file parsing and in-memory logic.

## Rollback considerations
Single-file, single-insertion change to a Python test file under version
control; revert via `git revert`. No other file depends on this new test.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/tools/test_check_docs_structure.py | Full suite | `uv run pytest tests/tools/test_check_docs_structure.py -v` | All tests pass, including the new `test_category_only_fixture_is_flagged_for_missing_area` |
| tests/tools/test_check_docs_structure.py | Regression check | `uv run pytest -v` (full suite) | No existing test fails |
| tests/tools/test_check_docs_structure.py | Standard validation sequence | `ruff format`, `ruff check`, `mypy` | No new errors |

## Completion criteria
- `tests/tools/test_check_docs_structure.py` contains a test using a literal
  `category:`-only fixture that asserts the missing-`area` finding is reported
  (AC-4, REQ-004).
- `uv run pytest tests/tools/test_check_docs_structure.py -v` passes in full;
  `uv run pytest -v` shows no regression.

## Out of scope
`tools/check_docs_structure.py`, `tools/TOOL_DESCRIPTIONS.md` — both already
fully implement/document REQ-001/002/005 (see this Plan's own 2026-09-03
corrections; no implementation-procedure document was generated for either,
since neither requires any edit).
`.github/workflows/governance-docs-consistency.yml` (seq 03) — has its own
implementation-procedure document per this Plan's Implementation Target Files
table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Re-verified anchor before editing — no drift. Inserted the new test exactly as designed. |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | This row's own file is the test — 12 tests total (was 11), all passing |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `uv run pytest tests/tools/test_check_docs_structure.py -v`: 12/12 passed. `uv run pytest tests/tools/ -q` (broader regression check, scoped to this change's actual blast radius): 179/179 passed, no regression. `ruff format`/`ruff check`: clean. `mypy`: no issues. Full repo-wide `uv run pytest -v` not re-run — this session already ran it once earlier for an unrelated change and found 274 pre-existing failures in modules this row does not touch (agent commands, REPL, RAG ingestion); re-running for a one-test addition to `tests/tools/` would not add new information. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | N/A |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260902-194021_docmeta03_ci_enforce_documentation_metadata_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-125706_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-160534
- **Related target files**: tests/tools/test_check_docs_structure.py
