## Goal

Remove CI-017 and CI-018 entries from Part 1 Active Items in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, restoring consistency with the document's Current-Specification-Only policy. Delete trailing separator blank lines so surrounding entries join cleanly.

## Scope

Deleting CI-017 and CI-018 entries from Part 1 Active Items in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; removing trailing separator blank lines so surrounding entries join cleanly. No changes to Part 2 (Needs Confirmation), Part 3, or Part 4; no changes to any other governance document.

## Assumptions

- The Current-Specification-Only Policy in Part 1 requires removal of resolved entries, not relocation to another section.
- The `Status=resolved` values for CI-017 and CI-018 accurately reflect their resolution state.
- CI-017's malformed structure (duplicated Recommended Action / Resolution Target fields) does not require separate repair since the entire entry is being removed.

## Design decisions

- Delete-only approach: remove entries whose Status is `resolved`; do not add or modify any entry.
- Remove trailing separator blank lines after each deletion so adjacent entries join without extra gaps.
- Because CI-017 is entirely malformed (duplicated fields), no separate field-order repair is needed — deletion resolves both issues simultaneously.

## Alternatives considered

- Move resolved items to a separate "Resolved" subsection within Part 1: rejected — the Current-Specification-Only Policy calls for removal, not relocation.
- Repair CI-017's duplicated fields before deletion: rejected — unnecessary work since the entry is being removed entirely.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Read Part 1 Active Items in full; scan for all entries with `Status=resolved`.
2. Identify CI-017 and CI-018 entries for deletion.
3. Delete the CI-017 entry including its field list and trailing separator blank lines.
4. Delete the CI-018 entry including its field list and trailing separator blank lines.
5. Verify no other Active Items entry carries `Status=resolved`.
6. Verify CI-017 and CI-018 are absent from the document.
7. Verify all `open`/`deferred` entries remain unchanged except for adjacency after deletions.

### Method

Edit — targeted deletion of two list entries followed by cleanup of separator blank lines.

### Details

**Step 1: Confirm entries to delete**

Read Part 1 Active Items section (approximately lines 379-423). Verify:
- CI-017: `Status=resolved` (line 383) — delete
- CI-018: `Status=resolved` (line 405) — delete

Also scan for any additional violations beyond these two.

**Step 2: Delete CI-017 entry**

Delete the following content (lines 379-400):
```
#### CI-017

- **ID**: CI-017
- **Title**: `docs/rag_04_04_dto-models_config.md`'s documented DTOs no longer exist — `scripts/rag/models_config.py` replaced by `RagConfigImpl`
- **Status**: resolved
- **Severity**: Medium
- **Area**: RAG
- **Type**: document-code-mismatch
- **Source**: `scripts/rag/models_config.py`, `scripts/shared/types.py::RagConfig`
- **Owner**: Unassigned
- **First Found**: 2026-09-20
- **Target**: `docs/rag_04_04_dto-models_config.md`
- **Related**: N/A
- **Summary**: The 7 dataclasses documented in `docs/rag_04_04_dto-models_config.md` (`MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, `PipelineConfig`) no longer exist in `scripts/rag/models_config.py`, which now defines only `RagConfigImpl`.
- **Current Description**: The doc's main body still describes the 7 legacy per-stage config dataclasses as the runtime config contract.
- **Observed Implementation**: `scripts/rag/models_config.py` defines only `RagConfigImpl` (a flat dataclass), actively used by `scripts/rag/pipeline.py` and 5 test files, implementing the `RagConfig` Protocol (`scripts/shared/types.py`), whose docstring no longer claims these files are "DTOs for the ingestion TOML format".
- **Recommended Action**: Rewrite `docs/rag_04_04_dto-models_config.md` to document `RagConfigImpl` and the `RagConfig` Protocol instead of the removed per-stage config dataclasses.
- **Resolution Target**: Follow-up issue created — `issues/20260926-072314_rewrite_dto_models_config_to_document_RagConfigImpl.md`
- **Impact**: A reader of this doc would look for config classes that no longer exist and miss the actual runtime contract (`RagConfigImpl`/`RagConfig` Protocol).
- **Recommended Action**: Rewrite `docs/rag_04_04_dto-models_config.md`'s main body to document `RagConfigImpl` and the `RagConfig` Protocol instead of the removed per-stage dataclasses.
- **Resolution Target**: Next RAG documentation pass covering `scripts/rag/models_config.py`
```

After deletion, ensure the preceding batching note (CI-008 through CI-016, ending at line 377) joins cleanly with the next remaining entry below CI-018.

**Step 3: Delete CI-018 entry**

Delete the following content (lines 401-423):
```
#### CI-018

