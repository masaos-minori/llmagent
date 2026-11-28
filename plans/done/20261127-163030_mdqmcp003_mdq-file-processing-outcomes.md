# Make MDQ file processing report one per-file outcome with unambiguous limits and correct grep locations

## Goal
- Give every MDQ file-processing call one per-file result that states what actually happened, so counts, `index_state`, and the tool response describe committed work rather than attempted work; make size limits state their unit; make grep report the source-file line and the context it was asked for; and make non-fatal parser warnings observable without leaking absolute paths.

## Priority
High

## Scope
- **In-Scope**:
  - A per-file processing result DTO with the statuses `indexed`, `skipped_unchanged`, `skipped_size_limit`, `skipped_no_content`, and `failed`, plus stable reason codes and non-sensitive warning counts.
  - Every indexing and refresh caller tallies from the DTO status instead of from "the call returned without raising".
  - `index_state` advances only after a successful commit.
  - Separate counters for input paths, discovered files, committed files, skipped files, and failed files; directory counts describe files in both refresh modes; `partial_success` for mixed outcomes and a tool error when every file fails.
  - Byte and decoded-character size limits with explicit units (`max_file_bytes`), and the configuration-key rename documented as a compatibility change.
  - Scan semantics: normalized root-relative POSIX path matching, explicit symlink-directory behavior, canonical deduplication, re-authorization and re-stat between scan and read, deterministic exclude rules with documented case sensitivity.
  - Grep: return the requested context before and after the match, compute line numbers from the stored `start_line`, define multiple matches per chunk and multiline-regex semantics, honor an explicit zero context, and apply output limits to the context-inclusive text.
  - Structured `invalid_frontmatter` warnings and counts without absolute paths, keeping the permissive fallback.
  - Documentation of the resulting outcome, unit, scan, grep, and warning semantics.
- **Out-of-Scope**:
  - Content fingerprints and the single file transaction: the fingerprint and transaction-atomicity issues own them; this Plan defines the rule that `index_state` advances only after commit, and the transaction plan must not redefine it.
  - The server error contract, audit emission, and audit redaction, owned by `plans/20261127-160114_mdqmcp001_mdq-server-boundary.md` (this Plan consumes its codes and its no-absolute-path rule).
  - The search query boundary, owned by `plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md`; grep path authorization and the raw-pattern metadata field are not changed here.
  - Approval and dry-run behavior.
  - An optional strict-frontmatter mode: the issue only asks to consider it, and no strict-mode flag exists in the repository, so it is deferred to the owner.
  - Any change to `scripts/db/helper.py`.
- **Dependencies**:
  - Depends on `plans/20261127-160114_mdqmcp001_mdq-server-boundary.md` — phase all — the closed domain error-code vocabulary used by the all-files-failed tool error, and the rule that persistent output carries no absolute paths, are defined there.
  - Blocks the file-identity and transaction-atomicity plans: those plans consume the per-file outcome and the post-commit rule defined here and must not redefine them.
  - Can run in parallel with the search query-boundary plan.
  - The MDQ server contract is documented in the MCP domain docs named by `docs/00_index.md` "Document References by Task".
  - **Depends on**: issues/20261119-142123_mdqmcp001_mdq-server-boundary.md — phase all — error codes and the audit redaction contract.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 3), filed as `issues/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`.

The issue marked one claim as explicit in code (the byte-versus-character comparison) and the rest as backlog claims needing confirmation. Every one of those claims is now confirmed against current source, so the Problem section below states them as facts rather than claims.

## Problem
Verified against current source:

