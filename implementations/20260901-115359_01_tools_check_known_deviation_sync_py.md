## Goal
Implement `tools/check_known_deviation_sync.py`, a read-only reporting tool that
cross-references every ADR's Known Deviations (and Related Documents → Known
Issues) section against the Status field of the same Known Issue ID in its area's
canonical `docs/*_90_inconsistencies_and_known_issues.md` document, reporting Status
disagreements and dangling ID references (REQ-001, REQ-002, REQ-003, REQ-004,
REQ-005, REQ-006).

## Scope
- In scope: canonical-doc `### <ID>` + Status extraction (dual format); ADR-side
  Known Issue ID extraction scoped to `## Known Deviations` and `## Related
  Documents` → `### Known Issues`; glob-based cross-document resolution over
  every `*_90_inconsistencies_and_known_issues.md` file; Status-mismatch and
  dangling-reference reporting; `--format json` alongside a default
  human-readable summary.
- Out of scope: automatically resolving any detected mismatch (reporting only);
  checking Known Issue content accuracy beyond the Status field; modifying
  `tools/_docs_consistency_lib.py`.

## Assumptions
- IDs are resolved by glob-discovering every
  `docs/*_90_inconsistencies_and_known_issues.md` file, not a hardcoded
  three-document list — required to correctly resolve `EVENTBUS-008` against
  `docs/06_eventbus_90_inconsistencies_and_known_issues.md` rather than reporting
  a false dangling reference.
- `tools/_docs_consistency_lib.py` needs no modification — this tool defines its
  own local ID/Status/Known-Deviations parsing and only imports the shared
  `DocFile`/`Issue`/`discover_md_files`/`report_and_exit` helpers, mirroring
  `tools/check_needs_confirmation_inventory.py`'s existing precedent.
- `mypy` is not part of this file's validation gate — `pyproject.toml`'s
  `[tool.mypy] files = ["scripts/"]` does not cover `tools/`.

## Design decisions
- Follow `tools/check_needs_confirmation_inventory.py`'s shape (the closest
  existing analog): parse per-ID entries from one document family, parse ID
  references from a second document family, cross-check, emit `Issue` objects,
  finish with `report_and_exit` — reusing `tools/_docs_consistency_lib.py`'s
  `DocFile`/`Issue`/`discover_md_files`/`report_and_exit` helpers, not
  reimplementing Markdown discovery.
- Canonical-doc Status extraction tries two patterns in order: bullet-list form
  `^- \*\*Status\*\*:\s*(\S+)` (confirmed format for `04_mcp_90`'s `MCP-004`
  entry: `- **Status**: resolved`), falling back to inline-prose form for
  `90_shared_90`'s `SHARED-*` entries. An entry matching neither is skipped with
  a note, not silently ignored.
- ADR-side ID extraction is restricted to exactly two locations: `## Known
  Deviations` bullets and `## Related Documents` → `### Known Issues`
  parenthetical mentions — never whole-document prose. A candidate token must
  match `[A-Z]+-\d+` and be immediately followed by whitespace, an em-dash, or
  end-of-line, so `ADR-004-D1-profile-config-model-still-present` (confirmed
  present in `docs/adr/ADR-004-environment-failure-handling-policy.md`'s Known
  Deviations bullet) is not misread as ID `ADR-004`.
