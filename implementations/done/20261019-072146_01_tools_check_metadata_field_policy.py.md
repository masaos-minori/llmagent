## Goal

Create a new standalone checker `tools/check_metadata_field_policy.py` that scans `docs/*.md`
front matter and workitem files (`issues/`, `plans/`, `implementations/`) for metadata/status
fields outside the sanctioned field set, then flags them at `Warning`. Non-blocking. This closes
the documented `Partial` gap for GV-016.

## Scope

- **In-Scope**:
  - Define the permitted metadata/status field set per domain from authoritative sources.
  - Scan `docs/*.md` front matter for keys outside the front-matter schema's property set.
  - Scan workitems for `## ` sections outside their template's canonical section set.
  - Flag out-of-set fields at `Warning`.
  - Add unit tests with extra-field and compliant fixtures; run against the current `docs/` and
    `issues/` corpora.
- **Out-of-Scope**:
  - Changing the sanctioned field set or the templates.
  - Adding new required fields.

## Assumptions

- The checker is `Warning`-level and non-blocking, consistent with GV-016's existing gate.
- The dominant `tools/check_*.py` convention is string severity (`Issue(severity: str)` with
  `"WARNING"`/`"ERROR"`); follow it (the `Severity` HIGH/MEDIUM/LOW enum is used only by
  `check_canonical_source_conflicts.py`).
- The permitted front-matter set is the schema's defined `properties`: `title`, `area`, `tags`,
  `related`, `status`, `class` (four required plus two optional defined properties).
- Workitem files map to templates by directory: `issues/` → `issue.md`, `plans/` → `plan.md`,
  `implementations/` → `implementation-procedure.md`.

## Design decisions

- New standalone CLI following the `tools/check_*.py` convention (argparse, `Issue` results,
  string `Warning`/`ERROR` severities, `main() -> int` + `sys.exit(main())`).
- Two independent scanners share one reporting path: a front-matter scanner and a workitem-section
  scanner.
- Front-matter permitted set derived from `schemas/doc_front_matter.json`'s `properties`; ignore
  `additionalProperties: true` for GV-016's purpose (fields outside the defined properties are
  "unnecessary").
- Workitem permitted set derived from each template's canonical `## ` sections, excluding
  meta/instructional sections and unioning embedded sub-template sections.

## Alternatives considered

- Hardcoding the permitted field sets — rejected: REQ-001/REQ-002 require deriving them from the
  schema and templates (single source of truth); hardcoding would drift.

## Implementation

### Target file

`tools/check_metadata_field_policy.py`

### Procedure

1. Scaffold the module following an existing `tools/check_*.py` (e.g. `check_docs_content_policy.py`):
   argparse CLI, `Issue` results with string severity, `main() -> int` ending in `sys.exit(main())`.
2. Implement the front-matter scanner (UNK-01): parse each `docs/*.md` YAML front matter and
   compare its keys against the permitted set derived from `schemas/doc_front_matter.json`'s
   `properties`. Do not flag the four required fields or the two optional defined properties
   (REQ-005). Flag keys outside the set at `Warning` (REQ-003).
3. Implement the workitem scanner (UNK-02): map each workitem file to its template by directory;
   derive the permitted section set (top-level `## ` sections minus meta/instructional sections,
   unioned with embedded sub-template sections); flag any `## ` section not in that set (UNK-03,
   REQ-004).
4. Report `Warning`-only; preserve the non-blocking contract.

### Method

- **CLI.** Mirror `check_docs_content_policy.py`: `argparse.ArgumentParser`, optional `--root`
  (default repo root), `def main(argv=None) -> int` ending in `sys.exit(main())`.
- **Front-matter parsing.** Reuse `tools/_front_matter_schema.py` (shared front-matter schema
  loader / required-field default) rather than re-implementing it. Load `schemas/doc_front_matter.json`
  and read its `properties` keys as the permitted set. Parse YAML front matter via the same loader
  `check_docs_structure.check_front_matter` uses.
