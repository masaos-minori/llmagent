# Implementation Procedure: `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`

**Plan**: [20261023-183637 Turn006 history compression reorders and duplicates the summary and the fallback truncation drops whole tool units](../plans/20261023-183637_plan.md)
**Related**: [issues/done/20261021-093421_turn006_history-compression-reorders-and-duplicates-summary.md](../issues/done/20261021-093421_turn006_history-compression-reorders-and-duplicates-summary.md)

## Goal

Rewrite the chapter sections that state the history-compression contract so they describe what rows 1 and 2
implement: whole-turn-unit oldest-first selection, unit-atomic fallback truncation, one summary message replaced in
place with the previous summary carried forward, and the estimate-based token gate `compress()` actually uses. This is
the documentation half of `REQ-009` and `AC-9`.

## Scope

One file: `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` (123 lines, 7030 bytes at HEAD
`2c2bbcce9`). Frozen ranges from the Plan's target-table row 5 and `Phase 4 (7)`: `:35-49`, `:51-58`, `:82-84`,
`:101-116`.

- `### Selection of Targets for Compression` (`:35-45`): replace the four-category model (`:40-44`) with the unit
  contract (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`).
- `### Compression Results` (`:47-49`): single-summary replacement, prior-summary carry-forward, and the reported
  counters including `summary_chars` (new) (`REQ-005`, `REQ-007`).
- `### Fallback Decision on Failure` (`:51-58`): `:53-56` keep their branching shape and the `error=` literal; `:58`
  changes from per-message deletion to whole-unit dropping (`REQ-006`).
- `### Token Counting` (`:82-84`): correct the "LLM `usage.input_tokens` (accurate) first" claim to what `compress()`
  does (`history.py:346-353`, `config/agent.toml:65`).
- `### Ensuring Protected Pairs` (`:101-103`) and `### Character Limit Behavior` (`:105-107`) under `## Key
  Constraints` (`:99`).
- Review `## Operational Notes` (`:109-112`) and `## Known Limitations` (`:114-116`), the rest of the frozen `:101-116`
  range, and record them as unchanged with the measured reasons in step 7.
- Do not edit the front matter (`:1-15`), `## Purpose` (`:22-24`), `## Design Intent` (`:26`), `### Compression
  Triggers` (`:28-33`), `### Compression Persistence Model` (`:60-71`), `## Responsibility Boundary` (`:73-80`), `###
  Data Classification` (`:86-97`), `## Keywords` (`:118-123`), or any heading name: `:58` cross-references "Key
  Constraints, Character Limit Behavior", and `agent_12_reference-api.md:147`, `agent_07_09_*.md:46`, `agent_04_01_*.md`
  and `governance_03_issue-and-uncertainty-management.md:18` link to this file.

## Assumptions

- Rows 1 and 2 have landed before this procedure runs. The rewritten text names
  `HistorySelectionPolicy.group_turn_messages()`, `HistorySelectionPolicy.group_importance()` and `summary_chars` (new), none
  of which exist at HEAD. Two consequences: `tools/stale_detector.py` reports a backticked name as `symbol_missing`
  when it is absent from every `.py` file (`_check_symbol_refs`, `:609-689`), so the required pre-execution stale check
  (`skills/code-implementation/workflow.md:171`) passes only after rows 1 and 2 land; and
  `check_docs_consistency.py`'s function-reference check (`tools/_docs_consistency_lib.py:477-499`) reports a
  backticked `name()` with no matching definition in the source.
- Rows 3 and 4 have landed, so the test names in the Validation plan resolve and the regression counts hold.
- `check_docs_structure.py "docs/**/*.md"` is clean at HEAD. Its former blocking finding
  (`agent_13_reference-api-generated.md: size 24961 bytes exceeds 24576 byte limit`, measured 2026-10-24) was closed
  by an owner-approved `SIZE_EXCEPTIONS` ceiling of 24972 (`tools/check_docs_structure.py:83-115`, 2026-10-24,
  `BLK-001`), so a fully clean structural run is available as `AC-9` evidence. The ceiling is pinned to the size the
  generated block reaches once `plans/20261023-072425_plan.md` REQ-005 regenerates it; this row's own 7030 bytes is
  nowhere near it, and this row does not touch the generated file.
- The other docs gates are clean at HEAD and measured: `check_docs_consistency.py --domain agent`,
  `--domain overview`, `check_docs_content_policy.py` and `check_docs_quality.py` all report no issue.
- Document line numbers are measured against the current file. Rows 1 and 2 change only source files, so this
  document's own line numbers stay valid while the procedure is executed.

## Design decisions

- **Rewrite whole subsections; keep every heading name and the section order.** `:58` cross-references "Key
  Constraints, Character Limit Behavior", `tools/check_docs_structure.py` resolves cross-links from front matter
  `related:` as the single cross-reference store (`check_docs_structure.py:5-6`), and four documents link here; a
  renamed heading would break them and the Plan's own `:101-107` citation.
- **Keep `classify_importance()` documented, add no scoring section.** `agent_04_02:58` is the only line in `docs/`
  that names `classify_importance()` (Plan `:788`), and `DR-004` leaves its thresholds unchanged; the rewritten `:58`
  keeps the reference through `group_importance()`, so the function stays documented where it is used and no
  duplicated score list is introduced.
- **Cite symbols, not source line numbers, in the document body.** Rows 1 and 2 delete source lines
  (`history.py:32`, `history_selection_policy.py:44-63,95-119`), shifting every later line number; the chapter carries
  no source line citations today, and adding them would make it stale the moment the code lands.
- **State the token gate as implemented behavior.** The frozen row's reason for `:82-84` is that it "claims an
  LLM-`usage.input_tokens` priority that `compress()` never uses"; the replacement names the three sources
  `count_tokens_async()` can use and which one the trigger actually reaches with `tokenize_url = ""`. The estimator is
  the category-aware one in `scripts/shared/token_estimation.py:14-16`, not `chars // 4` — see the
  `Corrections from re-measurement` section of the Plan in the
  Traceability section for the Plan wording this corrects.
- **Keep the soft-limit framing at `:105-107`** and change only the drop granularity: `REQ-006` keeps the soft-limit
  WARNING and the "never drop protected messages" rule unchanged.

## Alternatives considered

- **Delete `### Data Classification` (`:86-97`) together with the category model.** Rejected: the frozen row's
  "four-category model" is `:40-44` (`temporary`, `temporary_reasoning`, `factual`, `history`), while `:86-97` is a
  session-versus-memory persistence table unrelated to `classify()`. Editing it is outside this row's evidence.
- **Move the importance-score list into `agent_12_reference-api.md`.** Rejected: `agent_12:147` defers full details to
  this chapter, `agent_12` is outside the Plan's allowed edit scope, and its generated sibling already exceeds the
  structural size limit.
- **Rewrite `## Operational Notes` to describe unit-atomic fallback under `/compact`.** Rejected as unnecessary:
  `force_compress()`'s mechanism (`history.py:127-139`) and the two exposed counters (`cmd_config_stats.py:83-88`) are
  unchanged, and the granularity change is documented in `### Character Limit Behavior`. Recorded as a reviewed region
  instead.
- **Add a Needs-Confirmation marker for how the summarizer handles the carried summary.** Rejected: `UNK-04` is
  tracked in the Plan, and the chapter states the observable guard (`summary_chars` (new) plus the WARNING) rather than
  claiming the summarizer preserves the carried summary.

## Implementation

### Target file

`docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`

### Procedure

1. Replace `### Selection of Targets for Compression` (`:35-45`) with:

   ```markdown
   ### Selection of Targets for Compression

   `HistorySelectionPolicy.select_turns_to_compress()` groups the non-`system` messages into turn units and selects
   whole units:

   1. **Unit grouping** — a unit starts at a `user` message and holds every `assistant` and `tool` message until the
      next `user` message; messages before the first `user` message form a leading unit, so a `tool` row whose
      `assistant` message was compressed in an earlier cycle is a unit of its own. Concatenating the units reproduces
      the input exactly.
   2. **Oldest-first selection** — whole units are taken from the front until the cumulative message count reaches
      `context_compress_turns * 2`; the last unit may overshoot it, so `compressed_count` can exceed the quota.
      `to_compress` and `remaining` are returned in history order.
   3. **Pinned units** — a unit containing a message with the `pinned` key set is never selected and stays in
      `remaining` in place.
   4. **Protection** — whole units are protected from the end until the cumulative message count reaches
      `history_protect_turns * 2`; the boundary rounds outward and never splits a unit.
   5. **System messages** — every `system` message is split out before selection and is never a candidate; summary
      rows are taken out of them and recompressed with the transcript (see Compression Results).
   6. **No selection** — returns `None` when no whole unit can be taken, and `compress()` then logs a skip warning
      without modifying history.

   Selection identifies messages by unit position, never by value equality, so
   `len(system_msgs) + len(to_compress) + len(remaining) == len(history)` for every input and two messages with
   identical content are both accounted for. Importance scoring does not order selection; it orders fallback drops (see
   Fallback Decision on Failure).
   ```

   The deleted items 1-2 (`:39-44`) documented `partition_by_class()`'s four buckets, whose `factual` bucket is always
   empty because `system` messages are split out first (`turn006_probe1.out`: `factual is empty: True`). Item 3
   (`:45`) survives as item 4 in units.

2. Replace `### Compression Results` (`:47-49`) with:

   ```markdown
   ### Compression Results

   The selected units are replaced by exactly one `system` message whose content starts with `[Conversation summary]`.
   The previous summary text is handed to the summariser in a `PREVIOUS SUMMARY:` block ahead of the transcript, and
   the old summary row is removed, so the summary is carried forward in place instead of accumulating rows: an input
   that already holds several summary rows produces one. `HistoryManager`'s compression counter increments, and
   `CompressResult` reports `compressed_count` (messages replaced), `protected_count` (retained turn messages),
   `summary_added=True` and `summary_chars` (new) (the length of the new summary). The INFO log names `summary_chars` (new), and a
   WARNING is logged when `summary_chars >= count_chars(to_compress)` — the summary is not smaller than the messages it
   replaced. The relative comparison is used because the summariser input caps every message at 300 characters
   (`_build_history_text()`), which is what let a 16-message history produce a 1296-character summary block.
   ```

   The old `:49` states "a single LLM summary message" without saying the previous summary is replaced, and reports
   only "how many messages were replaced and how many were protected"; the measured `protected_count` was 3 against 4
   retained messages (`turn006_probe5.out`, `history.py:387`), which row 2 fixes.

3. Replace `### Fallback Decision on Failure` (`:51-58`) with:

   ```markdown
   ### Fallback Decision on Failure

   If `HistoryManager.compress()` fails to call the summarization LLM, a `HistoryCompressionError` is raised but caught
   internally, returning `None` and logging a WARNING. Subsequent branching:

   - **If character limit is still exceeded** → Falls through to fallback truncation, dropping whole turn units
     without summarization.
   - **If character limit is no longer exceeded** → Returns as a no-op without modifying history
     (`CompressResult(compressed_count=0, ...)`).

   Fallback truncation protects every `system` message plus the whole units covering the last `history_protect_turns`
   pairs, groups the remaining candidates into whole units, orders them by `HistorySelectionPolicy.group_importance()`
   (the highest `classify_importance()` score inside the unit) ascending, and deletes one whole unit per iteration from
   candidates that exclude the `system` role and the protected units until the character limit is met or a further drop
   would leave fewer than one message (soft-limit behavior: see Key Constraints, Character Limit Behavior). A
   `user`/`assistant` unit and its `tool` results are never split, so no `tool` row is orphaned. This path sets
   `CompressResult.is_fallback=True`, `summary_added=False` and `summary_chars=0`, reports `compressed_count` as the
   number of dropped messages, and increments `HistoryManager.stat_fallback_truncate_count`.
   ```

   `:53` and `:56` are re-typed unchanged except for the drop wording in `:55`: the old `:55` says "performing
   mechanical deletion of low-importance messages" and the old `:58` says candidates "deletes them one by one from
   candidates that exclude the `system` role and the most recent `protect_turns` pairs" — the per-message form is what
   orphaned the `tool` rows in the turn006 incident.

4. Replace the `### Token Counting` body (`:84`) with:

   ```markdown
   `count_tokens_async()` prefers: (1) an exact `last_input_tokens` value supplied by the caller, (2) the `/tokenize`
   endpoint when `tokenize_url` is set, (3) the category-aware estimate in `scripts/shared/token_estimation.py` — 4.0
   characters per token for text, 2.5 for serialized tool calls, 3.5 for `system` messages. The compression trigger
   consults tokens only when the character limit is not already exceeded and `context_token_limit` is greater than 0.
   It never supplies `last_input_tokens`, and `config/agent.toml` sets `tokenize_url = ""`, so the trigger compares the
   category-aware estimate against `context_token_limit`. The exact per-turn count reaches `count_tokens()` only from
   `scripts/agent/services/context_view.py`, which passes the previous turn's `last_input_tokens` for the pre-turn
   decision.
   ```

   Keep the `### Token Counting` heading (`:82`). The old `:84` reads "Priority: (1) LLM's `usage.input_tokens`
   (accurate), (2) `/tokenize` endpoint (accurate), (3) Fallback to the category-aware estimate (see
   `scripts/shared/token_estimation.py`)": the field name is wrong (the code reads `usage.prompt_tokens`,
   `history.py:190`) and the priority is not the one the trigger follows, because `compress()` never passes
   `last_input_tokens` (`history.py:346-353`) and `tokenize_url` is empty (`config/agent.toml:65`). The rewritten
   sentence keeps the `scripts/shared/token_estimation.py` reference so the file-reference check still resolves it.