- ADR-side status signal: a bullet is "resolved-like" only when its label is
  literally `**Resolved**:` (confirmed as the label ADR-012 uses for its
  resolved entries); every other Known-Deviations bullet (e.g. `**Known
  Issue**:`, confirmed as ADR-012's label for its still-active `MCP-004` entry)
  is "open-like".
- Cross-document resolution: resolve every extracted ID against the union of
  `discover_md_files` results filtered to filenames ending in
  `_90_inconsistencies_and_known_issues.md` — confirmed necessary by the
  `EVENTBUS-008` case (referenced by both `docs/adr/ADR-006-...md` and
  `docs/adr/ADR-008-...md`, resolved only against
  `docs/06_eventbus_90_inconsistencies_and_known_issues.md`, which is not one of
  the three documents the source issue names explicitly).

## Alternatives considered
- Hardcoding the three canonical documents the source issue names explicitly
  (`04_mcp_90`, `05_agent_90`, `90_shared_90`): rejected — confirmed to produce a
  false dangling-reference report for `EVENTBUS-008`, contradicting the issue's
  own constraint to avoid false positives.
- Extending `tools/_docs_consistency_lib.py` with new shared parsing functions:
  rejected — `tools/check_needs_confirmation_inventory.py` already establishes
  the precedent of a new checker defining its own local per-ID parsing without
  touching the shared lib; this keeps the file count at three (Path A).

## Implementation
### Target file
`tools/check_known_deviation_sync.py`

### Procedure
1. Discover every `docs/*_90_inconsistencies_and_known_issues.md` file via
   `discover_md_files` (or equivalent glob), filtered to that filename suffix.
2. For each such document, parse every `### <ID>: <title>` entry's Status field
   using the dual-format extraction (bullet-list, then inline-prose fallback);
   record `{ID: Status}` per document.
3. Discover every `docs/adr/*.md` file; for each, scan its `## Known Deviations`
   section's bullets and `## Related Documents` → `### Known Issues`
   subsection's parenthetical mentions for candidate ID tokens matching
   `[A-Z]+-\d+` followed by whitespace/em-dash/end-of-line; record each ID
   alongside whether its bullet's label is `**Resolved**:` (resolved-like) or
   any other label (open-like).
4. For each ADR-side ID reference: look it up in the canonical `{ID: Status}`
   map built in step 2. If not found in any canonical document, emit a
   dangling-reference `Issue`. If found, compare the canonical Status against
   the ADR-side resolved-like/open-like signal; emit a Status-mismatch `Issue`
   when they disagree.
5. Emit the collected `Issue` objects via `report_and_exit` in the default
   human-readable form, or serialize the same objects as JSON under `--format
   json`.

### Method
Follows `tools/check_needs_confirmation_inventory.py`'s structure: plain
functions for canonical-doc parsing, ADR-side parsing, and cross-checking, plus
an argparse-based `main()` with a `--format {text,json}`-style flag (mirroring
`tools/check_docs_consistency.py`'s `--domain`/`--skip` argparse-flag
convention, not a new CLI framework). Imports `DocFile`, `Issue`,
`discover_md_files`, `report_and_exit` from `tools/_docs_consistency_lib.py`.

### Details
- Regex for the ADR-side ID lookahead: `r"([A-Z]+-\d+)(?=\s|—|$)"` (or
  equivalent), applied only within the two scoped sections per bullet line —
  never against the full file content.
- An ADR bullet whose first token after its label does not match the ID pattern
  at all (e.g. `docs/adr/ADR-005-rag-source-derived-index-relationships.md`'s
  backtick-led `sqlite-vec` bullet, confirmed to carry no ID token) contributes
  no ID and is not reported as anything — not an error, not a finding.
- The two UNK items from the source Plan (05_agent_90's 5-tier Status scheme,
  90_shared_90's `partially resolved` bucket) are implemented as: any 5-tier
  value not obviously in the `open` family is excluded from automatic
  mismatch reporting (flagged in an inline code comment); `partially resolved`
  is a third bucket that never triggers an automatic mismatch on its own
  (informational only).
- Exit code: `0` when no findings exist; the tool's own exit-code-on-findings
  policy should mirror `tools/check_needs_confirmation_inventory.py`'s
  established convention for this class of reporting-only checker (confirmed
  via reading that script during Phase 1 preparation, per the source Plan's
  Implementation steps).

## Compatibility considerations
New file; no existing callers (not wired into any pre-commit hook or
`routing.md` "When to run which tool" row by this Plan — invoked manually).
Read-only against `docs/adr/*.md` and `docs/*_90_inconsistencies_and_known_issues.md`
— never writes to either. No `deploy/deploy.sh` change required (`tools/` and
`tests/` are outside its rsync/config scope).

## Security considerations
- Strictly read-only against every document it scans — no write/rename/move/
  delete call anywhere in this file.
- No `shell=True` subprocess usage, `eval()`/`exec()`, or untrusted
  deserialization.
- `uv run bandit -r tools/ -c pyproject.toml` must report no high/medium
  findings; the repo's existing `tools/` bandit baseline is 0 issues.

## Rollback considerations
New file only; rollback is deleting `tools/check_known_deviation_sync.py`. Being
read-only, it cannot have altered any other file's state.

## Validation plan
- `uv run pytest tests/tools/test_check_known_deviation_sync.py -v` — once
  created (see
  `implementations/20260901-115359_03_tests_tools_test_check_known_deviation_sync_py.md`),
  all fixture cases (match / mismatch / dangling / false-positive-avoidance)
  must pass.
- `uv run ruff format tools/ tests/tools/`; `uv run ruff check tools/
  tests/tools/` — clean, no errors.
- `uv run bandit -r tools/ -c pyproject.toml` — no high/medium findings.
- Live-repository validation (informational, not a pytest assertion): `uv run
  python tools/check_known_deviation_sync.py` and `... --format json` against
  the actual `docs/` tree — must report `MCP-004`, `DESIGN-1`, `DESIGN-2`; must
  NOT report `MCP-003`, `MCP-005`, `EVENTBUS-008`, or
  `ADR-004-D1-profile-config-model-still-present`.

## Completion criteria
- `tools/check_known_deviation_sync.py` exists and implements all four report
  categories plus `--format json`.
- AC-1: reports `MCP-004` as a Status mismatch against the live repository.
- AC-2: confirms `MCP-003` and `MCP-005` produce no report.
- AC-3: reports `DESIGN-1` and `DESIGN-2` as dangling references.
- AC-4: does not report `EVENTBUS-008` as dangling.
- AC-5: `--format json` output is valid JSON and matches the default summary's
  findings.
- AC-7: does not falsely report `ADR-004-D1-profile-config-model-still-present`.

## Out of scope
- Automatically resolving any detected mismatch.
- Checking Known Issue content accuracy beyond the Status field.
- Modifying `tools/_docs_consistency_lib.py`.
- Adding a `routing.md` "When to run which tool" row.
- Fixing `docs/03_rag_90_inconsistencies_and_known_issues.md`'s missing `### <ID>`
  headings or ADR-008's Japanese-language Known Deviations section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `implementations/20260901-115359_03_tests_tools_test_check_known_deviation_sync_py.md` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `mypy` N/A per Assumptions |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Covered by `implementations/20260901-115359_02_tools_TOOL_DESCRIPTIONS_md.md` |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: `issues/20260831-194739_tool006_check_known_deviation_sync.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-112435_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-115359
- **Related target files**: `tools/check_known_deviation_sync.py`
