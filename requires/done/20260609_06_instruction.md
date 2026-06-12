# 改修計画書

## 1. 目的

本計画書の目的は、MCP サーバ基盤、ツール実行ディスパッチ、入力検証、監査ログ、テスト用 echo server、および MCP サーバ雛形生成系モジュールについて、責務分離の徹底、入力契約の厳密化、環境依存要素の外出し、ならびに後方互換のために残存している実装の削除を実施することである。`server.py` は HTTP 実行と stdio 実行を同時に抱え、`dispatch.py` はエラーを文字列化して返却し、`models.py` は一部のみ自動検証・一部は手動検証であり、installer 系は OpenRC / init.d / 固定 repo layout を前提とした生成を行っている。

## 2. 全体改修方針

### 2.1 基本方針

1. MCP サーバ基盤は **transport 別責務へ分離** する。現行 `MCPServer` は HTTP 起動、stdio JSON-RPC 処理、tool list、トランケーション、認証 middleware 登録を併せ持つため、共通ポリシーと transport adapter に再編する。
2. ツール呼出し契約は **モデル検証→ディスパッチ→構造化結果返却** に一本化する。現状の `CallToolRequest.validate_args()` 手動呼出し、`dispatch_tool()` の `(str, bool)` 戻り値、validator 未登録時 no-op は整理対象である。
3. installer 系は **テンプレート生成**, **インストール計画**, **ファイル書込み**, **ポート選定** を分離し、OpenRC / init.d / `/opt/llm` 固定前提を削除する。現状は `installer_templates.py` と `installer_writer.py` が強く環境依存している。
4. 後方互換のためだけに残されている API や補助経路は削除する。対象は `server.py` の `run()` alias、`installer.py` の thin facade、`installer_port.py` の init.d fallback、テンプレート内の backward-compat 依存である。

### 2.2 適用原則

1. 例外は文字列へ潰さず、構造化された結果または専用例外として上位へ渡す。`dispatch.py` の `Tool error: {e}` 形式は改修対象とする。
2. 入力検証はモデル生成時に完了する構成とし、手動 `validate_args()` 呼出し前提を廃止する。
3. repo root や service manager、config source などの実行環境依存値は必須入力または構成オブジェクト経由とし、`__file__` ベースや固定パスベースの暗黙推定を削除する。
4. 監査ログ、ディスパッチログ、テスト観測情報は機械処理可能な形式に統一する。`audit.py` の単純 log line、`echo_server.py` の内部 `_stats` だけの状態、`dispatch.py` の平文ログは改善対象である。

## 3. 現状整理

### 3.1 `server.py` の現状

`server.py` は `MCPServer` 基底クラスとして、HTTP 起動用 `run_http()`、backward-compat alias の `run()`、stdio JSON-RPC ループ `run_stdio()`、レスポンス切詰め `_truncate()` / `_truncate_with_meta()`、認証 middleware 付与関数 `attach_auth_middleware()`、health/list_tools の既定実装を提供している。

### 3.2 `dispatch.py` / `models.py` / `tool_validators.py` の現状

`dispatch.py` は dispatch table と tool 名・args を受け取り、unknown tool、空 tool 名、handler 実行時例外をすべて `(result_text, is_error)` へ丸めて返している。`models.py` は `CallToolRequest` の `name` だけを field validator で検証し、tool-specific args 検証は `validate_args()` の手動呼出しに委ねている。`tool_validators.py` はグローバル registry に validator を登録し、登録がない tool では no-op となる。

### 3.3 installer 系の現状

`installer.py` は各 sub-module の public API を再 export する thin facade である。`installer_port.py` は config/agent.toml の ports を取りつつ、init.d の `--port` 引数も fallback で読む構成を持つ。`installer_writer.py` は template 選択と file I/O を 1 関数で実施し、`installer_templates.py` は OpenRC の init.d script、conf.d template、`/opt/llm` 固定 path、`rc-service` 前提コメントを生成する。

### 3.4 `audit.py` / `echo_server.py` の現状

