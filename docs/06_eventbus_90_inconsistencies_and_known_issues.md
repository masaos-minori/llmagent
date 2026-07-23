---
title: "Event Bus: Known Inconsistencies and Issues"
category: eventbus
tags:
  - event-bus
  - known-issues
  - inconsistencies
  - spec-conflicts
  - deferred-items
  - ack-offset
  - monotonicity
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_04_dlq-background-loop.md
  - 06_eventbus_04_dlq_offsets_and_delivery_semantics.md
source:
  - index.md
---

## 移行ノート

- 移行日: 2026-07-23
- 移行元フォーマット: 既存のバレット形式（Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference）
- 移行先フォーマット: 共通テンプレート（17フィールド）
- 注: 既存のエントリ内容は維持。不足フィールドは「未確認」で埋める。

# Event Bus: Known Inconsistencies and Issues

## 対応が必要な項目

これらの項目は、実装変更を要する未解決の問題、またはユーザーに実際の影響を与えている問題を示す。

### EVENTBUS-001: Ack オフセットの単調性が保証されていない

- **ID**: EVENTBUS-001
- **Title**: Ack オフセットの単調性が保証されていない
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: offsets.py の write_offset()
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: offsets.py
- **Related**: 未確認
- **Summary**: write_offset() が max(current, new) チェックを持たず、オフセットの単調な前進を保証しない
- **Current Description**: 古いイベント seq を ack すると、コンシューマのオフセットが後退する可能性がある
- **Observed Implementation**: write_offset() に max(current, new) のチェックがない
- **Impact**: 再接続時にコンシューマが重複イベントを受信することがある
- **Recommended Action**: コンシューマ側でオフセットの後退が起こり得ることを考慮した実装が必要
- **Resolution Notes**: サーバー側での修正は予定していない

---

## ドキュメントのみで対応する項目

これらの項目は、実装変更を伴わないドキュメント上の改善事項である。

### EVENTBUS-002: /replay?format=json はページネーションされたオブジェクトを返す

- **ID**: EVENTBUS-002
- **Title**: /replay?format=json はページネーションされたオブジェクトを返す
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: missing-documentation
- **Source**: GET /replay endpoint
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: ドキュメント
- **Related**: 未確認
- **Summary**: /replay?format=json のレスポンス形式のドキュメント化が必要
- **Current Description**: GET /replay?format=json が生の配列ではなく {total, limit, offset, items} を返す
- **Observed Implementation**: クライアントは limit/offset パラメータを使って replay 結果をページネーションできる
- **Impact**: クライアント実装者がページネーション形式を誤解する可能性
- **Recommended Action**: ドキュメントにレスポンス形式を明記
- **Resolution Notes**: ドキュメントのみの対応

---

### EVENTBUS-003: DLQ への promotion は nack 時のインライン処理と安全網としての sweep の組み合わせである

- **ID**: EVENTBUS-003
- **Title**: DLQ への promotion は nack 時のインライン処理と安全網としての sweep の組み合わせである
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: dlq.py, app.py, ack_route.py
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: ドキュメント
- **Related**: 未確認
- **Summary**: DLQ promotion の2つの経路（インラインとバックグラウンド）のドキュメント化が必要
- **Current Description**: 主たる DLQ への promotion は /nack でインラインに実行され、バックグラウンドループは安全網としての sweep
- **Observed Implementation**: バックグラウンドの DLQ ループはしきい値に達したがインラインで promotion されなかったイベントを捕捉
- **Impact**: DLQ promotion の動作を理解できない
- **Recommended Action**: ドキュメントに DLQ promotion の2つの経路を明記
- **Resolution Notes**: ドキュメントのみの対応

---

### EVENTBUS-004: dlq.py::promote_to_dlq() は本番経路から呼ばれていない

