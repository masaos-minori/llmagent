# 概要・アーキテクチャ・ファイル構成 (インデックス)

| ファイル | 内容 |
|---|---|
| [01_overview-arch.md](01_overview-arch.md) | 概要・目的・アーキテクチャ (プロセス構成・取込パイプライン・クエリパイプライン・ターン処理順序・MCP サーバ一覧・実装済み機能・実装補足) |
| [01_overview-files.md](01_overview-files.md) | ファイル構成 (デプロイ先 `/opt/llm/` ディレクトリ構造・ソースモジュール一覧) |

## 実装意図

- `01_overview-arch.md` と `01_overview-files.md` を分割している理由: arch は設計・動作・ライフサイクルを記述し、files は `/opt/llm/` 以下の物理配置とソースモジュールの対応を記述する。関心の異なる2種の参照ニーズに対応するための意図的な分離。(根拠: 各ファイルのトップに相互リンクが張られており、分離を前提とした設計になっている)
- `01_overview-arch.md` には単純なアーキテクチャ図に加えて、ターン処理順序・`workflow_mode` の3種・`startup_mode`・プラグインシステム・`AgentContext` の DI ハブ役割・メモリフォールバック等の実装補足セクションが含まれている。これらは `orchestrator.py`・`startup.py`・`factory.py`・`context.py` 等のソースコードから直接裏付けられる。
- 本ファイルはシステム全体の概要インデックス。詳細なドキュメントセットの目次は `00_llm-implementation-guide.md` を参照。
