# MCP / Installer 改修計画書

## 全体方針

- 後方互換性は維持しない。旧挙動の温存、曖昧な入力受け入れ、暗黙補正、fail-soft な救済分岐は削除する。
- すべてのレイヤで **fail-fast** を徹底する。入力不正、設定不備、テンプレート生成失敗、I/O 失敗、検証失敗、ツール実行失敗は即座に検知し、呼び出し元へ明示的に返す。
- 変換・型付けは厳密に行う。文字列・辞書・HTTP リクエスト・テンプレート変数・監査ログ入力を曖昧に扱わない。
- `except Exception` は原則使用しない。想定する失敗型を個別に捕捉し、それ以外はそのまま送出する。
- 役割を明確に分離する。
  - `installer_*`: インストーラ専用（検証 / テンプレート生成 / ファイル書き込み / ポート計算）
  - `models.py`: API 契約専用
  - `dispatch.py`: ツールディスパッチ専用
  - `tool_validators.py`: ツール引数検証専用
  - `audit.py`: 監査イベント出力専用
  - `server.py`: MCP サーバ基盤専用
  - `echo_server.py`: サンプル / 疎通確認用
- テンプレート生成と実ファイル生成は分離しつつ、テンプレートの妥当性を事前に検証できる構造にする。
- 生成物の品質を一定化する。テンプレートから出力されるコード・設定・init スクリプト・conf.d テンプレート・agent.toml 断片は、常に構文・命名・責務が整合した状態で出力されるようにする。

## 実装ルール

- 検証関数は **例外を返さない**。`str | None` のような曖昧な戻り値ではなく、成功時は正規化済み値を返し、失敗時は専用例外を送出する。
- `Any` は最小限に抑える。ツール引数、ディスパッチテーブル、HTTP アプリ、監査イベントに具体型または Protocol を導入する。
- 文字列テンプレートは単純連結・埋め込みに頼りすぎず、構造ごとに責務を分ける。
- ファイル書き込みは原子的に扱う。既存ファイル検出、親ディレクトリ作成、書き込み、権限変更を段階的に行い、中途半端な状態を残さない。
- テンプレート生成関数は「有効な入力のみ受け取る」ことを前提にしない。引数は内部でも再検証する。
- 監査ログは失敗しても業務ロジックを曖昧に継続しない。監査が必須の操作なら失敗扱いにする。
- Truncation・認証・stdio/HTTP 実行は明確に経路を分け、副作用を局所化する。
- 生成される Python / TOML / init スクリプトはテスト可能な単位で出力し、生成後検証（構文チェック / 最低限の静的検証）を通す。

## ファイルごとの修正内容

### 1. `installer_templates.py`

#### High
- テンプレート生成責務を細分化する。現在は `generate_server_script()` にサーバ実装、ツール定義、ディスパッチ、HTTP エンドポイント、起動コードまで含まれており責務が大きすぎるため、**サーバ骨格 / ツール定義 / HTTP エンドポイント / 起動部 / 設定断片** を個別テンプレートへ分離する。
- 生成コード内の型を厳密化する。`dict[str, Any]` や `list[dict]` のまま出力せず、生成先でも具体的モデルや typed structure を利用するテンプレートへ変更する。
- role ごとの `generate_config_toml_for_role()` を if/elif 分岐で増やさない。role ごとの設定モデルとテンプレートマッピングを導入し、不正 role は即例外とする。
- テンプレート引数 (`server_name`, `module`, `port`, `role`) の検証をテンプレート層でも行い、不正値で構文破壊した文字列を生成しない。
- 生成スクリプト内に説明コメントとして埋め込まれている TODO 的記述や「置き換えて使う」前提の曖昧さを減らし、最初から最小構成で実行可能な生成物を出力する。

#### Medium
- `generate_agent_toml_mcp_snippet()`、`tool_definition_snippet()`、`generate_initd_script()`、`generate_confd_template()` の共通部を整理し、命名規約・コメント様式・改行規則を統一する。
- `textwrap.dedent()` ベースの巨大文字列を構造化し、差分把握しやすい部品構成へ変更する。
- shell / sqlite など role 固有テンプレートは role ごとモジュール分割を検討する。

#### Low
- テンプレート関数名と docstring を統一し、戻り値が何の断片かを明確にする。
- 生成物内コメントの重複を削減する。

---

### 2. `installer_validation.py`