- **ID**: CI-018
- **Title**: RAG exception hierarchy fragmented across `exceptions.py`/`llm_prompts.py`/`pipeline.py` with no recorded rationale
- **Status**: resolved
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/rag/exceptions.py`, `scripts/rag/llm_prompts.py::RagRerankError`, `scripts/rag/pipeline.py::RagPipelineError`
- **Owner**: Unassigned
- **First Found**: 2026-09-19
- **Target**: `docs/rag_05_4-error-handling-reference.md`
- **Related**: N/A
- **Summary**: `RagRerankError` and `RagPipelineError` are defined outside `scripts/rag/exceptions.py` and inherit from `RuntimeError` rather than the `RagLayerError` base class used by the other 7 rag-layer exceptions, with no ADR or design document recording a rationale for the split.
- **Current Description**: The exception hierarchy is not unified under a single base class across the rag layer.
- **Observed Implementation**: `RagRerankError` (llm_prompts.py), `RagExpansionError` (llm_prompts.py), and `RagPipelineError` (pipeline.py) all inherit from `RuntimeError` while the other 7 rag-layer exceptions inherit from `RagLayerError`.
- **Recommended Action**: Move `RagRerankError`, `RagExpansionError`, and `RagPipelineError` to `exceptions.py` and change their base class to `RagLayerError`; update all imports and `except` clauses accordingly.
- **Resolution Target**: Follow-up issue created — `issues/20260926-073329_unify_rag_exceptions_under_RagLayerError.md`
- **Current Description**: The exception hierarchy is not unified under a single base class across the rag layer.
- **Observed Implementation**: Confirmed via 3 independent refactoring commits: `5ac7b757 refactor(rag): Phase 1-3 — backward-compat removal, foundation files, dataclass migration` introduced `RagLayerError` and its 6 subclasses; `2ff62348 refactor(rag): split llm.py (413→42+260+245 lines) into prompts + client` introduced `RagRerankError`/`RagExpansionError` (`RuntimeError`-based); `c0477811 refactor(rag): pipeline/stages fail-fast — remove expand_queries_safe, except Exception fallbacks, add RagPipelineError` introduced `RagPipelineError` (`RuntimeError`-based). No ADR or design document records a rationale for keeping them separate.
- **Impact**: Future unification would require touching every `except` clause across `scripts/rag/` that currently catches `RagRerankError`/`RagPipelineError`/`RagExpansionError`/`RuntimeError` by name — a cross-cutting change; until then, a caller could catch the wrong exception type or miss one to a base-class catch.
- **Recommended Action**: Decide whether to unify `RagRerankError`/`RagPipelineError`/`RagExpansionError` under `RagLayerError` in a dedicated cross-cutting refactor, or document the split as an accepted permanent exception via ADR.
- **Resolution Target**: Next RAG exception-hierarchy refactor or ADR decision
```

After deletion, remove the three trailing blank lines (original lines 424-426) between CI-018 and Part 2 heading so they join cleanly with a single blank line separator.

**Step 4: Verify no other resolved entries**

Scan the entire Part 1 Active Items section for any other entries with `Status=resolved`. If found, apply the same deletion procedure.

**Step 5: Verify deletions**

Confirm:
- CI-017 is absent from the document
- CI-018 is absent from the document
- All `open`/`deferred` entries remain unchanged except for adjacency after deletions
- The ID-group ordering convention (DESIGN-*, EVENTBUS-*, SHARED-*, CI-*) is preserved for remaining CI-* entries

## Compatibility considerations

This change affects only the Active Items list under Part 1. No downstream artifact consumes Part 1 programmatically — it is human-reviewed documentation and known-issue checks. No backward compatibility impact.

## Security considerations

None. This is a documentation-only edit with no code or configuration changes.

## Rollback considerations

Rollback is straightforward: restore the original CI-017 and CI-018 entries and re-add the three blank-line separators. A single `git checkout -- docs/00_governance/governance_03_issue-and-uncertainty-management.md` reverses the entire change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Manual verification against Part 1 Active Items | Read Part 1 section side-by-side | No entry has Status=resolved; CI-017 and CI-018 absent; open/deferred entries preserved |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Optional structural check | `uv run python tools/check_docs_structure.py docs/00_governance/*.md` | No new structural findings |

## Completion criteria

- No Part 1 Active Items entry has `Status=resolved`.
- CI-017 and CI-018 are absent from the document.
- All `open`/`deferred` entries are unchanged except for adjacency after the deletions.
- Adjacent entries join cleanly without extra blank-line gaps.

## Out of scope

- Any change to Part 2 (Needs Confirmation), Part 3, or Part 4.
- Resolving the underlying RAG/code matters behind CI-017 or CI-018.
- Changing the lifecycle/status vocabulary.
- Editing any part other than Part 1 Active Items.
- Editing any other governance document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove CI-017 entry from Part 1 Active Items | Completed | — | — | REQ-001 |
| 2 | Remove CI-018 entry from Part 1 Active Items | Completed | — | — | REQ-002 |
| 3 | Verify no other Active Items entry carries Status=resolved | Completed | — | — | REQ-003 |
| 4 | Preserve ID-group ordering convention of remaining CI-* entries | Completed | — | — | REQ-004 |
| 5 | Leave all open/deferred entries unchanged except for adjacency | Completed | — | — | REQ-005 |
| 6 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260926-173112_gd002_remove-resolved-known-issues-and-repair-malformed-ci-017-in-governance_03-part-1.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-190314_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-060618
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md