5. Replace the `### Ensuring Protected Pairs` body (`:103`) with:

   ```markdown
   The last `history_protect_turns` user+assistant pairs are protected as whole units: the boundary rounds outward to
   the start of the unit it enters, and `select_turns_to_compress()` and `_build_protected_ids()` apply the same rule so
   selection and fallback protection agree. A unit containing a pinned message is never compressed and never dropped.
   ```

   The old `:103` claim is count-based, which is what let a 3-pair setting protect 3 messages instead of 3 pairs' worth
   of unit messages.

6. Replace the `### Character Limit Behavior` body (`:107`) with:

   ```markdown
   Fallback truncation drops only unprotected whole units, lowest unit importance first, until the character limit is
   met or a further drop would leave fewer than one message. The `system` messages (including the summary) and the
   protected recent units are never dropped, so when they alone exceed the limit the limit is a soft limit: processing
   continues and a WARNING is logged. Protected messages are never dropped silently to reach the limit. Individual
   messages can also exceed `char_limit`.
   ```

   The soft-limit conclusion and the final sentence of the old `:107` stay; only "unprotected messages" becomes
   "unprotected whole units".

7. Read `## Operational Notes` (`:109-112`) and `## Known Limitations` (`:114-116`) and record them as unchanged in
   this procedure's Execution Status. Measured reasons: `:111` matches `force_compress()` (`history.py:127-146`), which
   still sets `char_limit=1` and `token_limit=0` and then restores both; `:112` names `stat_compress_count` and
   `stat_fallback_truncate_count` (`history.py:89-91`), which is exactly what `/config stats` reports
   (`cmd_config_stats.py:83-88`), and row 2 adds no new `stat_*` field, so the sentence stays accurate; the
   memory-extraction limitation at `:116` is untouched by the selection change.