- **Workitem mapping.** Map directory → template basename (`issues/` → `issue.md`, `plans/` →
  `plan.md`, `implementations/` → `implementation-procedure.md`). Extract top-level `## ` sections
  from each main template; drop known meta/instructional sections (`## Field notes`,
  `## Notes on filling...`, `## Column Definitions`, `## Notes`); union the sections contributed by
  embedded sub-templates (`requirement-traceability.md`, `traceability.md`, `risks-issue.md`,
  `unknowns-issue.md`, `execution-status.md`). Record the exclusion list and embedding map in-code.
- **Flagging.** A front-matter key not in the permitted set → `Warning`. A workitem `## ` section
  not in the permitted set → `Warning`. Fail safe toward not flagging when a template is missing.

### Details

- `REQ-001`: the permitted front-matter set is derived from `schemas/doc_front_matter.json`'s
  `properties`.
- `REQ-002`: the permitted workitem set is derived from each template's canonical sections.
- `REQ-003`: a `docs/*.md` front-matter key outside the permitted set is flagged at `Warning`.
- `REQ-004`: a workitem `## ` section outside its template's canonical set is flagged at `Warning`.
- `REQ-005`: required/template-mandated fields are never flagged.
- `REQ-006`: no false positives on the current `docs/` and `issues/` corpora.
- **UNK-01:** use the schema's defined `properties` (`title`, `area`, `tags`, `related`, `status`,
  `class`) as the permitted set; document the `additionalProperties: true` interpretation in-code.
- **UNK-02:** extract top-level `## ` sections, drop meta/instructional sections, union embedded
  sub-template sections; record the exclusion list and embedding map in-code.
- **UNK-03:** enforce strictly but validate against the current corpus first (REQ-006); triage
  pre-existing extra sections separately rather than expanding the permitted set silently.

## Compatibility considerations

New CLI entry point only; no external callers. `Warning`-only findings preserve the non-blocking
contract. No change to `schemas/doc_front_matter.json`, `templates/`, or the sanctioned field set.

## Security considerations

N/A: reads local `docs/` and workitem files; applies read-only parsing; executes no user input.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_metadata_field_policy.py` | Format/lint | `uv run ruff format tools/ && uv run ruff check tools/` | Clean |
| `tools/check_metadata_field_policy.py` | Type check | `uv run mypy --no-namespace-packages tools/` | Clean |
| `tools/check_metadata_field_policy.py` | Security | `uv run bandit -r tools/ -c pyproject.toml -ll` | No high/medium |
| `tools/check_metadata_field_policy.py` | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No boundary violations |
| `tools/check_metadata_field_policy.py` | Unit + corpus | `uv run pytest tests/tools/test_check_metadata_field_policy.py` then corpus runs | Extra field/section flagged; corpora clean |
| Whole change | Full regression | `uv run pytest` + `uv run pre-commit run --all-files` | No new failures |

## Completion criteria

- The checker derives per-domain permitted field sets, scans docs front matter + workitems, and
  flags out-of-set fields at `Warning`.
- Unit tests cover extra-field and compliant fixtures plus corpus runs with zero false positives.
- The GV-016 matrix row reports field-policy enforcement as automated with the follow-up note
  cleared.

## Out of scope

Changing the sanctioned field set or the templates, and adding new required fields.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261019-172724 | 20261019-172724 | REQ-001..006; UNK-01..03 |
| 2 | Add or update tests per Validation plan | Completed | 20261019-172724 | 20261019-172724 | REQ-001..006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-172724 | 20261019-172724 | all REQs Adversarial smoke test found missing 'if __package__' sys.path block -> direct-run ModuleNotFoundError; added per check_*.py convention. ruff/mypy/bandit/lint-imports clean; 30/30 tests pass; real-corpus run: No issues found. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261019-172724 | 20261019-172724 | REQ-007 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006` (new checker: derive per-domain permitted field sets, scan docs front matter + workitems, flag out-of-set fields)
- **Source issue**: `issues/done/20261018-173518_gov016_automate-metadata-field-usage-policy-enforcement.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-183121_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-072146
- **Related target files**: `tools/check_metadata_field_policy.py`