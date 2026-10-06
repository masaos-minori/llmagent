## Goal

Update section 2.1.2 (`crawl_file` Behavior) of
`docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` to state that `crawl_file` now resolves
`lang="auto"` for local files, and remove the cross-reference to the tracking issue.
Implements `REQ-004`.

## Scope

Modify only the prose in section 2.1.2 of the named document.

Out of scope: the CLI `--lang` help string (already advertises `auto` per CJK ratio and needs
no change), other sections of the doc, and detection thresholds.

## Assumptions

- The CLI `--lang` help already describes `auto` detection, so no CLI change accompanies this
  doc edit (`REQ-004`).
- The change aligns the doc with the implemented behavior in
  `scripts/rag/ingestion/crawl_persister.py` (handled by the sibling source procedure).

## Design decisions

- Edit prose only. Keep the document within `skills/DESIGN.md` Docs content policy: no
  implementation-detail tables, no source-code line numbers, no literal port numbers.
- State design intent (what `auto` resolves to and why) rather than mechanical steps.

## Alternatives considered

- N/A: single target file; no cross-file alternatives.

## Implementation

### Target file

`docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`

### Procedure

1. Open section 2.1.2 (`crawl_file` Behavior).
2. Replace the sentence stating that "`crawl_file` currently accepts only `en` and `ja`;
   `lang == 'auto'` is rejected ... tracked in
   `issues/20261005-102245_...`" with prose stating that `auto` is now resolved for local
   files via CJK-ratio detection with the same `en` fallback as web pages.
3. Remove the `issues/20261005-102245_...` cross-reference from section 2.1.2.
4. Confirm the surrounding "Language Detection" note stays consistent: web pages always
   detect, and local files now also resolve `auto`.

### Method

- Grep section 2.1.2 for `auto` / `rejected` / `102245` to locate the exact sentence, then
  edit it in place.
- Keep wording at design-intent level; do not paste code blocks or source line numbers.

### Details

- Current text (confirmed by repository evidence): section 2.1.2 states that `auto` is
  rejected and cross-references `issues/20261005-102245_rag001_crawl_file-does-not-resolve-lang-auto.md`,
  which contradicts the CLI help that advertises `auto`.
- Acceptance (`REQ-004`): after the edit the section states `auto` is resolved for local
  files and no longer references the issue.

## Compatibility considerations

- Removes the advertised-vs-actual contradiction between the CLI help and the doc, bringing
  the doc into alignment with the implemented `save()` behavior.

## Security considerations

- Documentation-only change; no security impact.

## Rollback considerations

- Revert the doc edit. `deploy.sh` rsyncs the tree; not applicable.

## Validation plan

- `uv run python tools/check_docs_consistency.py --domain rag`.
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`.
- `uv run python tools/check_docs_content_policy.py` (doc touched).

## Completion criteria

- Section 2.1.2 states that `auto` is resolved for local files.
- No remaining reference to `issues/20261005-102245_...` in the affected section.
- Both doc checkers pass.

## Out of scope

CLI `--lang` help string, other doc sections, detection thresholds.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | edit section 2.1.2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | doc consistency + structure checkers |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `REQ-004` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: no blockers | N/A |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261005-102245_rag001_crawl_file-does-not-resolve-lang-auto.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261005-214953_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-113559
- **Related target files**: `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`
