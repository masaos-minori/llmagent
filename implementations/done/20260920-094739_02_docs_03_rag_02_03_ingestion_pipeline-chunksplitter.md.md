## Goal
Remove `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`'s hand-maintained
TypedDict field table, CLI argument table, full JSON payload example,
duplicated error-handling table, and "Canonical Artifact-Field Contract"
validator tables (REQ-002), replacing each with a pointer to its actual
canonical source while retaining the surrounding design-intent prose.

## Scope
In scope: exactly the 5 locations named in REQ-002 —
- TypedDict table, line 44 (section "Typed dict", lines 42-50)
- CLI argument table, line 188 (section 3.3, lines 186-191)
- Full JSON example, line 195 (section 3.4, lines 193-217 — table only;
  retain the 4 bullets below it)
- Canonical Artifact-Field Contract section, line 219 (section 3.4a, lines
  219-284 — the 2 field/validator tables only, at lines 237-246 and
  256-270; retain the section's surrounding prose)
- Error-handling table, line 288 (section 3.5, lines 286-292)

Out of scope: sections 3.6 (Logging) and 3.7 (Configuration), the
"Inheritance"/"Public Methods" prose (lines 52-59), and the "3.2" content
between the TypedDict table and CLI Arguments (not read as part of this
row's investigation — no tool or manual finding there). Do not touch
`docs/03_rag_05_4-error-handling-reference.md` (Out-of-Scope per Plan
Design) or any `scripts/rag/**` source file.

## Assumptions
- The retained explanatory bullets at lines 214-217 (chunk_type,
  chunking_strategy, normalized_content, source_file semantics) and the
  "Missing key vs. null vs. empty string" / "Cross-Field Validation Rules"
  prose in section 3.4a (lines 229-234, 276-284) are design-intent, not
  implementation reference — Plan Assumption, carried forward unchanged.

## Design decisions
- Point the TypedDict table at `scripts/rag/ingestion/pipeline_utils.py`
  directly, and correct the table's own pre-existing naming error while
  doing so: the table's `ChunkJsonPayload` row (line 47) does not exist in
  the codebase — the doc's own Evidence note at line 50 already says so
  ("`ChunkJsonPayload` does not exist in the codebase; the actual TypedDict
  for chunk payloads is `ChunkJsonRaw`... line 219"). The replacement text
  must name `CrawlJsonPayload` and `ChunkJsonRaw` (not `ChunkJsonPayload`)
  as the real symbols in `pipeline_utils.py`.
- Point the CLI argument table at `scripts/rag/ingestion/chunk_splitter.py
  --help`, per Implementation intent ("generated from `--help`, not
  hand-maintained").
- Point the full JSON example at the TypedDict definition (same file/symbol
  as above) rather than restating the JSON shape.
- Point the Canonical Artifact-Field Contract's two validator tables at
  `scripts/rag/ingestion/pipeline_utils.py`'s `read_crawl_json()` /
  `read_chunk_json()` and their `_validate_*` helper functions, keeping the
  surrounding prose (the contract's intro paragraph, the "Missing key vs.
  null vs. empty string" rule, the "crawl artifacts do not carry..."
  paragraph, and the "Cross-Field Validation Rules" subsection) — these
  encode a business rule (why the exception exists), not a mechanical field
  mirror.
- For the error-handling table: replace the "File-level failure" and
  "Existing chunks" rows with a pointer to
  `docs/03_rag_05_4-error-handling-reference.md`'s "ChunkSplitter" section
  (both rows are consistent with that canonical doc — confirmed by direct
  comparison during this row's adversarial verification). For the "Sudachi
  tokenization error" row specifically, point to
  `scripts/rag/ingestion/chunk_japanese.py::_normalize_ja_sentence` and
  `scripts/rag/ingestion/chunk_splitter.py::process_all` instead — per
  Plan Design's "Error-handling-reference.md accuracy finding," the
  canonical doc's own entry for this one case ("Return `""`; skip chunk;
  `WARNING`") is stale; the current code raises `TokenizationError`
  uncaught up to `process_all()`'s per-file catch, aborting that file's
  processing entirely, not skipping one chunk. State this explicitly in the
  replacement text so a future reader does not consult the stale entry.

## Alternatives considered
- Point the whole error-handling table at error-handling-reference.md
  unconditionally — rejected: would repeat error-handling-reference.md's
  stale Sudachi-case claim, actively making the corpus less accurate, not
  more.
- Remove the entire "Canonical Artifact-Field Contract" section outright
  instead of retaining its prose — rejected: the section's business-rule
  prose (the empty-content/code_blocks cross-field exception, the
  missing-key-vs-null-vs-empty-string rule) is design intent per
  Implementation intent's retained-content list ("how missing, duplicate,
  or out-of-order data is handled"), not implementation reference.

## Implementation
### Target file
docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md

### Procedure
1. Replace the "Typed dict" table (lines 44-48) with a short paragraph
   naming `CrawlJsonPayload` and `ChunkJsonRaw` and pointing to
   `scripts/rag/ingestion/pipeline_utils.py` for their exact fields; keep
   the existing "Evidence: Explicit in code" line's substance (the
   `ChunkJsonPayload`-does-not-exist correction) folded into the new prose
   instead of as a separate table caveat.
2. Replace the CLI Arguments table (lines 188-191) with a one-line pointer:
   "Run `uv run python scripts/rag/ingestion/chunk_splitter.py --help` for
   the current argument list."
3. Replace the JSON code block (lines 195-212) with a one-line pointer to
   the `ChunkJsonRaw` TypedDict in `pipeline_utils.py`; keep the 4 bullets
   at lines 214-217 unchanged immediately below it.
4. In section 3.4a, replace the two Field/Classification/Validator/Notes
   tables (lines 237-246 and 256-270) each with a one-line pointer to
   `read_crawl_json()` / `read_chunk_json()` and their `_validate_*` helpers
   in `pipeline_utils.py`; keep every other paragraph in 3.4a unchanged
   (intro, missing-key-vs-null-vs-empty-string rule, crawl-artifact-internal
   -fields note, Cross-Field Validation Rules).
5. Replace the Error Handling table (lines 288-292) with: a pointer to
   `docs/03_rag_05_4-error-handling-reference.md`'s "ChunkSplitter" section
   for the file-level-failure and existing-chunks cases, plus an explicit
   note for the Sudachi-tokenization-error case pointing to
   `chunk_japanese.py::_normalize_ja_sentence` /
   `chunk_splitter.py::process_all` and stating that
   error-handling-reference.md's entry for this specific case is stale (do
   not rely on it).

### Method
Five separate `Edit` calls (old_string/new_string), one per location above,
in the order listed — each is independently revertable. Do not combine them
into one large replacement, since Method 4's two tables are separated by
several paragraphs of retained prose.

### Details
- Preserve every heading (`### 3.3 CLI Arguments`, `### 3.4 Output JSON
  Format`, `### 3.4a Canonical Artifact-Field Contract`, `### 3.5 Error
  Handling`, and the `#### Crawl artifacts...` / `#### Chunk artifacts...`
  / `#### Cross-Field Validation Rules` subheadings) exactly as-is — Plan
  Risk (heading-anchor breakage, UNK-01) requires this for
  `03_rag_02_02_ingestion_pipeline-crawler.md`'s existing link to
  `03_rag_02_03_ingestion_pipeline-chunksplitter.md` (the whole-doc link,
  unaffected either way) and any future link to the "Canonical
  Artifact-Field Contract" heading itself.
- Do not alter the "Module-level Constants" note (line 40) or the
  "Inheritance"/"Public Methods" prose (lines 52-59) — out of scope.

## Compatibility considerations
Documentation-only; no public interface, CLI, or data format changes. No
compatibility impact.

## Security considerations
N/A: no secret-handling or security-relevant code path is touched — this is
a documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit reverting
each Edit — no data migration or state change is involved. Each of the 5
Method edits is independently revertable.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `uv run python tools/check_docs_structure.py docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `uv run python tools/check_docs_content_policy.py` (full-tree; confirm
  lines 44/188/195/288 no longer appear in the output for this file — the
  "Canonical Artifact-Field Contract" tables at lines 237/256 were never
  tool-detected, so their absence from the tool's output is not itself
  evidence of success; confirm those two tables' removal by direct Read
  instead)
- `uv run python tools/check_docs_consistency.py --domain rag` (or
  equivalent internal-link check) to confirm UNK-01 (no other doc's link to
  this file's headings breaks)

## Completion criteria
All 5 locations in Scope no longer contain the original table/example, each
replaced by the pointer described in Design decisions; all headings in
Details are unchanged; `check_docs_quality.py`, `check_docs_structure.py`,
and `check_docs_content_policy.py` report no new finding on this file
relative to this Plan's baseline (chunksplitter.md: 4 tool findings → 0);
no new broken internal link is introduced.

## Out of scope
- `docs/03_rag_05_4-error-handling-reference.md` (Out-of-Scope per Plan).
- Any `scripts/rag/**` source file.
- Sections 3.6, 3.7, and any content not named in Scope above.
- Fixing the pre-existing "2 H1 headings" `check_docs_structure.py` finding
  on this file (pre-existing, unrelated to this row's change — Plan AC-3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the 5 Edits per Procedure/Method | Completed | 20260920-100529 | 20260920-100529 | Stale detection: not stale. Adversarial verification: all 5 locations confirmed unchanged at recorded line numbers. Applied all 5 Edits. |
| 2 | N/A: no test suite applies to a documentation content change | Completed | 20260920-100529 | 20260920-100529 |  |
| 3 | Run the 4 commands in Validation plan | Completed | 20260920-100529 | 20260920-100529 | check_docs_content_policy.py: 0 findings for this file (was 4). check_docs_quality.py: 2 pre-existing warnings (unchanged, unrelated). check_docs_structure.py: 1 pre-existing finding (2 H1 headings, unrelated). check_docs_consistency.py --domain rag: no new finding, no other doc links to the Canonical Artifact-Field Contract heading (UNK-01 resolved). |
| 4 | N/A: no further documentation update needed beyond this file itself | Completed | 20260920-100529 | 20260920-100529 |  |

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
- **Requirement ID**: `REQ-002` — remove chunksplitter.md's implementation-reference content
- **Source issue**: issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-094101_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-094739
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md