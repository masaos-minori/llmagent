# Implementation Procedure: Add SQLite/JSONL Reconciliation Procedure to Persistence Schema Doc

## Goal
Add a SQLite/JSONL reconciliation procedure section to `docs/06_eventbus_03_persistence_schema_and_replay.md` with detection method, existing signal reference, and recommended additions (counter metric, operator runbook step).

## Scope
- Target file: `docs/06_eventbus_03_persistence_schema_and_replay.md`
- Add reconciliation procedure section covering:
  - Detection: compare `SELECT MAX(seq) FROM events` in SQLite against last line of `events.jsonl`
  - Existing signal: `publish_route.py`'s WARNING log for JSONL append failure
  - Recommended additions: counter metric on WARNING path, operator runbook step to re-derive missing JSONL lines from SQLite

## Assumptions
- SQLite is authoritative per `docs/06_eventbus_02_05_failure-behavior-summary.md`
- JSONL is supplementary; JSONL append failure does not fail the HTTP request (returns 200)
- The existing WARNING log in `publish_route.py` line 59 is the only signal today

## Design decisions
- Place the reconciliation section after the existing "Replayの挙動" section
- Provide concrete detection command using `sqlite3` and shell tools
- Reference the existing WARNING log as the only current signal
- Document recommendations as documentation-only (not implemented here)

## Alternatives considered
- Create a separate reconciliation doc: Rejected — fits naturally in persistence schema doc
- Implement the metric/alert in code: Rejected — out of scope per Global Rule 8

## Implementation
### Target file
`docs/06_eventbus_03_persistence_schema_and_replay.md`

### Procedure
1. Read the current file content
2. Add reconciliation procedure section after the existing "Replayの挙動" section (around line 51)
3. Include detection method, existing signal, and recommended additions

### Method
Direct Markdown editing with exact section placement

### Details
**Reconciliation Procedure Section (to add after "Replayの挙動" section):**

## SQLite/JSONL 整合性チェックとリカバリ手順

### 検出方法
SQLiteの最大 `seq` と JSONLアーカイブの最終行の `seq` を比較し、差異があれば JSONL への追記失敗が発生していたことを示します。

```bash
# SQLite の最大 seq 取得
sqlite3 /path/to/eventbus.db "SELECT MAX(seq) FROM events;"

# JSONL の最終行 seq 取得
tail -1 /path/to/events.jsonl | jq '.seq'
```

両者が一致しない場合、JSONL に欠損があります。

### 既存の検知シグナル
`publish_route.py` (line 59) にて、JSONL 追記失敗時に以下の WARNING ログが出力されます：
```
logger.warning("eventbus: JSONL append failed (event still committed): %s", exc)
```
これは SQLite コミット成功後の JSONL 追記失敗時にのみ出力され、HTTP レスポンスは 200 を返します。この WARNING パスにはメトリクスやアラートが付いていません。

### 推奨される追加対応（本フェーズではドキュメントのみ）

1. **カウンターメトリクス**: 上記 WARNING パスにカウンターメトリクスを追加し、JSONL 追記失敗の発生回数を可視化
2. **オペレータランブック**: SQLite が正（正しいデータを持つ）前提で、欠損した JSONL 行を SQLite から再導出してバックフィルする手順をランブックに記載
   - SQLite は正（`docs/06_eventbus_02_05_failure-behavior-summary.md` より）
   - 欠損 `seq` 範囲を特定し、SQLite から該当行を SELECT して JSONL 形式で追記

## Compatibility considerations
- Documentation-only change, no code impact
- Recommendations are flagged as documentation-only for this phase

## Security considerations
- None — documentation only

## Rollback considerations
- Git revert of this file if issues arise

## Validation plan
- Manual review: detection command and backfill logic both stated concretely
- `git diff` to verify section added correctly
- No `scripts/` files changed (`git diff --stat -- scripts/` empty)

## Out of scope
- Implementation of counter metric or alert (separate requirement)
- OpenAPI spec creation
- Changes to other `06_eventbus_*.md` files not listed in the plan

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-220838_require.md
- Source plan: plans/20260819-173619_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-133437
- Related target files: docs/06_eventbus_03_persistence_schema_and_replay.md