`audit.py` は `server.py` から抽出された `_audit_log()` helper を持ち、session/request/action/target/outcome/detail を平文 structured-like に `info()` 出力する。`echo_server.py` は integration test 用の minimal JSON-RPC echo server を名乗る一方、`orjson` を利用し、`processed` / `malformed` / `empty_lines` の内部カウンタを持つが、観測手段は限定的である。

## 4. 課題

### 4.1 アーキテクチャ上の課題

1. `server.py` は transport, auth, truncation, dispatch 前後処理が混在し、基底クラスの凝集度が低い。
2. `dispatch.py` と `models.py` と `tool_validators.py` の責務境界が曖昧であり、モデル検証・ポリシー検証・例外整形の所在が分散している。
3. installer 系は import path 互換、repo layout 互換、service manager 互換を同時に抱え、モジュール構成が移行期のまま残っている。
4. `audit.py` は抽出 helper の段階に留まり、監査イベント API としては未整理である。

### 4.2 実装上の課題

1. `server.py` には `_truncate()` と `_truncate_with_meta()` の二重 API が存在し、切詰め仕様が重複している。
2. `dispatch.py` は HTTPException を duck typing で判定し、例外クラス体系の代わりに属性存在判定へ依存している。
3. `models.py` の `CallToolResponse` は `result` / `is_error` のみであり、`server.py` の stdio 応答が持つ `truncated` / `total_bytes` と整合していない。
4. `installer_port.py` の `scan_used_ports()` は reserved set を作った後で config / init.d の取得結果を上書きしており、docstring 記載の和集合動作になっていない。
5. `installer_templates.py` の生成物は OpenRC と固定パスに強く依存し、環境差分へ弱い。
6. `echo_server.py` の docstring は stdlib only とする一方、実装は `orjson` を import しており説明と不整合である。

### 4.3 後方互換性に起因する課題

1. `server.py` の `run()` は `run_http()` の alias に過ぎず、backward-compat 用コメント付きで残されている。
2. `installer.py` の facade は sub-module 再 export による import path 互換維持が主目的である。
3. `installer_port.py` の init.d fallback は agent.toml 以外の旧運用情報源を支える補助経路である。
4. `installer_templates.py` の `MCPServer.run()` 呼出しは `server.py` の backward-compat alias に依存している。

## 5. 改修内容

## 5.1 `server.py`

### 5.1.1 High

1. `MCPServer` を HTTP transport と stdio transport に分離し、共通基底は最小限の policy のみ保持する構成へ変更する。
2. `_truncate()` を廃止し、`_truncate_with_meta()` ベースの単一レスポンス切詰め API へ統一する。
3. `attach_auth_middleware()`、tool list、dispatch 呼出し補助など transport 非依存機能は専用コンポーネントへ切り出す。

### 5.1.2 Medium

1. stdio JSON-RPC の request/response を明示モデル化し、`orjson.loads()` 後の dict 直読みをやめる。
2. `run_stdio()` の例外パスを分類し、入力不正・handler 失敗・内部失敗を識別可能なエラー応答へ変更する。

### 5.1.3 Low

1. `ToolArgs` を共通型定義へ集約し、`dispatch.py` 側との重複定義を解消する。

### 5.1.4 削除対象

1. `run()` backward-compat alias。
2. `_truncate()` の旧 API。

## 5.2 `dispatch.py`

### 5.2.1 High

1. 戻り値 `(str, bool)` を `DispatchResult` などの構造化結果へ変更する。
2. HTTPException duck typing を廃止し、独自例外または正規化済みエラー型で分類する。
3. 空 tool 名や unknown tool の扱いを model validation と責務分担し、dispatch 層では handler 解決責務に集中させる。

### 5.2.2 Medium

1. request id や args 要約を含む構造化エラーログへ変更する。
2. sync handler / richer response handler も扱える dispatch 抽象へ見直す。

### 5.2.3 Low

1. `ToolArgs` 定義を共通型へ統一する。

### 5.2.4 削除対象

1. HTTPException duck typing による互換的例外判定。

## 5.3 `models.py`

### 5.3.1 High

1. `validate_args()` 手動実行を廃止し、tool-specific args 検証を Pydantic validator に統合する。
2. `args: dict[str, Any]` の自由度を縮小し、tool schema または typed envelope と連携させる。

### 5.3.2 Medium