### Method

Rewrite subsection by subsection using the exact old sentences quoted in steps 1-6 as the match anchors, then run the
documentation checkers in the Validation plan. Touch no source file: a source edit here would collide with rows 1-2 and
with `check_docstrings.py`'s baseline.

### Details

- Backticked names the rewrite introduces (`group_turn_messages()`, `group_importance()`, `summary_chars` (new)) exist only
  after rows 1-2 land; that is why this row runs last-but-one and why the pre-execution stale check must run after
  them.
- Write function names with `()` in the document body: `tools/stale_detector.py`'s symbol pattern
  (`_SYMBOL_RE`, `:56`) skips names that carry punctuation, while bare field names are checked against the source.
- Keep `:56`'s `CompressResult(compressed_count=0, ...)` parenthetical as written. The no-op branch also sets
  `error="compression returned None"` (`history.py:289`), which the chapter does not document today; documenting it
  would extend beyond this row's frozen ranges.
- Front matter (`:1-15`) stays byte-identical: `related:` is the cross-reference store and this procedure adds no new
  document relationship, so `check_docs_structure.py`'s link and duplicate checks are unaffected.
- Size stays far below the 24576-byte structural limit (7030 bytes at HEAD), so no `SIZE_EXCEPTIONS` entry is involved
  for this file.