- **ID**: EVENTBUS-004
- **Title**: dlq.py::promote_to_dlq() は本番経路から呼ばれていない
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: obsolete-description
- **Source**: dlq.py vs app.py, ack_route.py, tests/test_eventbus_dlq_promotion.py
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: ドキュメント
- **Related**: 未確認
- **Summary**: promote_to_dlq() がテストコードからのみ直接呼び出されており、本番コードパスからは呼ばれていない
- **Current Description**: dlq.py は promote_to_dlq(), sweep_orphans(), promote_single() の3関数を公開しているが、app.py は sweep_orphans のみを、ack_route.py は promote_single のみを import
- **Observed Implementation**: promote_to_dlq は本番コードパスのいずれからも呼ばれておらず、テストユーティリティとしてのみ使用
- **Impact**: ドキュメントが実際の使用経路と一致しない
- **Recommended Action**: ドキュメント上は sweep_orphans と promote_single の2経路のみを正規の DLQ promotion 経路として扱う
- **Resolution Notes**: ドキュメントのみの対応

---

## 保留中の項目

Event Bus と Agent ランタイムとの統合は、現時点では意図的に実装されていない。

### EVENTBUS-005: Agent によるイベント publish

- **ID**: EVENTBUS-005
- **Title**: Agent によるイベント publish
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: operational-gap
- **Source**: Event Bus HTTP API
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: Agent ランタイム
- **Related**: 未確認
- **Summary**: Agent 側のイベントプロデューサーは実装されていない
- **Current Description**: Event Bus の HTTP API はどの HTTP クライアントからの publish もサポートしている
- **Observed Implementation**: Agent 専用のプロデューサーは今後のリリースで追加予定
- **Impact**: Agent から Event Bus へ直接 publish できない
- **Recommended Action**: 今後のリリースで Agent 専用プロデューサーを追加
- **Resolution Notes**: 保留中

---

### EVENTBUS-006: Agent による SSE subscription

- **ID**: EVENTBUS-006
- **Title**: Agent による SSE subscription
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: operational-gap
- **Source**: /subscribe endpoint
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: Agent ランタイム
- **Related**: 未確認
- **Summary**: /subscribe の SSE 経由でイベントを消費する Agent 側のサブスクライバーは存在しない
- **Current Description**: Agent 側のコンシューマーは今後のリリースで追加予定
- **Observed Implementation**: Agent 側のコンシューマーは今後のリリースで追加予定
- **Impact**: Agent から SSE イベントを購読できない
- **Recommended Action**: 今後のリリースで Agent 側のコンシューマーを追加
- **Resolution Notes**: 保留中

---

### EVENTBUS-007: Agent 用のイベントトピック

- **ID**: EVENTBUS-007
- **Title**: Agent 用のイベントトピック
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: Event Bus トピック定義
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: Agent ランタイム
- **Related**: 未確認
- **Summary**: 現時点で Agent が定義するトピックは存在しない
- **Current Description**: Agent のライフサイクルイベント用のトピック規約は、Agent 統合が実装される際に定義される
- **Observed Implementation**: Agent のライフサイクルイベント用のトピック規約は、Agent 統合が実装される際に定義される
- **Impact**: Agent のライフサイクルイベントをトピックで識別できない
- **Recommended Action**: Agent 統合が実装される際にトピック規約を定義
- **Resolution Notes**: 保留中

---

## スキーマと実装の差異

| フィールド | スキーマ定義 | 実行時の挙動 | 状態 |
|---|---|---|---|
| `acked_at` | TEXT | ack 時に設定される(冪等 — 既存の値を上書きしない) | 使用中 — `db.py::ack_event()` を参照 |
| `delivery_failure_count` | INTEGER NOT NULL DEFAULT 0 | nack 時にインクリメントされる。`>= max_retry` で DLQ への promotion が発生する | 使用中 — `db.py::nack_event()` を参照 |
| `dlq_requeue_count` | INTEGER NOT NULL DEFAULT 0 | DLQ requeue 時にインクリメントされる。`delivery_failure_count` はリセットされない | 使用中 — `db.py::requeue_event()` を参照 |
| `dlq_at` | TEXT | イベントが DLQ に promotion された時に設定される(インラインまたはバックグラウンド sweep) | 使用中 — DLQ promotion 時に設定される |

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Keywords

event-bus
known-issues
inconsistencies
spec-conflicts
deferred-items
ack-offset
monotonicity
