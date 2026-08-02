# Add sqlite-vec path cross-reference note and flag deploy/build_sqlite_vec.sh's incorrect "common.toml" comment

## Priority
Medium

## Summary
`docs/02_deployment-part1.md` §2.1 correctly documents that the `vec0.so` placement path must match `config/agent.toml`'s `sqlite_vec_so` key (confirmed accurate against source). However, `deploy/build_sqlite_vec.sh`'s comment (~line 41) references a file named `common.toml` for this same key, but `config/common.toml` does not exist — the actual file is `agent.toml`, matching the documentation's own (correct) description.

## Reason for Change
This is a confirmed inconsistency between the documentation (correct) and a script comment (incorrect) — leaving it unaddressed risks a future reader trusting the script comment instead and searching for a nonexistent `common.toml`, wasting time without material harm but degrading maintainability.

## Implementation Intent
Add a note to the documentation clarifying that the documentation's description is correct and the script comment is outdated, and fix the script comment directly (a low-risk, one-line change) rather than only flagging it.

## Target Files or Areas
`docs/02_deployment-part1.md` (§2.1), `deploy/build_sqlite_vec.sh` (~line 41 comment)

## Required Changes
- Add to `part1`'s §2.1: "vec0.so の配置パスは `config/agent.toml` の `sqlite_vec_so` と一致させること(agent.tomlが正)。なお `deploy/build_sqlite_vec.sh` のコメントは古い記述(`common.toml`)を参照しており誤りである(別途修正済み/要修正)。"
- Fix `deploy/build_sqlite_vec.sh`'s comment from `common.toml` to `agent.toml`, matching the actual, current, correct file.

## Acceptance Criteria
`part1` explicitly cross-references the documentation-vs-script-comment discrepancy; `deploy/build_sqlite_vec.sh`'s comment correctly references `agent.toml`.

## Testing Expectations
Not required — this is a comment-only change in a shell script with no behavioral effect. Confirm via `grep -n "common.toml\|agent.toml" deploy/build_sqlite_vec.sh` before and after the change.

## Documentation Impact
`docs/02_deployment-part1.md` gains a clarifying cross-reference note.

## Out of Scope
Do not make any functional changes to `deploy/build_sqlite_vec.sh` beyond the comment text.

## AI Implementation Instruction
The script-comment fix is a trivial, comment-only, zero-behavior-change edit — safe to apply directly alongside the documentation note, rather than only flagging it as a separate follow-up.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §4 強化候補 (§2.1 sqlite-vec配置パス), §6 (build_sqlite_vec.shコメントの参照ファイル誤り)
- Generated at: 2026-08-02