- `scripts/shared/token_estimation.py` (`:84`) is the only source path this document cites, and step 4 keeps the
  citation, so `check_docs_consistency.py`'s file-reference check keeps resolving it.

## Compatibility considerations

- Documentation-only change: no import-layer, public-contract, config, or test change, and `REQ-008`'s docstring
  rewrites belong to rows 1-2.
- `agent_12_reference-api.md:142-147` describes `HistoryManager.compress()` generically and defers details here; no
  edit is needed and none is made.
- `agent_13_reference-api-generated.md:83-85` quotes the first docstring line of `HistoryManager`, `CompressResult`
  and `HistorySelectionPolicy`. Row 1 keeps the policy class docstring's first line byte-identical (`UNK-06`) and row 2
  keeps the other two first lines, so regenerating the table produces no diff for this chapter. Regeneration is not
  part of this procedure and the file is in the Plan's forbidden edit scope.
- `check_docs_consistency.py` reports `No issues found.` for `--domain agent` and `--domain overview` at HEAD; this
  procedure must keep both clean, including the function-reference check that would report a leftover `classify()` or
  `partition_by_class()` mention.
- Observed drift outside this row's scope: `history.py:192` documents the fallback estimator as `chars // 4` while the
  implementation reaches the category-aware estimator through `get_token_count` (`history.py:198-200`,
  `token_counter.py:93-94`). The chapter describes the implementation; the source docstring is not edited because no
  frozen row authorizes it (`BLK-002`).