1. `CallToolResponse` を `server.py` の truncation metadata と整合する共通応答モデルへ拡張する。
2. 利用先サーバ名を記載した docstring は汎用モジュールとして切り離す。

### 5.3.3 Low

1. tool 名検証を allowed tool catalog と接続し、blank check のみで終わらせない設計へ移行する。

### 5.3.4 削除対象

1. `validate_args()` 手動呼出し前提。

## 5.4 `tool_validators.py`

### 5.4.1 High

1. validator 未登録時 no-op を廃止し、少なくとも公開高リスク tool には validator または schema を必須化する。
2. グローバル `_VALIDATORS` registry を明示的 registry object へ置換する。

### 5.4.2 Medium

1. validator は role 設定や allowlist と連動した policy 検証まで担えるよう拡張する。
2. template 側の tool catalog と validator 登録名を単一データモデルから生成する。

### 5.4.3 Low

1. decorator の型戻り値を具体化し、型安全性を高める。

### 5.4.4 削除対象

1. validator 未登録時 no-op の互換挙動。

## 5.5 `audit.py`

### 5.5.1 High

1. `_audit_log()` を正式な監査 API と event schema に昇格させ、server/dispatch/role-specific server から一貫利用できるようにする。

### 5.5.2 Medium

1. `server_logger: Any` を protocol または明示 interface に変更する。
2. `detail` 文字列を構造化付帯情報へ変更する。

### 5.5.3 Low

1. private 名 `_audit_log` を公開 API 名へ変更する。

### 5.5.4 削除対象

1. server 抽出直後の暫定 private helper 形態。

## 5.6 `installer_validation.py`

### 5.6.1 High

1. `validate_server_name()` の `str | None` 返却を廃止し、例外または structured validation result へ変更する。
2. `name_to_module()` / `name_to_class()` を installer data model に統合し、テンプレートと writer で同一命名契約を強制する。

### 5.6.2 Medium

1. role 名、予約語、既存 package 名、既存 service 名なども検証対象へ広げる。
2. class 名変換規則を略語や区切り文字含めて明文化する。

### 5.6.3 Low

1. validation error に code を付与し、CLI 表示と API 利用を両立させる。

### 5.6.4 削除対象

1. `None` / エラー文字列返却の旧式契約。

## 5.7 `installer_port.py`

### 5.7.1 High

1. `scan_used_ports()` の reserved + config + init.d の集計を本来の和集合へ修正する。現状は上書きになっている。
2. `config/agent.toml` を唯一の正とし、init.d fallback を削除する。
3. `_REPO_ROOT` の `__file__` 依存を廃止し、`repo_root` を明示注入する。

### 5.7.2 Medium

1. config 解析・ファイル読込の包括例外握り潰しをやめる。
2. URL 正規表現による port 抽出を URL parser ベースへ変更する。

### 5.7.3 Low

1. `_RESERVED_PORTS` / `_PORT_START` を設定化する。

### 5.7.4 削除対象

1. init.d fallback。
2. `_REPO_ROOT` 暗黙推定。

## 5.8 `installer_writer.py`

### 5.8.1 High

1. template 選択・path 決定・存在確認・書込みを `install_mcp_server()` 1 関数に詰め込む構造を見直し、`InstallPlan` 作成と plan 適用に分離する。
2. repo root は必須入力または installer context から受け取り、`_REPO_ROOT` 依存を排除する。
3. OpenRC/init.d/conf.d 固定生成を writer 責務から外し、platform-specific provider を通じて供給する。

### 5.8.2 Medium

1. overwrite policy、dry-run、差分表示付き install transaction を導入する。
2. executable 判定を `path.parent.name == "init.d"` に依存しない方式へ変更する。

### 5.8.3 Low

1. 戻り値 `list[str]` を file metadata 付き DTO へ変更する。

### 5.8.4 削除対象

1. `_REPO_ROOT` 依存。
2. OpenRC/init.d 固定の writer 責務。

## 5.9 `installer_templates.py`

### 5.9.1 High

1. OpenRC / init.d / conf.d / `/opt/llm` / `rc-service` 固定を platform profile に分離し、テンプレート generator 自体を環境非依存化する。
2. `generate_server_script()` から `MCPServer.run()` 呼出しを除去し、`run_http()` へ統一する。
3. role ごとの role 値・tool 名・config keys を構造化データモデルで管理し、文字列断片生成に依存しない方式へ改める。