- `_index_single_file()` in `scripts/mcp_servers/mdq/indexer.py` returns `None` for every non-success outcome: the size-limit skip, a `FileNotFoundError` from `parse_markdown()`, and a swallowed `sqlite3.Error` from `write_document_chunks()`. Its caller `_tally_indexing()` counts any call that did not raise as `tally.indexed`, so a skipped or failed file is reported as indexed.
- `_refresh_changed_file()` writes the `index_state` row after `_index_single_file()` returns, and `_index_single_file()` swallows the write failure, so a file whose rows were never committed still advances `index_state` and is counted as indexed. The existing test `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py::test_failed_reindex_does_not_record_the_new_mtime` passes only because the failure is injected through a monkeypatched `_index_single_file` that raises; the internal swallow is covered only on its rollback side (`test_chunk_write_failure_rolls_back_the_document_upsert` asserts ROLLBACK and no COMMIT), not on its outcome side, so no test measures a swallowed write failure as a `failed` result or as a non-advancing `index_state`.
- The counters mix units. `index_paths()` and incremental refresh count one unit per requested path, so a directory with 20 files counts as 1, while force mode (`_reindex_forced()`) counts one per discovered file. `input_path_count` and `indexed_count` therefore describe different things in the same response.
- `scripts/mcp_servers/mdq/indexer.py` compares `path.stat().st_size` (bytes) with `service.max_file_chars` (characters). For Japanese, emoji, or a BOM the byte count exceeds the character count, so a file under the character limit can be skipped.
- `scripts/mcp_servers/mdq/index_scan.py` matches with `fnmatch.fnmatch()`, whose case behavior depends on `os.path.normcase` (case-sensitive on POSIX, case-insensitive elsewhere), and deduplicates by `str(f)` rather than the canonical path, so a symlinked duplicate is not deduplicated. `iter_indexable_files()` does not traverse symlinked directories (verified on the project's Python 3.13: `Path.rglob` does not follow symlinked directories), while `f.is_file()` follows a symlinked file, so a symlink inside a scanned root is discovered and only rejected later by `authorize_path()`.
- Nothing re-authorizes or re-stats a discovered file between the scan and the read, so a file replaced or removed between the two is processed against a stale decision.
- `scripts/mcp_servers/mdq/db_grep.py` computes `start_idx` and `end_idx` for the requested context, builds `_context_lines`, and never returns them: the match text is the pattern hit only. `line_number = start_idx + 1` is chunk-relative, not the source-file line, even though the row carries `start_line`. `find_grep_match()` returns on the first match, so a chunk contributes at most one match. `max_chars` is applied to the match text only, not to the context-inclusive output.
- `scripts/mcp_servers/mdq/mdq_service.py` resolves context with `req.context_before or self.context_before`, so an explicit `0` is replaced by the configured default; the same applies to `context_after`.
- `scripts/mcp_servers/mdq/parser.py` catches `yaml.YAMLError` and sets `fm_data = None`, so invalid frontmatter loses metadata silently: no warning, no count.

## Reason for Change
Result accuracy and state integrity. The fingerprint, transaction-atomicity, and approval work all read the per-file outcome and the post-commit rule, so those semantics have to be settled before that work starts.

## Implementation Intent
One per-file result DTO is the only source of truth for what happened to a file. Every caller — indexing, both refresh modes, and the aggregation that builds the tool response — tallies from the DTO status, so "the call returned" is no longer evidence of success. `index_state` advances only after the write transaction commits. Counters describe distinct things: requested paths, discovered files, committed files, skipped files, failed files. Size limits name their unit. Grep returns the context it was asked for and reports the source-file line. Parser warnings are structured records with stable codes and counts, carried without absolute paths. The error codes and the no-absolute-path rule come from the server-boundary plan; this Plan does not extend them.

## Requirements
- `REQ-001`: Introduce the per-file processing result DTO with statuses `indexed`, `skipped_unchanged`, `skipped_size_limit`, `skipped_no_content`, and `failed`, stable reason codes, and non-sensitive warning counts; every indexing and refresh caller tallies from the DTO status, so a skipped or failed file is never counted as `indexed`.
- `REQ-002`: `index_state` advances only after a successful commit; a swallowed write failure does not advance state and is reported as `failed`.
- `REQ-003`: Separate counters for input paths, discovered files, committed files, skipped files, and failed files; directory counts describe files in both modes; mixed outcomes report `partial_success`; a tool error is raised when every file fails.
- `REQ-004`: Size limits state their unit: the pre-read gate is `max_file_bytes`; the decoded-character limit is a separate named decision; the configuration-key rename is documented as a compatibility change.
- `REQ-005`: Scan semantics are deterministic: matching on normalized root-relative POSIX paths, explicit symlink-directory behavior, canonical deduplication, re-authorization and re-stat between scan and read, and documented case sensitivity for the exclude rules.
- `REQ-006`: Grep returns the requested context before and after the match, computes line numbers from the stored `start_line` with the synthetic heading offset and the documented definition that the reported line is the first stored content line (UNK-03, resolved 20261127), defines multiple matches per chunk and multiline-regex semantics, honors an explicit zero context (only `None` selects the default), and applies output limits to the context-inclusive text.
- `REQ-007`: Invalid frontmatter stays non-blocking but observable: structured `invalid_frontmatter` warning codes and counts, with no absolute path in the record.
- `REQ-008`: Document the outcome statuses, the counters, the byte-versus-character limits, the scan and symlink semantics, the grep location and context semantics, and the parser warnings.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261127; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Define the per-file result DTO, its status vocabulary, its stable reason codes, and the warning-count field; add the grep context fields to the match model; rename the size-limit configuration field to its byte unit | REQ-001, REQ-004, REQ-006, REQ-007, AC-1, AC-3, AC-5, AC-6 | `max_file_chars: int = Field(default=100000, gt=0)` is the configuration field; `GrepDocMatch` has `line_number` and `match_text` and no context fields; `IndexPathsMetadata` has `input_path_count`, `indexed_count`, `skipped_count`, `failed_count` and no discovered or committed count | `tests/mcp_servers/mdq/test_mdq_config.py`, `tests/mcp_servers/mdq/test_db_grep.py` | Verified |
| `scripts/mcp_servers/mdq/indexer.py` | Modify | Return the DTO from the per-file path instead of `None`; tally from the DTO status; advance `index_state` only after a commit; count discovered and committed files separately from requested paths; report `partial_success` and raise the all-files-failed tool error | REQ-001, REQ-002, REQ-003, AC-1, AC-2 | `_index_single_file()` returns `None` on the size skip, on `FileNotFoundError`, and after swallowing `sqlite3.Error`; `_tally_indexing()` increments `tally.indexed` whenever the awaited call does not raise; `_refresh_changed_file()` writes `index_state` after `_index_single_file()` returns; `_reindex_forced()` counts files while `_index_one_path()` counts paths | `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_mdq_service.py` | Verified |
| `scripts/mcp_servers/mdq/index_scan.py` | Modify | Match on normalized root-relative POSIX paths with explicit case behavior, deduplicate by canonical path, and state the symlink-directory behavior; keep discovery free of database access | REQ-005, AC-4 | `_matches_any_glob()` uses `fnmatch.fnmatch()`; `iter_indexable_files()` deduplicates with `matched: dict[str, Path]` keyed by `str(f)`; `f.is_file()` follows a symlinked file while `Path.rglob` does not traverse a symlinked directory | `tests/mcp_servers/mdq/test_mdq_scan_semantics.py` | Verified |
| `scripts/mcp_servers/mdq/parser.py` | Modify | Emit a structured `invalid_frontmatter` warning record with a stable code and keep the permissive fallback; report the decoded-character count so the byte gate and the character limit are distinct | REQ-004, REQ-007, AC-3, AC-6 | `except yaml.YAMLError: fm_data = None` discards the failure with no warning; `content = path.read_text(encoding="utf-8")` is read after the byte gate in `scripts/mcp_servers/mdq/indexer.py` | `tests/mcp_servers/mdq/test_parser.py` | Verified |
| `scripts/mcp_servers/mdq/db_grep.py` | Modify | Return the requested context before and after the match; compute the line number from the stored `start_line` with the synthetic heading offset, the reported line being the first stored content line (UNK-03, resolved 20261127); support multiple matches per chunk; apply the output limit to the context-inclusive text | REQ-006, AC-5 | `_context_lines = lines[start_idx:end_idx]` is computed and never used; `line_number=start_idx + 1` is chunk-relative although the query selects `start_line`; `find_grep_match()` returns on the first `finditer()` hit; `match_text = re_match.group()[:max_chars]` truncates only the match | `tests/mcp_servers/mdq/test_db_grep.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | Honor an explicit zero context (only `None` selects the default); carry the byte-unit attribute name; render the outcome text from the DTO counters including `partial_success` | REQ-003, REQ-004, REQ-006, AC-2, AC-3, AC-5 | `ctx_before = req.context_before or self.context_before` and `ctx_after = req.context_after or self.context_after` replace `0` with the configured default; `self.max_file_chars = cfg.max_file_chars`; `_format_refresh_summary()` renders the counters as fixed lines | `tests/mcp_servers/mdq/test_mdq_service.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_security_validation.py` | Modify | Apply the startup validation to the renamed byte-limit key | REQ-004, AC-3 | `"max_file_chars"` is an entry of `_MDQ_SCALAR_SETTINGS`, so the renamed key is not validated until this list changes | `tests/mcp_servers/mdq/test_mdq_config.py` | Verified |
| `config/mdq_mcp_server.toml` | Modify | Rename the size-limit key to its byte unit and state the unit in the comment | REQ-004, AC-3 | `max_file_chars = 100000` is the deployed key; the file's historical-notes comment points to a config-history document that does not exist under `docs/` | `tests/mcp_servers/mdq/test_mdq_config.py` | Verified |
| `tests/mcp_servers/mdq/test_db_grep.py` | Modify | Replace the chunk-relative line-number assertions with the first-stored-content-line definition (`start_line + 1 + k`), including a section whose stored content begins at its first content line, and add the returned-context, multiple-match, multiline, and zero-context cases; assert the limit applies to the context-inclusive text | REQ-006, AC-5 | `test_line_number_for_match_on_later_line` asserts `match.line_number == 4` from the chunk-relative formula; no test asserts returned context because none is returned | itself | Verified |
| `tests/mcp_servers/mdq/test_parser.py` | Modify | Keep the permissive fallback characterization and add the structured warning and its count | REQ-007, AC-6 | `test_invalid_yaml_syntax_falls_back_to_empty_tags` pins the silent fallback that must stay | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Modify | Move the counters assertions onto the DTO-based counts and add the mixed-success directory and retry-after-failure cases | REQ-001, REQ-002, REQ-003, AC-1, AC-2 | `_counters(result)` and `_meta_counts(meta)` pin the path-level counts; `test_failed_reindex_does_not_record_the_new_mtime` injects the failure through a monkeypatched `_index_single_file`, so the internal swallow is uncovered | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_service.py` | Modify | Rewrite the outcome-text assertions for `partial_success` and the all-files-failed tool error; move the size-limit tests onto the byte unit; add the ASCII, Japanese, emoji, and BOM cases | REQ-001, REQ-003, REQ-004, AC-1, AC-2, AC-3 | Seven tests assert `text == "Indexing complete"`: two skip-only runs (`test_index_paths_skips_nonexistent`, `test_index_paths_skips_non_md_file`), two all-failed runs (`test_index_paths_records_failed_count_on_file_error`, `test_index_paths_records_failed_count_on_directory_error`), three runs with committed work; `test_oversized_file_is_skipped_with_warning` asserts the message `exceeds max_file_chars` | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_config.py` | Modify | Assert the renamed byte-limit default and the field list | REQ-004, AC-3 | `assert cfg.max_file_chars == 100000` and the parametrized field list both name `max_file_chars` | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py` | Create | New file: production SQLite failure, size limit, file disappearance, and no-content outcomes measured through the DTO, and the retry-after-failure path | REQ-001, REQ-002, AC-1 | Does not exist; `tests/mcp_servers/mdq/` holds 35 test files. The swallow's rollback is covered by `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py::test_chunk_write_failure_rolls_back_the_document_upsert`, which asserts the ROLLBACK and the empty document row but not the outcome, so no test measures the swallowed write failure as a `failed` result or as a non-advancing `index_state` (re-verified 20261127) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_scan_semantics.py` | Create | New file: symlinked directory and symlinked file behavior, canonical deduplication, nested exclude, duplicate include, case sensitivity, and re-authorization and re-stat between scan and read | REQ-005, AC-4 | Does not exist; scan behavior is covered only by `tests/mcp_servers/mdq/test_mdq_service.py` and `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, which test glob matching through the service (checked in Step 3) | itself | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Document the file-result statuses and counters, the byte-versus-character limits, the scan and symlink semantics, the grep location and context semantics, and the parser warnings | REQ-008, AC-3, AC-4, AC-5, AC-6 | The doc states `max_file_chars`: "a larger file is skipped with a warning and is not indexed", which is the ambiguous unit being replaced | `uv run python tools/check_docs_content_policy.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/mdq/index_write.py` | `write_document_chunks()` is the commit boundary the post-commit rule is measured against; the caller owns the connection and rolls back on `sqlite3.Error`; `normalized_path = path.resolve().as_posix()` is the canonical form the scan must deduplicate against | REQ-002, REQ-005 |
| `scripts/mcp_servers/mdq/auth.py` | `authorize_path()` is the re-authorization applied between scan and read; this Plan calls it, it does not change it | REQ-005 |
| `scripts/mcp_servers/mdq/db_schema.py` | `chunks.start_line` and `chunks.end_line` are the columns the grep line number is computed from | REQ-006 |
| `scripts/mcp_servers/mdq/mdq_server.py` | The audit detail builder reads `indexed_count`, `skipped_count`, `deleted_count`, and `failed_count` with `.get(..., 0)`, so the new counters are additive; the tool-error rendering and the error codes are owned by the server-boundary plan | REQ-003 |
| `scripts/mcp_servers/mdq/mdq_error_codes.py` | The closed domain codes the all-files-failed tool error maps to; defined by the server-boundary plan. Re-verified 20261127: the file does not exist yet — it is a `Create` row of `plans/done/20261127-160114_mdqmcp001_mdq-server-boundary.md` whose procedure `implementations/20261127-213547_08_scripts_mcp_servers_mdq_mdq_error_codes.py.md` is still `Pending`, so the codes are read from that Plan's design, not from source | REQ-003 |
| `scripts/mcp_servers/mdq/mdq_models.py` domain exceptions section | `MdqServiceError` is the exception class the all-files-failed case raises | REQ-003 |
| `deploy/deploy.sh` | `config/mdq_mcp_server.toml` is copied by an existing `cp` line, so the key rename changes deployed content without adding a deploy line | REQ-004 |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | The rule that persistent output carries no absolute path, which the warning records must satisfy; owned by the server-boundary plan | REQ-007 |
| `docs/22_mcp/mcp_04_04_mdq.md` | Line 33 states `include_globs` / `exclude_globs` apply to all four indexing scans, which the scan-semantics wording must stay consistent with. Re-verified 20261127: `mcp_05_05_mdq-enforcement-and-lockdown.md` contains no glob statement, so the scan-semantics statement is in this doc, not in the enforcement doc | REQ-005 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): A skipped or failed file never advances successful state, and no counter reports it as committed.
- `AC-2` (REQ-003): Directory counts describe files in both modes; the counters name distinct things; a mixed run reports `partial_success`; a run in which every file fails reports a tool error.
- `AC-3` (REQ-004): Byte and character limits are unambiguous, and the renamed key is validated at startup.
- `AC-4` (REQ-005): Scan behavior is deterministic and documented: canonical deduplication, explicit symlink-directory behavior, documented case sensitivity, and re-authorization and re-stat before read.
- `AC-5` (REQ-006): Grep line numbers match the source file for a section whose stored content starts at its first content line; for a section whose content had leading blank lines stripped at index time, the reported line is the documented definition — the first stored content line (`start_line + 1 + k`). The requested context including an explicit zero is returned, and multiple-match behavior is documented and tested.
- `AC-6` (REQ-007): Invalid frontmatter remains non-blocking and produces a structured warning and a count with no absolute path.