## Security considerations

No secrets, endpoints, or configuration values are introduced. The document names existing keys (`tokenize_url`,
`context_char_limit`, `context_token_limit`, `context_compress_turns`, `history_protect_turns`). No command in this
procedure writes outside the target file.

## Rollback considerations

```bash
git checkout -- docs/23_agent/agent_04_02_state-and-persistence-history-compression.md
```

Then re-run `uv run python tools/check_docs_consistency.py --domain agent` to confirm the reverted document is clean on
its own. Rolling back rows 1-2 needs no extra action here: the document cites symbols rather than line numbers, so
re-running this procedure against the reverted source is the only follow-up.

## Validation plan

### Target tests

- None: no test asserts the content of this chapter. The tests listed under Regression tests cover the behavior the
  chapter describes, not the document.

### Test strategy

- `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect only the pre-existing `agent_13` size finding
  from `## Assumptions`, and no finding for `agent_04_02`.
- `uv run check-agent-docs` and `uv run python tools/check_docs_consistency.py --domain agent` — expect `No issues
  found.`; these are the checks that report a leftover `classify()` / `partition_by_class()` / `sort_by_importance()`
  reference or a broken internal link.
- `uv run python tools/generate_reference_table.py --type agent --check` — expect no `DRIFT:` output (`AC-8`),
  confirming the docstring lines the generated table copies were not disturbed.
- `uv run python tools/check_docs_content_policy.py` and `uv run python tools/check_docs_quality.py` — expect no
  finding for this file.
- Deleted-model residue: `grep -rn "temporary_reasoning" docs/` and `grep -rn "partition_by_class" docs/` must return
  no match after steps 1 and 3.
- `uv run python tools/stale_detector.py implementations/20261024-061024_05_docs_23_agent_agent_04_02_state-and-persistence-history-compression.md.md`
  — expect `Procedure is not stale` only when run after rows 1-2 have landed.

### Regression tests

- `uv run pytest tests/agent/test_history_selection_policy.py tests/agent/test_history_manager.py tests/agent/test_history_compression_consistency.py tests/agent/test_history_manager_new.py tests/agent/test_regression_history_compress_reload.py -q`
  → expect `117 passed` (`24` + `72` + `14` + `2` + `5`; the same command reports `103 passed` before rows 1-4 land),
  confirming this documentation-only row left the source untouched.

## Completion criteria

- Steps 1-6 applied, step 7's reviewed regions recorded as unchanged, the four docs checkers report no finding for this
  file, `generate_reference_table.py --check` reports no drift, and both residue greps return no match.
- Partial when a heading is renamed, a deleted category name survives anywhere in `docs/`, the chapter still claims an
  exact-token priority for `compress()`, or the `agent_13` size finding is reported as caused by this procedure.

## Out of Scope

- `docs/00_index.md` (row 6), `docs/23_agent/agent_12_reference-api.md`,
  `docs/23_agent/agent_13_reference-api-generated.md`, `docs/23_agent/agent_04_01_*`, `### Data Classification`
  (`:86-97`), `## Operational Notes` (`:109-112`), `## Known Limitations` (`:114-116`), `## Keywords` (`:118-123`).
