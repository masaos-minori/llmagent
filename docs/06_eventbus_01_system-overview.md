---
title: "Event Bus: System Overview"
category: eventbus
tags:
  - event-bus
  - system-overview
  - architecture
  - pub-sub
  - sse
  - security-model
  - authentication
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_05_02_bind-address-and-start.md
source:
  - index.md
---

# Event Bus: System Overview

## 目的

Event Bus は LLM エージェントシステム向けの内部 publish/subscribe 基盤を提供する。プロデューサーは JSON イベントを publish し、コンシューマーは SSE 経由でトピックを subscribe し、過去のイベントを replay する。

> **注記:** Event Bus HTTP API はスタンドアロンサービスとして完全に実装され、稼働している。
> Agent ランタイムとの統合（Agent からのイベント publish、SSE 経由での Agent トピックの subscribe）は
> 意図的に見送られており、まだ実装されていない。本ドキュメントは Event Bus を独立したコンポーネントとして
> 記述するものであり、Agent 側のイベント生成/消費については将来のリリースで文書化する予定である。

## アーキテクチャ

Event Bus はライブイベント配信のためにインメモリの pub/sub ブローカー（`EventBroker`）を使用する。各サブスクライバーは専用の `asyncio.Queue` を持ち、ブローカーはトピックフィルタに基づいてイベントを該当するサブスクライバーに fan-out する。

- **ライブ配信**: `EventBroker` は asyncio Queue を介したトピック単位の fan-out を提供する
- **リプレイ**: 過去のイベントは `/replay` と `/subscribe` エンドポイントを通じて SQLite から再生される
- **永続化**: すべてのイベントは SQLite に保存され、DLQ イベントは JSONL ファイルとして書き出される
- **オフセット管理**: コンシューマのリカバリ用にファイルベースでオフセットを永続化する

### EventBroker

`EventBroker` は `_Subscriber` データクラスのリストを保持し、各要素は asyncio Queue と任意のトピックフィルタを持つ。`publish()` は該当するサブスクライバーにイベントを fan-out し、キューが満杯の場合は破棄する（WARNING ログを出力）。`shutdown()` はすべてのサブスクライバーキューのブロックを解除するために None センチネルを送信する。

Queue の maxsize は 1000、低速コンシューマの閾値は 100 件。

## セキュリティモデル

Event Bus API には **認証も ACL も存在しない**。

- **設計上の前提**: 内部ネットワーク/信頼済みホスト上でのシングルノード運用を想定
- **アクセス制御**: ネットワーク境界（ファイアウォール、Docker ネットワーク）で実施
- **公開しないこと**: Event Bus はインターネットから直接到達可能にしてはならない
- **起動時のガード**: TOML 設定で `allow_public_bind=true` を設定しない限り、公開/ワイルドカードアドレス（0.0.0.0、::）へのバインドは設定検証で拒否される。認証なしで公開アドレスにバインドされた場合は WARNING ログが出力される。

### 将来の認証オプション

要件が生じた場合の選択肢:
- FastAPI の `Depends` による API キー認証
- サービス間認証のための mTLS

現時点では未実装。追加する前に実際の脅威モデルに基づいて評価すること。

## 今後の統合

以下の Agent 側統合は現時点で意図的に未実装である。

- **Agent によるイベント publish**: Agent 側のイベントプロデューサーは実装されていない。Event Bus HTTP API は任意の HTTP クライアントからの publish をサポートしており、Agent 固有のプロデューサーは将来のリリースで追加される予定。
- **Agent の SSE subscribe**: `/subscribe` の SSE を介してイベントを消費する Agent 側サブスクライバーは存在しない。Agent 側のコンシューマーは将来のリリースで追加される予定。
- **Agent のイベントトピック**: 現時点で Agent が定義したトピックは存在しない。Agent のライフサイクルイベントに関するトピック命名規則は、Agent 統合の実装時に定義される。

これらの項目は `docs/06_eventbus_90_inconsistencies_and_known_issues.md` にも保留事項（Deferred Items）として文書化されている。

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_05_02_bind-address-and-start.md`

## Keywords

event-bus
system-overview
architecture
pub-sub
sse
security-model
authentication
