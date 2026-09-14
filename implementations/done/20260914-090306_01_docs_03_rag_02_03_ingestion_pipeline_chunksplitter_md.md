## Goal

Add a clarifying note to `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`'s Markdown source detection description stating: (1) no historical rationale for the `.md`/`.markdown`/`.mdx` extension-based rule is recorded in code comments or commit history; (2) contrary to what a reader might assume, there is no configuration override for this rule on URL-based sources — `md_index_enable` only affects non-`.md`-extension heuristic detection (REQ-001, REQ-002).

## Scope

- Add a short clarifying note near the existing Markdown source detection description (`_is_markdown_source()`'s behavior) stating the two confirmed facts above

## Assumptions

- `git log --all -S` on the two search terms performed this cycle found the earliest evidence available in this repository's history — no earlier, unreachable commit exists that would predate `ee035ff5e`/`c0b578e82` for this behavior
- The sibling Plan (`plans/20260913-202903_plan.md`) addressing this same file's duplicate-section structure does not remove or relocate the content this Plan's note is added near (confirmed: that Plan's scope is deleting the exact-duplicate section `3a` and renumbering `3b`→`3a`, not altering `3b`'s unique content, which includes the Markdown detection description this Plan targets)

## Design decisions

1. State "no rationale recorded" as a confirmed fact, not silence on the topic — this is itself useful information (it tells a future reader not to keep searching for a design document that doesn't exist), consistent with how this cycle's sibling issue (`183013`, exception hierarchy) was handled by attributing fragmentation to its actual traceable cause rather than to an unrecorded "design decision"
2. Explicitly label any inferred technical rationale as inferred — mixing an unverified plausibility argument with confirmed facts (like the override's absence) would undermine the note's credibility on the parts that are confirmed
3. Do not add a configuration override — the Issue's request for "how to override" assumed one exists; correcting that assumption is the right-sized documentation fix, not implementing a new override mechanism that was never actually requested as a feature (only assumed to already exist)

## Alternatives considered

1. Inventing a plausible-sounding historical rationale not backed by code or commit evidence — rejected because the Issue's Recommended Action asks for "the historical reason for this distinction" — per user direction, this Plan states that no such reason is recorded, rather than speculating
2. Adding a configuration option to override the extension-based rule — rejected because it is a source-code change, not requested by the Issue and not part of a documentation fix
3. Correcting the section-numbering context this content lives in — rejected because a sibling Plan (`plans/20260913-202903_plan.md`) already handles renumbering this file's duplicate sections; this Plan's note applies regardless of which section number eventually contains it

## Implementation

### Target file

`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure

1. Confirm the check order and absence of an override
2. Add the clarifying note near the existing Markdown source detection description

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `chunk_splitter.py:137-156` to reconfirm the extension check (line 146) precedes and is unconditioned by `md_index_enable` (line 148) (REQ-001, REQ-002; `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`)

Phase 2: Core Logic — add the clarifying note
- Add the note near the existing Markdown source detection description, stating both confirmed facts and the explicitly-labeled inferred rationale (REQ-001, REQ-002; `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md:186` states "URLs ending in `.md`, `.markdown`, or `.mdx` always use heading chunking regardless of `md_index_enable`. For other files, heuristic detection ... is used only if `md_index_enable=true`."
- `_is_markdown_source()`'s unconditional extension check confirmed at `chunk_splitter.py:137-156` (line 146 returns before line 148's `md_index_enable` check)
- No rationale found in `ee035ff5e`/`c0b578e82`'s commit messages or `chunk_splitter.py`'s comments
- Local `file://` URLs confirmed to carry the same extension (`crawl_persister.py:62`)

**Phase 2:** Append the following note after line 186:

```markdown
Note: No historical rationale for this extension-based rule is recorded in code comments or commit history (earliest traced commits: `ee035ff5e`/`c0b578e82`, "feat: Markdown ingest standardization — production code changes", contain no explanation). Contrary to what a reader might assume from the documentation, `md_index_enable` does not provide any way to override this rule for `.md`/`.markdown`/`.mdx` sources — including local `file://` sources (where `str.endswith()` matches the extension regardless of the `file://` scheme prefix, confirmed by inspecting `WebCrawler.crawl_file()`'s URL construction, `crawl_persister.py:62`: `f"file://{path.resolve()}"`). A plausible technical rationale is determinism vs. content-based heuristics (an extension-based check requires no content inspection), but this is inferred from the code's structure, not documented anywhere.
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the absence of an override mechanism is important for readers who may be looking for a way to disable heading chunking for `.md`-extension sources.

## Security considerations

No security impact — documentation addition only. However, accurately documenting the absence of an override mechanism helps readers understand where to look when debugging chunking-related issues.

## Rollback considerations

Simple revert: remove the added note. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md | Manual — verify note against `chunk_splitter.py` and `git log` | Manual inspection + `git log --all -S "always use heading chunking"` | Note's claims match the traced evidence exactly |

## Completion criteria

- [ ] The documentation states no historical rationale for the extension-based rule is recorded in code comments or commit history, citing the traced commits as the earliest evidence checked (REQ-001)
- [ ] The documentation states `md_index_enable` does not override extension-based detection for `.md`/`.markdown`/`.mdx` sources, including local `file://` sources (REQ-002)
- [ ] Any inferred technical rationale offered is explicitly labeled as inferred, not historical (REQ-001)

## Out of scope

- Inventing a plausible-sounding historical rationale not backed by code or commit evidence (the Issue's Recommended Action asks for "the historical reason for this distinction" — per user direction, this Plan states that no such reason is recorded, rather than speculating)
- Adding a configuration option to override the extension-based rule (a source-code change, not requested by the Issue and not part of a documentation fix)
- Correcting the section-numbering context this content lives in (`## 3b.` at the time of this cycle's investigation — a sibling Plan, `plans/20260913-202903_plan.md`, already handles renumbering this file's duplicate sections; this Plan's note applies regardless of which section number eventually contains it)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm check order and absence of an override | Completed | — | — | Confirmed via direct code reading |
| 2 | Phase 2: Add clarifying note | Completed | — | — | Added after existing description |
| 3 | Verification: manual review | Completed | — | — | Quality check passed |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-183018_missing_chunksplitter_markdown_detection_rationale.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-210434_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-090306
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
