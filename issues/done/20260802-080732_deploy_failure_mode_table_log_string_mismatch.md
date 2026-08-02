# Fix failure-mode table symptom-column log-string mismatch in docs/02_deployment-part2.md

## Priority
Medium

## Summary
`docs/02_deployment-part2.md` §3.3's failure-mode table lists symptom strings (`[FATAL] Invalid workflow definition`, `[FATAL] Checksum does not match source`, `[FATAL] Schema is missing or incomplete`, `[FATAL] Schema version mismatch`) that do not match the actual log strings emitted by `deploy.sh`/`init_db.sh`/`setup_services.sh`. The actual strings are, respectively: `[FATAL] Workflow definition failed validation; aborting deployment.`, `[FATAL] Deployed workflow definition checksum does not match source; deployment corrupted.`, `[FATAL] Workflow database schema is missing or incomplete.`, `[FATAL] Workflow schema version mismatch: expected <X>, found <Y>.`. Because the table is formatted like a code block, operators may reasonably believe these are exact, grep-able strings.

## Reason for Change
This is a confirmed factual error with direct operational impact — an operator grepping logs for the table's exact strings during an incident would get zero matches, delaying root-cause identification exactly when speed matters most.

## Implementation Intent
Either update the table to use the actual, verified log strings, or explicitly label the column as a summary (not a literal grep target) if summarization is intentionally preferred — the review recommends aligning to actual strings, or at minimum adding an explicit disclaimer.

## Target Files or Areas
`docs/02_deployment-part2.md` (§3.3, failure-mode table)

## Required Changes
- Replace each symptom-column entry with the corresponding actual log string, re-verified against current `deploy.sh`/`init_db.sh`/`setup_services.sh` source.
- If exact-string synchronization is judged too fragile to maintain long-term, instead add: "下表の「症状」列は要約ラベルであり、grep用の完全一致文字列ではない。実際のログ文字列は各スクリプト([deploy.sh](../deploy/deploy.sh) 等)を参照するか、正確な文字列を表に転記して同期する。" — choose one approach, not both.

## Acceptance Criteria
Either the table's symptom strings exactly match current script log output, or the table is explicitly labeled as a non-literal summary — not left in its current ambiguous, code-block-styled-but-inaccurate state.

## Testing Expectations
Not required (documentation-only). Manually re-verify each log string via `grep -n "FATAL" deploy/deploy.sh deploy/init_db.sh deploy/setup_services.sh` before finalizing.

## Documentation Impact
`docs/02_deployment-part2.md` failure-mode table corrected.

## Out of Scope
Do not change the actual log strings in `deploy.sh`/`init_db.sh`/`setup_services.sh` in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error — apply directly after re-verifying each log string against current source. Prefer exact-string synchronization if maintenance burden is acceptable; otherwise use the explicit non-literal-summary disclaimer, but do not leave the table in its current misleading code-block styling with mismatched content.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §4 強化候補 (§3.3 失敗モード表), §5 例4, §6 (失敗ログ文字列の不一致)
- Generated at: 2026-08-02
