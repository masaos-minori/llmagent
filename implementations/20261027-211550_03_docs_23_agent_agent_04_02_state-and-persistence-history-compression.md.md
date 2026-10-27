## Goal

Update the history-compression documentation so its fallback-on-failure description matches the post-`REQ-001` / `REQ-002` behavior: fallback now triggers on **both** character and token overflow (not character only), and the fallback drop condition is token-aware. (`REQ-001`, `REQ-002`, `REQ-004`)

## Scope

One documentation file, `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`:

1. "Fallback Decision on Failure" section — the two branching bullets currently gate only on the character limit; reword them to gate on "over the character limit or the token limit".
2. Fallback truncation stop-condition prose ("until the character limit is met") → "until both the character and token limits are met (token-aware)".
3. "Character Limit Behavior" section body — note the token-aware stop condition.

No production code or tests touched here (Rows 1 and 2).

## Assumptions

- The doc is the canonical home for `HistoryManager` compression, mapped via `docs/00_index.md` L155 → `agent_04_02_state-and-persistence-history-compression.md` (plan-verified); `docs/00_index.md` itself needs no change.
- Current doc "Fallback Decision on Failure" (`L79`-`L82`) branches only on the character limit, which is stale once `compress()` falls back on `over_char or over_token`.
- The "Compression Triggers" section (`L30`-`L33`) already documents both char and token triggers, so aligning the fallback section to both triggers keeps the doc internally consistent.
- Docs are written in English (`skills/DESIGN.md` output-language rule).

## Design decisions

- Keep the change minimal and localized to the fallback description: change the two branching bullets and the stop-condition prose so they name both limits. Do not rewrite the trigger, selection, or persistence sections, which are unaffected.
- Leave the "Character Limit Behavior" section heading as-is (it describes the soft-limit edge where protected/system messages exceed the limit); only update its body to mention the token-aware stop condition.

## Alternatives considered

- Renaming the "Character Limit Behavior" heading to "Limit Behavior" — rejected: out of scope for this change and would shift downstream line citations; the body edit is sufficient.

## Implementation

### Target file
`docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`

### Procedure
1. In "Fallback Decision on Failure", replace the bullet "**If character limit is still exceeded** → Falls through to fallback truncation, dropping whole turn units without summarization." with a bullet that fires when the history is over the character limit **or** the token limit.
2. Replace the bullet "**If character limit is no longer exceeded** → Returns as a no-op without modifying history (`CompressResult(compressed_count=0, ...)`)..." with a bullet that returns the no-op only when neither the character nor the token limit is exceeded.
3. In the fallback-truncation paragraph, change "until the character limit is met or a further drop" to "until both the character and token limits are met (token-aware) or a further drop".
4. In "Character Limit Behavior", add a clause that the soft-limit stop condition applies to the character limit and, when a token limit is configured (`context_token_limit > 0`), to tokens as well.

### Method
Four prose edits in one docs file; no new sections, no structural change.

### Details
- Before (current, `L79`-`L82`):
  > - **If character limit is still exceeded** → Falls through to fallback truncation, dropping whole turn units without summarization.
  > - **If character limit is no longer exceeded** → Returns as a no-op without modifying history (`CompressResult(compressed_count=0, ...)`).
  After:
  > - **If over the character limit or the token limit** → Falls through to fallback truncation, dropping whole turn units without summarization.
  > - **If neither the character nor the token limit is exceeded** → Returns as a no-op without modifying history (`CompressResult(compressed_count=0, ...)`).
- Before (fallback stop condition, `L88`): "...candidates that exclude the `system` role and the protected units until the character limit is met or a further drop would leave fewer than one message..."
  After: "...candidates that exclude the `system` role and the protected units until **both the character and token limits are met (token-aware)** or a further drop would leave fewer than one message..."
- "Character Limit Behavior" (`L149`-`L155`): append that the soft-limit applies to the character limit and, when `context_token_limit > 0`, to the token limit too, so the warning covers both measurements.

## Compatibility considerations

- The doc is reached via `related:` links and ADR cross-references; editing fallback prose does not change any link target, heading structure, or front matter, so internal link reachability is preserved.

## Security considerations

N/A: documentation-only change; no runtime surface.

## Rollback considerations

N/A: revert the commit. No config, schema, or deployed-state change.

## Validation plan

Run the documentation checkers named in `routing.md` "When to run which tool" for edited `docs/*.md`:

- `uv run python tools/check_docs_quality.py` — structural/formatting rules (headings, tables, code fences).
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` — file size, H1 count, front matter, Keywords, `Related Documents`/`Related Chapters` headings, front-matter `related:` format, internal link reachability.
- `uv run python tools/check_docs_content_policy.py --strict` — no implementation-detail warnings that point to a canonical source instead.
- `uv run python tools/check_docs_consistency.py --domain agent` — doc claims agree with `config/agent.toml` and `scripts/`.
- `uv run python tools/check_docs_japanese.py` — no Japanese text.

## Completion criteria

- The "Fallback Decision on Failure" section states that fallback triggers on character **or** token overflow and the no-op path fires only when neither limit is exceeded.
- The fallback stop-condition prose names both the character and token limits (token-aware).
- All five documentation checkers above pass.

## Out of Scope

- Production logic (`scripts/agent/history.py`) — Row 1.
- Tests (`tests/agent/test_history_manager.py`) — Row 2.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the fallback-section doc edits described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (`routing.md` "When to run which tool") | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-004`
- **Source issue**: issues/20261026-224931_history001_token-overflow-compression-fallback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074212_history001_token-overflow-compression-fallback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-211550
- **Related target files**: docs/23_agent/agent_04_02_state-and-persistence-history-compression.md