## Tests
- `REQ-001`: `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py` — production SQLite write failure, size limit, file disappearance between scan and read, and no-content outcomes measured through the DTO; `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` — mixed-success directories and retry after failure.
- `REQ-002`: `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py` — `index_state` does not advance when the write fails inside `_index_single_file()`; `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` — the existing post-success characterization stays.
- `REQ-003`: `tests/mcp_servers/mdq/test_mdq_service.py` — `partial_success` for a mixed run, the all-files-failed tool error, and the directory unit in both modes.
- `REQ-004`: `tests/mcp_servers/mdq/test_mdq_service.py` — ASCII, Japanese, emoji, and BOM size-limit cases; `tests/mcp_servers/mdq/test_mdq_config.py` — the renamed default and the field list.
- `REQ-005`: `tests/mcp_servers/mdq/test_mdq_scan_semantics.py` — symlinked directory, symlinked file, canonical duplicate, nested exclude, duplicate include, case sensitivity, and file replacement between scan and read.
- `REQ-006`: `tests/mcp_servers/mdq/test_db_grep.py` — returned context, source-file line number, multiple matches per chunk, multiline regex, explicit zero context, and the limit applied to the context-inclusive text.
- `REQ-007`: `tests/mcp_servers/mdq/test_parser.py` — invalid frontmatter still parses to empty tags and now produces a structured warning and a count with no absolute path.
- Full-suite validation: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run pytest`, `uv run diff-cover coverage.xml --compare-branch=master` at or above 90% on changed lines, `uv run pre-commit run --all-files`.

Baseline before any change: `uv run pytest tests/mcp_servers/mdq/test_db_grep.py tests/mcp_servers/mdq/test_parser.py tests/mcp_servers/mdq/test_mdq_incremental_refresh.py tests/mcp_servers/mdq/test_mdq_service.py tests/mcp_servers/mdq/test_mdq_config.py -q` → 159 passed (re-run 20261127: 159 passed); the whole `tests/mcp_servers/mdq/` suite is 416 passed, 1 skipped (re-run 20261127; the previously recorded 460 was stale).

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task" (MCP server spec row):
- `REQ-008` drives the MDQ server contract doc: the file-result statuses and the counters, the byte-versus-character limits, the scan and symlink semantics, the grep location and context semantics, and the parser warnings. The `max_file_chars` statement must be rewritten to the byte unit.
- The configuration-key rename is a compatibility change and must be stated in that doc; `config/mdq_mcp_server.toml`'s historical-notes comment points to a config-history document that does not exist under `docs/`, so the rename note is written in the doc named by the task mapping and the stale reference is reported rather than invented (UNK-04).
Doc content policy applies: the status vocabulary and the reason codes are a closed vocabulary (retain); no per-exception handling table or implementation-location statement is added (`skills/DESIGN.md` Docs content policy). Run `uv run python tools/check_docs_content_policy.py` per `rules/tool-gates.md`.

## Assumptions
- The status vocabulary and the reason codes are closed sets defined in `scripts/mcp_servers/mdq/mdq_models.py`; the DTO carries a root-relative POSIX path, never an absolute path, so the warning records satisfy the audit rule without re-implementing redaction in the mdq package.
- The configuration key is renamed rather than accepted under both names. A dual-name migration would keep the ambiguous unit in the deployed config, and no repository convention supports aliasing a config key. Recorded as UNK-01 for the owner.
- The decoded-character limit is not added as a new key in this Plan; the byte gate is the enforced limit and the character limit is documented as a separate decision (UNK-02). Adding a key would change the deployed config content.
- `index_scan.py` keeps its boundary: discovery only, no database access and no authorization. Re-authorization and re-stat are applied by `scripts/mcp_servers/mdq/indexer.py`, which already imports `authorize_path()`, so no new cross-module dependency is introduced.
- The all-files-failed tool error is raised from the service layer as `MdqServiceError` and rendered by the audit boundary owned by the server-boundary plan; this Plan does not modify `scripts/mcp_servers/mdq/mdq_server.py`.
- The grep line number is computed as `start_line + 1 + k` within the stored content. Because `parser.py` strips leading blank lines from `content` before storing it, `k` cannot be traced back to the original file line for a section whose content began with blank lines. Per the owner decision recorded on 20261127 (UNK-03), the reported line is defined as the first stored content line, so `start_line + 1 + k` is the contract and the doc states that it is the stored-content line, not necessarily the original file line.
- The existing counter keys keep their current names and path-level meaning, and the discovered-file and committed-file counters are added as new keys (UNK-06, resolved 20261127). `tests/mcp_servers/test_mdq_audit.py` is therefore unaffected by this Plan and stays out of its target rows.
- Cross-plan target overlaps recorded by `tools/check_plan_target_overlaps.py` (run 20261127): 12 findings name this Plan. The 7 recorded in the next bullet are compatible; the remaining 5 were not recorded before and are compatible as well — `scripts/mcp_servers/mdq/indexer.py` (mdqmcp004, mdqmcp005, mdqmcp007), `scripts/mcp_servers/mdq/parser.py` (mdqmcp010), `tests/mcp_servers/mdq/test_db_grep.py` (mdqmcp010), `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` (mdqmcp004, mdqmcp005, mdqmcp010), `tests/mcp_servers/mdq/test_parser.py` (mdqmcp010). mdqmcp010 adds only a `pytestmark` line and a citation to each test module; the source rows are different sections of the same modules. Re-verified 20261127: the current run reports 11 findings, because `config/mdq_mcp_server.toml` is no longer a candidate — the server-boundary plan that shared it is archived in `plans/done/` and the tool scans open Plans only. All 11 are compatible on the same grounds.
- Cross-plan target overlaps are compatible, recorded here per `check_plan_target_overlaps.py`: `scripts/mcp_servers/mdq/mdq_models.py` — the server-boundary plan changes the `MdqConfig` strict types, the query-boundary plan changes `SearchDocsMetadata.query_preview`, this Plan adds the result DTO and renames the size-limit field; different sections of the same module. `docs/22_mcp/mcp_04_04_mdq.md` — the server-boundary plan documents the availability, health, stats, error-code, and audit surfaces, the query-boundary plan documents the query boundary, this Plan documents the outcome, unit, scan, grep, and warning semantics. `config/mdq_mcp_server.toml` — the server-boundary plan changes the strict-value handling of existing keys, this Plan renames one key; the rename must not be read as a strict-type change. `scripts/mcp_servers/mdq/mdq_security_validation.py` — the server-boundary plan changes validation behavior, this Plan changes only the key name in `_MDQ_SCALAR_SETTINGS`. `scripts/mcp_servers/mdq/mdq_service.py` — the server-boundary plan owns the audit and health surfaces, this Plan changes the context resolution, the size-limit attribute, and the outcome text. `tests/mcp_servers/mdq/test_mdq_config.py` — the server-boundary plan adds strict-type cases, this Plan moves the renamed default and field list. `tests/mcp_servers/mdq/test_mdq_service.py` — the server-boundary plan adds the audit and health cases, this Plan rewrites the outcome-text, size-limit, and unit cases.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The configuration migration for `max_file_chars` | No owner decision recorded; no repository convention for aliasing or migrating a config key | Confirm with the configuration owner; the plan's default is a rename with the compatibility note in the doc named by the task mapping | False |
| UNK-02 | Whether a decoded-character limit is required in addition to `max_file_bytes` | The issue says "plus a decoded-character limit if required"; no owner decision recorded | Decide between byte-gate-only and a second named key; a new key changes the deployed config content | False |
| UNK-03 | The grep line-number offset for a section whose content had leading blank lines stripped at index time | `chunks` stores the stripped `content` and the heading `start_line`; the number of stripped leading lines is not recoverable from the stored row | Resolved by the owner on 20261127: the reported line is defined as the first stored content line, i.e. `start_line + 1 + k` within the stored content; the schema change that would store the stripped-line offset is not taken. `AC-5` is met under this definition and the definition is documented | False |
| UNK-04 | Where the configuration-key rename history is documented | `config/mdq_mcp_server.toml` references `docs/mdq_config_history.md`, which does not exist under `docs/` | Confirm the doc the config-history note should point to; the plan writes the rename note in the doc named by `docs/00_index.md` and reports the stale reference | False |
| UNK-05 | Multiline-regex and multiple-match semantics for grep | No owner decision recorded; `re.compile(req.pattern)` is called with no flags, so `^` and `$` are not line-anchored, and `find_grep_match()` returns one match per chunk | Owner decision; the plan's default is multiple matches per chunk up to the cap and documented line-anchored semantics, and both are pinned by tests | False |
| UNK-06 | Whether `skipped_count` and `indexed_count` keep their current path-level meaning or become file-level counters | `tests/mcp_servers/test_mdq_audit.py::TestIndexPathsAudit.test_mixed_scenario_counts` asserts `skipped_count=2` for two skipped paths (a nonexistent path and a non-Markdown file) through the audit detail builder; the file is not a row of this Plan and is owned by `plans/done/20261127-160114_mdqmcp001_mdq-server-boundary.md` for redaction tests only | Resolved by the owner on 20261127: the existing keys keep their current path-level meaning and the discovered-file and committed-file counters are added, so the audit assertion is unaffected and no row is added | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/indexer.py` | Modify | Highest for the indexing path: every `index_paths` and `refresh_index` call, every counter, and the `index_state` rule pass through it; no external importer outside `mcp_servers.mdq` | 0 | 3 | N/A: copied by the scripts sync |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Medium: the DTO and the renamed configuration field are read by `indexer.py`, `mdq_service.py`, and `mdq_security_validation.py`; the audit detail builder reads the counter keys with `.get(..., 0)`, so added counters are additive | 0 | 2 | N/A |
| `scripts/mcp_servers/mdq/index_scan.py` | Modify | Medium: shared by the indexer and both refresh modes; the change is confined to matching and deduplication | 0 | 1 | N/A |
| `scripts/mcp_servers/mdq/parser.py` | Modify | Medium: the parse result is consumed by the indexer; the warning record is new output | 0 | 3 | N/A |
| `scripts/mcp_servers/mdq/db_grep.py` | Modify | Medium: the match model gains fields and the reported line number changes, which is a visible output change for `grep_docs` | 0 | 3 | N/A |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | Medium: the context resolution, the size-limit attribute, and the outcome text are all service-level behavior | 1 | 3 | N/A |
| `scripts/mcp_servers/mdq/mdq_security_validation.py` | Modify | Low: one entry in the validated key list | 1 | 1 | N/A |
| `config/mdq_mcp_server.toml` | Modify | Medium: the deployed key name changes, so the deployed config and the code must change in the same release | 3 | 2 | Existing `cp` line copies the file; the deployed key must be renamed with the code change |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Low | 2 | 2 | N/A |