#### High
- `validate_server_name()` の `str | None` 戻り値を廃止し、専用例外送出へ変更する。
- `name_to_module()` / `name_to_class()` は「事前に validate 済み」を暗黙前提にせず、自身でも入力検証を行う。
- サーバ名から派生する module 名・class 名が Python 識別子として安全かどうかを厳密に検証する。

#### Medium
- server 名の validation と、module/class 変換を分離した正規化パイプラインにする。
- 予約語・既存モジュール衝突・既存クラス名衝突を検出対象に加える。

#### Low
- エラーメッセージの一貫性を改善する。

---

### 3. `installer_writer.py`

#### High
- `install_mcp_server()` を単一巨大関数のままにせず、**入力検証 / 出力対象決定 / 既存競合検出 / 原子的書き込み / 権限設定** に分割する。
- `validate_server_name()` の結果文字列を `ValueError` に変換する流れを廃止し、検証レイヤの例外をそのまま扱う構造にする。
- 既存ファイル検出後の書き込みは原子的に行う。現状は順次 `write_text()` しているため、中途失敗時に部分生成が残る。テンポラリ書き込み + rename またはロールバック戦略を導入する。
- `chmod(0o755)` をディレクトリ名依存ではなく、出力ファイル種別で判定する。
- `repo_root` 解決を厳密化し、意図しないパス書き込みを防ぐ。

#### Medium
- 戻り値 `list[str]` ではなく、生成ファイル・権限設定結果・衝突情報を持つ structured result に変更する。
- ファイル生成前にテンプレート構文妥当性を確認できるようにする。
- dry-run モードを追加し、書き込み前に差分確認可能にする。

#### Low
- パス構築ロジックをより宣言的に整理する。

---

### 4. `models.py`

#### High
- `CallToolRequest.args` の型を `dict[str, Any]` のままにせず、少なくとも tool 名ごとの validator と整合した strict object に寄せる。
- `validate_args()` を明示呼び出し前提にせず、モデル生成時または dispatch 前に必ず実行されるよう API 契約を変更する。
- blank name 以外にも、長さ・許可文字・内部予約名をモデル層で検証する。

#### Medium
- `CallToolResponse.result: str` 固定を見直し、将来の structured response に備えた result model を導入する。
- request/response に request id や tool metadata を持たせることを検討する。

#### Low
- docstring を実際の利用箇所に合わせて更新する。

---

### 5. `server.py`

#### High
- `MCPServer` 基底クラスの責務を整理し、HTTP 実行・stdio 実行・認証・truncation・監査を分離する。
- `run_stdio()` 内の `except Exception` を廃止し、JSON decode error、validation error、dispatch error、I/O error を個別に扱う。
- `ToolArgs = dict[str, Any]` を廃止し、少なくとも Protocol または request model に寄せる。
- `_truncate_with_meta()` の UTF-8 切り捨て戦略は bytes 制限と表示責務が混在しているため、truncation policy と formatter に分離する。
- `attach_auth_middleware()` は token 文字列だけで分岐せず、認証ポリシーオブジェクトを受け取るようにする。
- 監査ログ呼び出しと dispatch 実行の境界を明確化し、監査必須時の失敗扱いを定義する。

#### Medium
- `run_http()` の `uvicorn.run()` 直接呼び出しをラップし、設定注入・テスト・差し替え可能な構造にする。
- `list_tools()` / `health()` は単なる dict/list 返却ではなく、明示的モデルに変更する。
- stdio JSON-RPC の入出力形式を専用モデル化する。

#### Low
- 基底クラス属性の docstring と命名を統一する。

---

### 6. `tool_validators.py`

#### High
- validator 登録と実行の API を厳密化する。現在の「存在すれば呼ぶ」構造を見直し、未登録時の既定挙動を明文化する。
- `dict[str, Any]` のまま検証せず、validator ごとに strict model を持たせる。
- git / workflow / shell 実行など危険な操作の validator は文字列存在チェックレベルで終わらせず、許可値・必須引数・禁止パターンを明示的に定義する。
- validator が `ValueError` を投げるだけの構造をやめ、失敗コードを持つ例外または result に変更する。

#### Medium
- validator registry を宣言的な定義へ変更し、追加時に手続きコードを書かなくてよい形にする。
- server / dispatcher から validator の責務を見えやすくするため、validation spec を分離する。

#### Low
- validator 名と tool 名の対応規則を明文化する。

---

### 7. `audit.py`

#### High
- 監査イベントを単なる logger 呼び出しに留めず、監査イベントモデルを定義する。
- 監査ログ失敗時の扱いを曖昧にしない。重要操作では監査失敗を無視しない。
- `Any` を廃止し、監査 payload の入力型を固定する。