- Regenerating the API reference table, and the `agent_13` size exception (`BLK-001`).
- The `history.py:192` docstring `chars // 4` drift (`BLK-002`).
- Any claim about how the real summarizer handles the `PREVIOUS SUMMARY:` block (`UNK-04`, gated on
  `tests/live/test_live_summarization_smoke.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `:35-49` (Selection of Targets, Compression Results) | Completed | 20261025-001445 | 20261025-001445 | Requires rows 1-2 landed Applied; headings and section order preserved; temporary_reasoning/partition_by_class residue greps clean |
| 2 | Rewrite `:51-58` (Fallback Decision) and `:82-84` (Token Counting) | Completed | 20261025-001445 | 20261025-001445 | Keep `:53`, `:55` and the `:82` heading Applied; :53/:55 branching shape and error= literal kept; :82 heading kept |
| 3 | Rewrite `:101-107` (Ensuring Protected Pairs, Character Limit Behavior) | Completed | 20261025-001445 | 20261025-001445 | Soft-limit conclusion and last sentence stay Applied; soft-limit conclusion and last sentence kept |
| 4 | Review `:109-116`, run the docs checkers and residue greps | Completed | 20261025-001445 | 20261025-001445 | `:109-116` recorded as unchanged with measured reasons :109-116 (Operational Notes, Known Limitations) reviewed, unchanged with measured reasons (force_compress char_limit/token_limit restore; stat_compress_count/stat_fallback_truncate_count via ctx.services.hist_mgr; memory-extraction limitation). Four docs checkers + generate_reference_table --check + residue greps clean. stale_detector temporary_reasoning symbol_missing is a false positive on the removed category name (see Blocker Log) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `check_docs_structure.py` reported `agent_13_reference-api-generated.md: size 24961 bytes exceeds 24576 byte limit` at HEAD, and CI runs that checker as a blocking step (`BLK-001`) | Yes — owner approved a `SIZE_EXCEPTIONS` ceiling at `tools/check_docs_structure.py:114`; the accepted value is 24972, the size measured after the `20261023-072425` Plan regenerated that document, so the full `docs/**/*.md` run reports no issue | 2026-10-24 |
| 1 | `history.py:192` docstring names `chars // 4` as the fallback estimator while the implementation uses the category-aware estimator (`BLK-002`) | No — not in any frozen row's scope; recorded so the chapter and source are not silently contradictory | — |
| 4 | `stale_detector.py` reports `temporary_reasoning` as `symbol_missing` when run post-execution (`_check_symbol_refs`, `:609-689`) | Yes — false positive: `temporary_reasoning` is a category name cited only in this procedure's Alternatives section describing the rejected four-category model (`temporary`, `temporary_reasoning`, `factual`, `history`); rows 1 and 2 removed it from source, so it is absent from every `.py` file. It is a descriptive historical reference, not a construct the execution depends on, and this row's Completion criteria list the four docs checkers, `generate_reference_table.py --check` and the two residue greps — not the stale detector. The document deliverable passes every governance checker | 2026-10-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-005`, `REQ-006`, `REQ-007`, `REQ-009`
- **Source issue**: issues/done/20261021-093421_turn006_history-compression-reorders-and-duplicates-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-183637_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-061024
- **Related target files**: docs/23_agent/agent_04_02_state-and-persistence-history-compression.md

- Related procedures: [20261024-061024_01 (history_selection_policy.py)](20261024-061024_01_scripts_agent_history_selection_policy.py.md),
  [20261024-061024_02 (history.py)](20261024-061024_02_scripts_agent_history.py.md),
  [20261024-061024_06 (docs/00_index.md)](20261024-061024_06_docs_00_index.md.md)
- Corrections to the Plan (the Plan's frozen rows are not rewritten):
  - `REQ-009` (`:193-194`) says the gate "uses a `chars // 4` estimate" with `tokenize_url = ""`. Measured: with an
    empty `tokenize_url`, `get_token_count` returns `estimate_tokens`' category-aware figure (`token_counter.py:93-94`,
    `token_estimation.py:14-16`; ratios 4.0 text / 2.5 tool calls / 3.5 `system`). `chars // 4` is the wording of
    `history.py:192`'s own stale docstring, not of the chapter: `agent_04_02:84` already names the category-aware
    estimator, so step 4 corrects only the priority claim and the `usage.input_tokens` field name.
  - The target-table row 5 evidence column cites `:101-116` while its reason column cites `:101-107`. Measured:
    `:101-107` are the two `## Key Constraints` subsections this row rewrites; `:101-116` also covers `## Operational
    Notes` and `## Known Limitations`, which step 7 reviews and leaves unchanged.