## Design
**One per-file result.** The DTO is the only place a file's outcome is decided. `_index_single_file()` returns it instead of `None`, and every caller tallies from its status. The statuses are a closed vocabulary: `indexed`, `skipped_unchanged`, `skipped_size_limit`, `skipped_no_content`, `failed`. Reason codes are stable strings, not messages, so a count can be reported without a path. The DTO carries the root-relative POSIX path, never an absolute path, which keeps the warning records inside the audit rule already defined by the server-boundary plan.

**Post-commit state.** `_refresh_changed_file()` advances `index_state` only when the write transaction committed, which requires `_index_single_file()` to report the commit outcome rather than swallowing the error. This is the rule the transaction-atomicity plan consumes; it is defined here and must not be redefined there.

**Counters that name their unit.** Requested paths, discovered files, committed files, skipped files, and failed files are separate counts. A directory is reported as the files it produced, in both the incremental and force modes, so the same run reports the same unit regardless of mode. A mixed run reports `partial_success`; a run in which every file fails raises `MdqServiceError`, which the audit boundary maps to the code defined by the server-boundary plan.

**Units.** The pre-read gate compares `st_size` with `max_file_bytes`. The character limit is a separate decision (UNK-02), so the byte gate is not silently reinterpreted as a character limit. The rename is a compatibility change: the model field, the service attribute, the validated key list, the config file, the tests, and the doc change together in one commit.