### 5.9.2 Medium

1. `generate_config_toml_for_role()` の if-elif 分岐を enum/provider 化する。
2. `tool_definition_snippet()` は JSON 文字列ではなく構造化 dict を返却する。
3. 「update to match actual tool name」といった手作業前提コメントを廃止し、生成時に整合した tool catalog を出力する。

### 5.9.3 Low

1. role-specific skeleton の記述精度を高め、sample code から実用 skeleton へ寄せる。

### 5.9.4 削除対象

1. OpenRC 固定 init.d template。
2. `rc-service` 前提 conf.d template。
3. `MCPServer.run()` 依存テンプレート。

## 5.10 `installer.py`

### 5.10.1 High

1. sub-module 再 export の thin facade を削除し、呼出し側は必要モジュールを直接 import する。

### 5.10.2 Medium

1. installer 公開 API を残す場合でも、関数再 export ではなく `InstallerService` などの明示オブジェクトへ再編する。

### 5.10.3 Low

1. `__all__` は再編後の最小公開面に合わせて縮小する。

### 5.10.4 削除対象

1. import path 互換目的の thin facade。

## 5.11 `echo_server.py`

### 5.11.1 High

1. integration test 用 server として deterministic な request/response 契約に整理し、正常系レスポンスと異常系挙動を明示する。

### 5.11.2 Medium

1. docstring と実装の不整合を解消する。`orjson` を使うなら stdlib only 表現を削除し、stdlib only を維持するなら `json` へ変更する。
2. `_stats` の観測手段を追加し、stderr summary などでテストから参照可能にする。

### 5.11.3 Low

1. malformed JSON stderr 出力フォーマットを固定し、テスト判定可能にする。

### 5.11.4 削除対象

1. 説明と矛盾する stdlib only 記述。

## 6. 実施優先順位

### 6.1 Phase 1: 最優先

1. `server.py` の backward-compat alias と二重 truncate API を削除し、transport 別責務分割へ移行する。
2. `installer_port.py` のポート集計不整合を修正し、init.d fallback を削除する。
3. `installer_templates.py` / `installer_writer.py` の OpenRC 固定前提と `run()` alias 依存を除去する。
4. `models.py` / `tool_validators.py` の検証方式を自動バリデーションへ統一する。
5. `installer.py` の thin facade を削除する。

### 6.2 Phase 2: 中優先

1. `dispatch.py` の結果型・例外型を再設計する。
2. `audit.py` を監査イベント API として再定義する。
3. `installer_validation.py` を structured validation 化する。
4. `echo_server.py` を deterministic test double として整理する。

## 7. 期待効果

1. transport, validation, dispatch, installer, audit の責務が明確になり、基盤改修の影響範囲が狭くなる。
2. 後方互換用の alias や fallback を削除することで、保守判断コストと実装の曖昧さが減少する。
3. 環境依存テンプレートを外出しすることで、OpenRC 以外の運用方式にも追随しやすくなる。
4. 入力検証と例外契約が統一され、ツール呼出し失敗時の原因追跡性が向上する。

## 8. リスクおよび留意事項

1. `server.py` の `run()` 削除と template 側修正は、既存 generated server や呼出しコードへ影響するため、テンプレート更新と呼出し側修正を同時に行う必要がある。
2. `installer.py` facade 削除は import 先の一括更新を伴う。
3. `installer_port.py` の fallback 削除後は agent.toml の整備が前提となる。
4. validator 必須化後は既存 tool 定義側に未登録 validator があると起動や呼出しが失敗するため、tool catalog との同時整備が必要である。

## 9. 実施条件

1. 既存の generated MCP server 群が `run()` / OpenRC template / init.d fallback に依存している箇所を事前棚卸しすること。
2. tool 名一覧と validator 対応表を作成し、未登録 tool を明示化すること。
3. installer 利用側 import 先を洗い出し、`installer.py` facade 削除に備えること。
4. 監査ログと dispatch ログの運用要件を確認し、event schema を先に固定すること。
