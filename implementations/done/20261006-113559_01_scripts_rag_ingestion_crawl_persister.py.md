## Goal

Resolve `lang="auto"` to `en` or `ja` inside `CrawlPersister.save()` for local files,
reusing the existing `crawler_utils.detect_lang()` CJK-ratio logic, and remove the
misleading identity expression/comment in `save()`. Implements `REQ-001` (resolve `auto`)
and `REQ-002` (remove identity expression).

## Scope

In scope: modify `scripts/rag/ingestion/crawl_persister.py`, `save()` only.

Out of scope: `save_http()`, the web-page resolution path, `_CJK_RATIO_THRESHOLD`,
`MIN_TEXT_LENGTH_FOR_DETECTION`, adding languages beyond `en`/`ja`, and the pre-existing
cosmetic staleness of the `crawler.py` module docstring (`REQ-005`, `UNK-03`).

## Assumptions

- `content` is already read above the resolution point (UTF-8 read with `errors="ignore"`),
  so `detect_lang(content)` needs no additional I/O or ordering change.
- `detect_lang(content) or "en"` reproduces
  `LanguageResolver.resolve_lang(content, "auto")` semantics: short/inconclusive text →
  `en`, CJK ratio ≥ threshold → `ja`, else `en`.
- `save_http()` never receives `auto` in practice because the HTTP orchestrator resolves
  the language via `LanguageResolver` first, so leaving it unchanged does not reintroduce
  the bug (`REQ-005`).

## Design decisions

- Resolve `auto` inside `save()` before the `{"en", "ja"}` supported-language check
  (option A, encoded in the plan): there is exactly one caller (`WebCrawler.crawl_file()`),
  so resolving here covers the only entry point and any future caller, and avoids
  duplicating the CJK-ratio logic.
- Reuse the pure `detect_lang()` helper from `crawler_utils` rather than reimplementing the
  CJK ratio, keeping a single source of truth for the threshold and fallback.

## Alternatives considered

- Option B (alternative, not encoded in the plan): resolve `auto` in
  `WebCrawler.crawl_file()` before delegating to `save()`. Equally valid given the single
  caller, and keeps `CrawlPersister` free of language-detection concerns. The implementer
  may choose A or B; both satisfy `REQ-001`. Do not add option B to this document as a
  second target file — it is an alternative within the same single target file.

## Implementation

### Target file

`scripts/rag/ingestion/crawl_persister.py`

### Procedure

1. In the local import block that currently imports only `url_to_slug` from
   `rag.ingestion.crawler_utils`, also import `detect_lang`, using the same
   `# noqa: E402` circular-import-avoidance rationale already applied to `url_to_slug`.
2. Replace the identity expression

   ```python
   resolved_lang: str = lang if lang != "auto" else lang
   ```

   with a branch that resolves `auto`:

   ```python
   if lang == "auto":
       resolved_lang = detect_lang(content) or "en"
   else:
       resolved_lang = lang
   ```

   Place it where the identity expression currently sits, immediately before the
   `if resolved_lang not in frozenset({"en", "ja"})` check.
3. Remove or correct the stale comment
   `# Resolve "auto" lang by CJK-ratio detection on the file content` so it accurately
   describes the implemented behavior (deleting it is acceptable).

### Method

- Locate the two sites with grep: the import block (~lines 25-27) and the resolution block
  (~lines 55-61). Edit in place.
- Keep `content` referenced; it is defined by the read above, so no variable-order change.
- Do not touch `save_http()` (lines 96-135) or the payload construction beyond the value
  already written to `"lang": resolved_lang` (line 74).

### Details

- Current code (confirmed by repository evidence): line 56 holds the identity expression;
  line 57 rejects non-`{en, ja}` with a warning and returns `0`; line 74 writes
  `resolved_lang` to the JSON `lang` field.
- `detect_lang(text)` (`crawler_utils`) returns `None` below `MIN_TEXT_LENGTH_FOR_DETECTION`,
  `"ja"` when the CJK ratio ≥ `_CJK_RATIO_THRESHOLD`, else `"en"`. Therefore
  `detect_lang(content) or "en"` yields `en` for short (< 100 char) or inconclusive text,
  identical to `LanguageResolver.resolve_lang(..., "auto")`.
- Complexity: `save()` is currently radon `B(7)`; adding one branch raises cyclomatic
  complexity slightly. Re-check radon after the edit; if the grade degrades below the
  acceptable threshold, factor the resolution into a small private helper instead of
  inlining it (`REQ-001` risk mitigation).

## Compatibility considerations

- Supported output languages remain `{en, ja}` (`REQ-005`). Unsupported values other than
  `en`/`ja`/`auto` still return `0` with a warning and write nothing.
- The non-auto path is byte-for-byte unchanged, so existing `test_ingestion_freshness.py`
  (`crawl_file(target, "en")`) is unaffected.

## Security considerations

- No new input surface: `detect_lang()` operates on already-read file content. No
  command execution, eval, or deserialization is introduced.

## Rollback considerations

- Revert the two-line change in `save()` and restore the identity expression. No data,
  schema, migration, or configuration impact. `deploy.sh` rsyncs the tree; not applicable.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawl_persister_lang.py -v` (new tests cover the
  `auto` path produced by the sibling test-file procedure).
- `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` (regression, unchanged).
- `uv run ruff check scripts/`, `uv run mypy scripts/`,
  `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/rag/ingestion/ -c pyproject.toml`.

## Completion criteria

- `crawl_file(path, "auto")` on a CJK-dominant local file writes a crawl JSON whose `lang`
  is `ja`; on an English file writes `en`; short/inconclusive text falls back to `en`.
- An unsupported value other than `en`/`ja`/`auto` passed to `crawl_file()` returns `0`
  with a warning and writes nothing.
- No `lang if lang != "auto" else lang` identity expression remains in `save()` (`REQ-002`).
- All validation commands pass with no new findings.

## Out of scope

`save_http()`, the web-page resolution path, `_CJK_RATIO_THRESHOLD`,
`MIN_TEXT_LENGTH_FOR_DETECTION`, adding languages, and the `crawler.py` module docstring
staleness.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261006-135532 | `REQ-001`, `REQ-002` |
| 2 | Add or update tests per Validation plan | Completed | — | 20261006-135532 | covered by `test_crawl_persister_lang.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261006-135532 | ruff/mypy/lint-imports/bandit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261006-135532 | N/A: doc handled by separate row |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261005-102245_rag001_crawl_file-does-not-resolve-lang-auto.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261005-214953_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-113559
- **Related target files**: `scripts/rag/ingestion/crawl_persister.py`