**Scan semantics.** Matching is performed on normalized root-relative POSIX paths with `fnmatchcase`, so case behavior is stated rather than inherited from `os.path.normcase`. Deduplication is by canonical path, which removes a symlinked duplicate. Symlinked directories are not traversed and symlinked files are discovered, so the plan states that behavior in the doc instead of changing it. Re-authorization and re-stat happen in `scripts/mcp_servers/mdq/indexer.py` before the read, which keeps `scripts/mcp_servers/mdq/index_scan.py` free of authorization and database access.

**Grep.** The match model carries the context before and after the match, so the computed context becomes part of the result. The line number is computed from the stored `start_line` with the synthetic heading offset, and the reported line is the first stored content line (UNK-03, resolved 20261127), which is the source-file line for a section whose content was stored without stripping. Multiple matches per chunk are supported up to the cap, and the multiline semantics are stated (UNK-05). Only `None` selects the configured default, so an explicit zero context is honored. The output limit is applied to the context-inclusive text, not to the match alone.

**Consumer scan (Step 3).** `grimp` reports 18 MDQ modules with no external importers; `indexer`, `index_scan`, `parser`, `db_grep`, `index_write`, and `mdq_models` are imported only inside `mcp_servers.mdq`. `PYTHONPATH=scripts uv run lint-imports` passes (6 contracts kept). `tools/scan_change_consumers.py --seed max_file_chars` returns six script consumers (`indexer.py`, `mdq_models.py`, `mdq_security_validation.py`, `mdq_service.py`), six test consumers (`test_mdq_config.py`, `test_mdq_service.py`), and one doc consumer (`docs/22_mcp/mcp_04_04_mdq.md`); all are rows in this Plan. `scripts/mcp_servers/mdq/mdq_server.py` reads the counter keys with `.get(..., 0)`, so added counters are additive and it is recorded as a reference file, not a target. Re-verified 20261127: the module and contract counts hold, and the only test module outside `tests/mcp_servers/mdq/` that imports a target module is `tests/mcp_servers/test_mdq_audit.py` (`from mcp_servers.mdq.indexer import index_paths`), which asserts the counter values; the seed scan does not reach it because it scans the `max_file_chars` seed only.