#### Medium
- 監査イベントに request id、tool name、is_error、actor/source を含める統一フォーマットへ変更する。
- logger 以外の監査バックエンドへ切り替え可能なポートを導入する。

#### Low
- 補助関数名をイベント出力の意図に合わせて見直す。

---

### 8. `dispatch.py`

#### High
- `_handle_tool_exception()` と `dispatch_tool()` の例外戦略を全面見直しする。`dispatch_tool()` の末尾 `except Exception` を廃止し、未知例外を安易に result 文字列へ変換しない。
- dispatch table の型を厳密化し、tool handler のシグネチャを Protocol で固定する。
- request validation → handler 呼び出し → 例外正規化 → 監査 の順序を明示し、責務を分ける。
- unknown tool / validation failure / handler failure / internal failure を別エラーとして扱う。

#### Medium
- dispatch 結果を `tuple[str, bool]` ではなく result model に変更する。
- logger 出力内容を一貫化し、監査ログと重複しないよう整理する。

#### Low
- 補助関数の命名と docstring を更新する。

---

### 9. `echo_server.py`

#### High
- サンプル用途であっても API 契約は基底クラスと一致させる。サンプルだから曖昧型でよい、という扱いをしない。
- echo server を疎通確認専用に明確化し、本番向けサーバ例として誤用できないよう責務を限定する。

#### Medium
- テスト用サーバとしての最低限の validator / response model / health 表現を整える。
- サンプルコードをテンプレート生成系と共通化できる箇所は揃える。

#### Low
- ドキュメントとサンプル文言を簡潔化する。

---

### 10. `installer_port.py`

#### High
- `_ports_from_config()` の `except Exception` を廃止し、ファイル不存在・読み込み失敗・パース失敗を個別に扱う。
- ポート候補探索を fail-soft にせず、設定不備や衝突状態を明示的に返す。
- `_REPO_ROOT` からの設定探索を暗黙にせず、解決根を呼び出し側から渡せるようにする。

#### Medium
- `scan_used_ports()` / `suggest_port()` の責務を分け、設定読み取り済みポート集合と提案戦略を独立させる。
- ポート範囲、予約領域、既存標準サーバとの衝突回避ルールを設定可能にする。

#### Low
- 補助関数名をより意図に沿ったものへ調整する。

## 作業ステップ

1. **型と契約の固定**
   - `models.py`, `tool_validators.py`, `dispatch.py`, `audit.py` の境界型・例外型・result 型を先に定義する。
   - `Any` と曖昧な `tuple[str, bool]` / `list[str]` / `str | None` を structured model へ置き換える。

2. **失敗戦略の統一（fail-fast 化）**
   - `installer_validation.py`, `installer_port.py`, `dispatch.py`, `server.py` から `except Exception` を除去する。
   - validation error / I/O error / generation error / dispatch error を明示クラスへ分離する。

3. **インストーラ責務の分解**
   - `installer_templates.py` をテンプレート部品へ分割する。
   - `installer_writer.py` を 検証 / 出力計画 / 競合確認 / 原子的書き込み / 権限付与 に分割する。
   - dry-run と生成後検証を導入する。

4. **サーバ基盤の整理**
   - `server.py` の HTTP / stdio / 認証 / truncation / 監査を分離する。
   - request/response/dispatch/audit の流れを型付きで再構成する。

5. **ポート・サンプル・補助部の整備**
   - `installer_port.py` の提案戦略を整理する。
   - `echo_server.py` を疎通確認専用サンプルとして最小構成にする。

6. **テスト追加**
   - validation 異常系
   - 既存ファイル衝突
   - 部分書き込み失敗
   - stdio 不正 JSON
   - unknown tool
   - validator failure
   - auth failure
   - truncation 境界
   - port 衝突

## 完了条件

- `except Exception` が原則として除去され、例外が分類済みになっている。
- validation 戻り値が `None` / 文字列エラーではなく、成功値または明示的例外になっている。
- インストーラは原子的にファイル生成でき、中途失敗で部分生成物を残さない。
- 生成テンプレートは role ごとに構造化され、生成後に静的妥当性を確認できる。
- dispatch / validator / audit / server の境界が明確になり、型が厳密化されている。
- HTTP / stdio / auth / truncation / audit の責務が `server.py` から分離または整理されている。
- ポート提案が設定・衝突・予約規則を考慮し、曖昧な fallback を行わない。
- サンプルサーバは本番実装の最低契約に準拠しつつ、責務が明確に限定されている。