**Predictable fallout check (Step 3).**
- Module size gate (24576 B): `indexer.py` 14835 B, `mdq_models.py` 12071 B, `parser.py` 9551 B, `db_grep.py` 5094 B, `index_scan.py` 2759 B all have headroom.
- Pinned behavior that changes: `tests/mcp_servers/mdq/test_db_grep.py::test_line_number_for_match_on_later_line` asserts the chunk-relative line number; seven `text == "Indexing complete"` assertions in `tests/mcp_servers/mdq/test_mdq_service.py` split into two skip-only runs (`test_index_paths_skips_nonexistent`, `test_index_paths_skips_non_md_file`), two all-failed runs (`test_index_paths_records_failed_count_on_file_error`, `test_index_paths_records_failed_count_on_directory_error`, which become the all-files-failed tool error), and three runs with committed work (`test_index_paths_md_file_returns_complete`, `test_index_paths_directory_returns_complete`, `test_index_paths_delegates`); `test_oversized_file_is_skipped_with_warning` asserts the message text `exceeds max_file_chars`; `tests/mcp_servers/mdq/test_mdq_config.py` pins the key name in the default assertion and the parametrized field list; `tests/mcp_servers/mdq/test_parser.py::test_invalid_yaml_syntax_falls_back_to_empty_tags` pins the fallback that must stay.
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py::test_failed_reindex_does_not_record_the_new_mtime` passes only through a monkeypatched `_index_single_file` that raises; the swallowed write failure is pinned only on its rollback side, so the new test file is what closes the outcome side of that gap.
- `parse_markdown()` returns a two-value tuple at thirteen unpacking test call sites (two in `tests/mcp_servers/mdq/test_parser.py`, eleven in `tests/mcp_servers/mdq/test_mdq_service.py`; seventeen call sites in total); the warning record changes that contract, so those call sites are rewritten in Phase 1.
- Counter consumer outside this Plan's rows: `tests/mcp_servers/test_mdq_audit.py::TestIndexPathsAudit.test_mixed_scenario_counts` asserts the audit detail lines `indexed_count=1`, `skipped_count=2`, `failed_count=0` for three requested paths (one committed file, one nonexistent path, one non-Markdown file). It is not a row of this Plan and is owned by `plans/done/20261127-160114_mdqmcp001_mdq-server-boundary.md` for redaction tests only. It stays passing only while `skipped_count` remains the path-level counter; if REQ-003 makes `skipped_count` a file-level counter, that assertion changes and the file needs its own row (UNK-06). No other test file outside this Plan's rows asserts the counters or the outcome text.

## Implementation steps
1. **Phase 1: Characterization tests first**
   - [ ] Write the DTO-based outcome tests for the internal swallow, the size skip, file disappearance, and no-content cases before any production change (REQ-001, REQ-002; `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py`)
   - [ ] Pin the current grep behavior: chunk-relative line number, missing context, one match per chunk, and the zero-context default replacement (REQ-006; `tests/mcp_servers/mdq/test_db_grep.py`)
   - [ ] Pin the current counter unit and the outcome text, then rewrite them for `partial_success` and the all-files-failed tool error (REQ-003; `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_mdq_service.py`)
   - [ ] Add the byte-versus-character cases and the scan-semantics cases, and the structured frontmatter warning test (REQ-004, REQ-005, REQ-007; `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_scan_semantics.py`, `tests/mcp_servers/mdq/test_parser.py`)
2. **Phase 2: Per-file result DTO**
   - [ ] Define the DTO, the status vocabulary, the reason codes, and the warning-count field, and add the grep context fields to the match model (REQ-001, REQ-006, REQ-007; `scripts/mcp_servers/mdq/mdq_models.py`)
   - [ ] Return the DTO from the per-file path and tally from its status (REQ-001; `scripts/mcp_servers/mdq/indexer.py`)
3. **Phase 3: Post-commit state and counters**
   - [ ] Advance `index_state` only after a successful commit (REQ-002; `scripts/mcp_servers/mdq/indexer.py`)
   - [ ] Separate the input-path, discovered, committed, skipped, and failed counts, make the directory unit describe files in both modes, and report `partial_success` and the all-files-failed tool error (REQ-003; `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_service.py`)
4. **Phase 4: Units and scan semantics**
   - [ ] Rename the size-limit key to `max_file_bytes` across the model, the service attribute, the validated key list, the config file, and the tests (REQ-004; `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/mdq_security_validation.py`, `config/mdq_mcp_server.toml`, `tests/mcp_servers/mdq/test_mdq_config.py`)
   - [ ] Apply `fnmatchcase` on normalized root-relative POSIX paths, deduplicate by canonical path, and state the symlink-directory behavior (REQ-005; `scripts/mcp_servers/mdq/index_scan.py`)
   - [ ] Re-authorize and re-stat each discovered file before the read (REQ-005; `scripts/mcp_servers/mdq/indexer.py`)
5. **Phase 5: Grep correctness**
   - [ ] Return the requested context, compute the line number from the stored `start_line` with the synthetic heading offset, support multiple matches per chunk, and apply the limit to the context-inclusive text (REQ-006; `scripts/mcp_servers/mdq/db_grep.py`)
   - [ ] Honor an explicit zero context, changing `or` to an explicit `None` test (REQ-006; `scripts/mcp_servers/mdq/mdq_service.py`)
6. **Phase 6: Parser warnings**
   - [ ] Emit the structured `invalid_frontmatter` warning and its count without an absolute path, keeping the permissive fallback (REQ-007; `scripts/mcp_servers/mdq/parser.py`)
7. **Phase 7: Documentation**
   - [ ] Update the MDQ server contract doc for the statuses, counters, units, scan and symlink semantics, grep location and context, and parser warnings, and rewrite the `max_file_chars` statement (REQ-008; `docs/22_mcp/mcp_04_04_mdq.md`)
   - [ ] Run the full validation sequence in `rules/toolchain.md` including `uv run python tools/check_module_size.py` and `uv run python tools/check_docs_content_policy.py`

### Release units
**Unit**: per-file-outcome-and-counters | **Phases**: 1, 2, 3 | **Reason**: the Phase 1 tests assert the DTO statuses and the post-commit rule that only land in Phases 2 and 3, so Phase 1 cannot be validated alone.
**Unit**: byte-limit-key-rename | **Phases**: 4, 7 | **Reason**: the renamed key, the model field, the validated key list, the tests, and the doc statement must land in the same commit; the code change alone breaks the deployed config and the pinned tests.
**Unit**: grep-context-and-line-numbers | **Phases**: 1, 5 | **Reason**: Phase 1 pins the current chunk-relative line number and the missing context that Phase 5 replaces.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/indexer.py` | Unit for the DTO statuses and the post-commit rule; integration for a mixed-success directory and retry after failure | `uv run pytest tests/mcp_servers/mdq/test_mdq_index_internal_failures.py tests/mcp_servers/mdq/test_mdq_incremental_refresh.py tests/mcp_servers/mdq/test_mdq_service.py` | A skipped or failed file never advances `index_state` and is never counted as committed; the counters name distinct units; a mixed run reports `partial_success`; an all-failed run raises the tool error |
| `scripts/mcp_servers/mdq/mdq_models.py` | Unit for the DTO, the reason codes, and the renamed configuration field | `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py tests/mcp_servers/mdq/test_db_grep.py` | Statuses and reason codes are the closed vocabulary; the byte field validates; the match model carries context |
| `scripts/mcp_servers/mdq/index_scan.py` | Unit for canonical deduplication, case behavior, nested exclude, duplicate include, and symlink behavior | `uv run pytest tests/mcp_servers/mdq/test_mdq_scan_semantics.py` | Matching is deterministic on normalized root-relative POSIX paths; a symlinked duplicate is deduplicated; symlinked directories are not traversed |
| `scripts/mcp_servers/mdq/parser.py` | Unit for the structured warning and the unchanged fallback | `uv run pytest tests/mcp_servers/mdq/test_parser.py` | Invalid frontmatter still returns empty tags and produces a warning code and a count with no absolute path |
| `scripts/mcp_servers/mdq/db_grep.py` | Unit for returned context, source-file line numbers, multiple matches, multiline, and the limit on context-inclusive text | `uv run pytest tests/mcp_servers/mdq/test_db_grep.py` | Line numbers match the source file; the requested context including zero is returned; multiple matches are reported up to the cap |
| `scripts/mcp_servers/mdq/mdq_service.py` | Unit for zero context, the byte attribute, and the outcome text | `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py` | An explicit zero context is honored; the outcome text reflects `partial_success` |
| `scripts/mcp_servers/mdq/mdq_security_validation.py` | Unit for the renamed key | `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py` | The renamed key is validated at startup |
| Architecture boundary | Contract check | `PYTHONPATH=scripts uv run lint-imports` | Passes; `index_scan.py` gains no authorization or database dependency |
| Module size gate | Gate check | `uv run python tools/check_module_size.py` | No module crosses 24576 B |
| Static analysis | CI parity | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new errors |
| Coverage | Diff coverage | `uv run diff-cover coverage.xml --compare-branch=master` | At or above 90% on changed lines |
| Documentation | Content policy | `uv run python tools/check_docs_content_policy.py` | No implementation-detail content introduced |

## Risks
- **Risk**: the key rename is a compatibility change, so a deployed config that still uses `max_file_chars` fails startup validation after the code change. → **Mitigation**: the code, the config file, the tests, and the doc change in one commit (release unit `byte-limit-key-rename`); the compatibility note is written in the doc named by `docs/00_index.md`.
- **Risk**: changing the outcome text and the all-failed behavior changes observable tool output for runs that currently report success. → **Mitigation**: the affected assertions are listed in Implementation Target Files and rewritten in Phase 1, so the new behavior is pinned by tests rather than inferred.
- **Risk**: the grep line number cannot be exact for a section whose content had leading blank lines stripped at index time. → **Mitigation**: resolved by the owner on 20261127 (UNK-03) — the reported line is defined as the first stored content line and the definition is documented; the residual risk is that a reader expects the original file line for a section that began with blank lines, which the doc statement and a test pin.
- **Risk**: re-authorization and re-stat between scan and read add a second decision point, which can disagree with the scan result for a file replaced between the two. → **Mitigation**: the read path uses the re-authorized, re-statted path as the single source for the DTO, and the file-replacement scan test pins the outcome.
- **Risk**: `fnmatchcase` changes case behavior on a platform where `fnmatch.fnmatch` was case-insensitive. → **Mitigation**: the change makes case behavior explicit and documented; on the project's POSIX runtime the behavior is unchanged, and the scan test pins it.
- **Risk**: the DTO changes `parse_markdown()`'s return contract, which ten test call sites unpack. → **Mitigation**: the contract change is made in Phase 2 after the Phase 1 tests are written, and the call sites are listed in the predictable fallout check.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization tests first | Completed | — | 20261128-153123 | DTO outcomes, grep context and line numbers, counters, and units pinned before production change |
| 2 | Phase 2: per-file result DTO | Completed | — | 20261128-153123 | Status vocabulary, reason codes, warning counts, grep context fields |
| 3 | Phase 3: post-commit state and counters | Completed | — | 20261128-153123 | `index_state` advances only after commit; counters name their unit |
| 4 | Phase 4: units and scan semantics | Completed | — | 20261128-153123 | `max_file_bytes`, `fnmatchcase`, canonical dedup, re-authorization and re-stat |
| 5 | Phase 5: grep correctness | Completed | — | 20261128-153123 | Context returned, source-file line numbers, multiple matches, zero honored |
| 6 | Phase 6: parser warnings | Completed | — | 20261128-153123 | Structured `invalid_frontmatter` warning without absolute paths |
| 7 | Phase 7: documentation | Completed | — | 20261128-153123 | MDQ contract doc and doc content policy gate |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | UNK-03: the grep line-number offset for a section whose content had leading blank lines stripped at index time is not recoverable from the stored row, so `AC-5` could not be met exactly until the owner decided between storing the content offset at index time and defining the reported line as the first stored content line. Resolved by the owner on 20261127 with the second option, so `AC-5` is met under that definition and procedure generation is no longer blocked. | Yes | 20261127 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261127-225351_01_scripts_mcp_servers_mdq_mdq_models.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261127-225351_02_scripts_mcp_servers_mdq_indexer.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261127-225351_03_scripts_mcp_servers_mdq_index_scan.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261127-225351_04_scripts_mcp_servers_mdq_parser.py.md` | 6 | Procedure | Completed | — | — |
| `implementations/20261127-225351_05_scripts_mcp_servers_mdq_db_grep.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261127-225351_06_scripts_mcp_servers_mdq_mdq_service.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261127-225351_07_scripts_mcp_servers_mdq_mdq_security_validation.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261127-225351_08_config_mdq_mcp_server.toml.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261127-225351_09_tests_mcp_servers_mdq_test_db_grep.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261127-225351_12_tests_mcp_servers_mdq_test_mdq_service.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261127-225351_13_tests_mcp_servers_mdq_test_mdq_config.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261127-225351_16_docs_22_mcp_mcp_04_04_mdq.md.md` | 7 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-163030
- **Evidence revision**: 1ea69ed7f1415545ca2c75f531e8a9376939ddad
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/index_scan.py`, `scripts/mcp_servers/mdq/parser.py`, `scripts/mcp_servers/mdq/db_grep.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/mdq_security_validation.py`, `config/mdq_mcp_server.toml`, `tests/mcp_servers/mdq/test_db_grep.py`, `tests/mcp_servers/mdq/test_parser.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_config.py`, `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py`, `tests/mcp_servers/mdq/test_mdq_scan_semantics.py`, `docs/22_mcp/mcp_04_04_mdq.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; per-file DTO with the status vocabulary and stable reason codes | `scripts/mcp_servers/mdq/mdq_models.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_config.py` | Confirmed by repository evidence |
| REQ-001 | Problem; callers count skipped files as success | `scripts/mcp_servers/mdq/indexer.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; update `index_state` only after commit | `scripts/mcp_servers/mdq/indexer.py` | Phase 3 | AC-1 | `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; separate input-path, discovered, committed, skipped, and failed counts | `scripts/mcp_servers/mdq/mdq_models.py` | Phase 3 | AC-2 | `tests/mcp_servers/mdq/test_mdq_config.py` | Confirmed by repository evidence |
| REQ-003 | Problem; directory counts mixing paths and files | `scripts/mcp_servers/mdq/indexer.py` | Phase 3 | AC-2 | `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; `partial_success` and a tool error when all files fail | `scripts/mcp_servers/mdq/mdq_service.py` | Phase 3 | AC-2 | `tests/mcp_servers/mdq/test_mdq_service.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; replace `max_file_chars` with `max_file_bytes` | `scripts/mcp_servers/mdq/mdq_models.py` | Phase 4 | AC-3 | `tests/mcp_servers/mdq/test_mdq_config.py` | Confirmed by repository evidence |
| REQ-004 | Constraints; the key rename is a compatibility change and must be documented | `config/mdq_mcp_server.toml` | Phase 4 | AC-3 | `tests/mcp_servers/mdq/test_mdq_config.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; startup validation of the renamed key | `scripts/mcp_servers/mdq/mdq_security_validation.py` | Phase 4 | AC-3 | `tests/mcp_servers/mdq/test_mdq_config.py` | Confirmed by repository evidence |
| REQ-004 | Testing Expectations; ASCII, Japanese, emoji, and BOM size-limit cases | `tests/mcp_servers/mdq/test_mdq_service.py` | Phase 1 | AC-3 | itself | Confirmed by repository evidence |
| REQ-005 | Required Changes; normalized root-relative POSIX matching, canonical deduplication, documented case sensitivity | `scripts/mcp_servers/mdq/index_scan.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_mdq_scan_semantics.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; re-authorization and re-stat between scan and read | `scripts/mcp_servers/mdq/indexer.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_mdq_scan_semantics.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; return requested context before and after matches | `scripts/mcp_servers/mdq/db_grep.py` | Phase 5 | AC-5 | `tests/mcp_servers/mdq/test_db_grep.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; compute line numbers from stored `start_line` with the synthetic heading offset | `scripts/mcp_servers/mdq/db_grep.py` | Phase 5 | AC-5 | `tests/mcp_servers/mdq/test_db_grep.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; only `None` selects defaults, zero is honored | `scripts/mcp_servers/mdq/mdq_service.py` | Phase 5 | AC-5 | `tests/mcp_servers/mdq/test_mdq_service.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; structured `invalid_frontmatter` warnings and counts without absolute paths | `scripts/mcp_servers/mdq/parser.py` | Phase 6 | AC-6 | `tests/mcp_servers/mdq/test_parser.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; file-result statuses, counters, and byte versus character limits | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 7 | AC-3 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; scan, symlink, grep, and parser-warning semantics | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 7 | AC-4, AC-5, AC-6 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261127-225351 -->
