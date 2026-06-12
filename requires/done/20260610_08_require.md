# File MCP（Read / Write / Delete）改修計画書

## 全体方針

- 本改修では 後方互換性を維持しない。旧挙動の温存、config 読み込み失敗時の `{}` fallback、warning のみで継続する救済、暗黙の fail-open、 loosely typed な引数受け入れは削除する。
- すべてのレイヤで fail-fast を徹底する。設定不備、パス検証失敗、サイズ上限違反、不正なリクエスト、I/O 失敗、ディレクトリ走査失敗、エンコード失敗、audit/dispatch 不整合は即座に検知し、明示的な例外または結果型として扱う。
- 変換・型付けは厳密に行う。`Any`、raw dict、暗黙の config 辞書、動的 dispatch、 loosely typed tool schema を減らし、型付き設定・型付き request/response・service 결과型へ置き換える。
- `except Exception` は原則使用しない。想定される失敗型のみを個別に捕捉し、それ以外はそのまま送出する。
- `common.py` / `*_models.py` / `*_service.py` / `*_server.py` / `read_tools.py` の責務を明確化する。
  - `common.py`: パス/存在/サイズ/権限に関する共通ポリシー
  - `*_models.py`: request/response model と設定モデル09
  - `*_service.py`: 業務ロジック（read/write/delete）
  - `*_server.py`: FastAPI / MCP transport 層
  - `read_tools.py`: 読み取りツール schema 定義
- HTTP transport（FastAPI / `HTTPException`）と domain service を分離し、service 層は transport 非依存にする。

## 実装ルール

- `_get_cfg()` の module-level cache と `except Exception` + `{}` fallback を禁止する。設定は起動時に一度ロードし、型付き設定オブジェクトを注入する。
- `HTTPException` は server / transport 層のみで使用し、`common.py` と `*_service.py` からは除去する。service/common では domain/service 例外を使用する。
- `Path` 解決、許可ディレクトリ検証、サイズ検証、存在確認、ファイル/ディレクトリ種別確認は共通ポリシーとして統一し、read/write/delete で重複実装しない。
- `print()` は業務ロジックに持ち込まない。表示責務は server ないし formatter に限定する。
- `read_tools.py` のような手書き schema は、request model から生成するか、単一ソースへ統一する。
- media/base64、grep、directory tree、text edit、move、delete recursive などの操作は、入力検証と実行ロジックを明確に分離する。
- dry-run は write/delete 系の正式な実行モードとして扱い、戻り値・監査・差分表示契約を統一する。
- ファイル I/O は原子的に扱う。特に書き込み・移動・削除は中途半端な状態を残さないよう設計する。

## ファイルごとの修正内容

### 1. `common.py`

#### High
- `resolve_safe()`, `require_file()`, `require_dir()`, `check_size_limit()` が `HTTPException` を直接投げる構造を廃止し、transport 非依存の domain 例外へ変更する。
- パス解決と allowed_dirs 検証を fail-fast に統一し、read/write/delete で例外種別がぶれないようにする。
- `resolve_safe()` の正規化・symlink・親ディレクトリ判定を厳密化し、単純な `Path.resolve()` 依存の抜け道をなくす。

#### Medium
- `require_file()` / `require_dir()` / `check_size_limit()` を policy object または validator 群に分離し、読み書き削除サービスから共通利用する。
- permissions 表示やサイズエラー文面を formatter と例外クラスで分離する。

#### Low
- `format_permissions()` の責務を純粋表示ユーティリティとして明確化する。

---

### 2. `read_models.py`

#### High
- `_get_cfg()` の `except Exception` + `{}` fallback を廃止し、設定ロードは fail-fast にする。
- `Any` ベースの config 契約をやめ、型付き設定モデルへ移行する。
- `ReadTextFileRequest` の head/tail 排他以外にも、paths 数上限、grep パターン、file_pattern、directory depth 上限などをモデル層で厳密に検証する。
- `ReadMediaFileResponse.content_base64` や `FileResult.content/error` など曖昧な nullable 契約を見直し、成功/失敗を別モデルまたは discriminated union にする。

#### Medium
- request/response モデルをカテゴリ別（directory/text/media/search/info）に分割し、共有ベースモデルを導入する。
- size/depth/max count の設定依存制約をモデル定義から切り離し、validator に明示注入する。

#### Low
- description 文言の一貫性を整理する。

---

### 3. `read_service.py`

#### High
- `ReadFileService` が持つ責務（path/security、tree build、text/media read、multi-read、search、grep、formatting、dispatch table）を分割する。
- service 層から `HTTPException` を除去し、domain/service 例外へ置き換える。
- `fmt_*` 系メソッドを service 本体から分離し、formatter 層へ移す。
- `read_multiple_files()` の部分成功/部分失敗を曖昧に `FileResult` へ詰める形を見直し、失敗契約を明確にする。
- grep / directory tree / media read の重い I/O 系で fail-soft にしない。失敗は warning で継続せず、原因を明示して返す。
- `_LazyReadFileService` のグローバル singleton 依存をやめ、server から DI する。

#### Medium
- `_build_tree()`, `_count_tree_nodes()`, `_slice_lines()`, `_collect_grep_matches()` を専用 helper/component に分割する。
- text / media / grep / tree / metadata の責務を個別 service に分ける。
- base64 変換、text read、encoding 前提を明示化し、バイナリ/テキスト判定を強化する。

#### Low
- logger 文面と metrics の粒度を統一する。

---

### 4. `read_tools.py`

#### High
- 手書き `_MCP_TOOLS` 定義を廃止し、`read_models.py` の request model から schema 生成へ移行する。
- route 名 / service 名 / tool 名 / request model の整合性を自動検証できるようにする。

#### Medium
- 説明文、required、optional の表記と粒度を揃える。
- 読み取り系ツールをカテゴリ別に分割し、schema 定義を宣言的に管理する。

#### Low
- 文言重複を削減する。

---

### 5. `read_server.py`

#### High
- route 関数の繰り返し構造（request → service → logger → response）を declarative registration にまとめる。
- server 層が service singleton に直接依存する構造をやめ、依存注入へ切り替える。
- `_dispatch_read_tool()` と `FileReadMCPServer.dispatch()` の責務を整理し、FastAPI transport と MCP dispatch を共通 registry/adapter に寄せる。
- server 層で warning ログを追加するだけの処理を減らし、統一例外ハンドラで service 例外を HTTP response へ変換する。

#### Medium
- `health()` に設定・allowed dirs・service 初期化状態を含められるようにする。
- `list_tools()` を `read_tools.py` の静的値ではなく registry から返す構造にする。

#### Low
- endpoint 名と function 名の一貫性を整理する。

---

### 6. `write_models.py`

#### High
- `_get_cfg()` の fallback を廃止し、設定は fail-fast で型付きロードする。
- `WriteFileRequest`, `EditFileRequest`, `CreateDirectoryRequest`, `MoveFileRequest` の path/content/encoding/edit list に対する制約を強化する。
- `EditOperation` の old/new text 契約を厳密化し、空置換や重複適用時のルールを model 層で補強する。

#### Medium
- write 系 request/response を operation 別に整理し、共通 path model を導入する。
- バイト数上限や dry-run 依存の制約を validator と service で役割分担する。

#### Low
- Field description の粒度統一。

---

### 7. `write_service.py`

#### High
- service 層から `HTTPException` を除去し、domain/service 例外へ置き換える。
- `_apply_text_edits()` / `_write_if_changed()` / move/create/write の責務を分離し、I/O と差分生成を別コンポーネント化する。
- 書き込み処理を原子的にし、部分書き込みや中途失敗でファイル破損を残さない設計へ変更する。
- dry-run 契約を正式化し、write/edit/move/create で戻り値と効果を統一する。
- `_LazyWriteFileService` を廃止し、DI 化する。

#### Medium
- text edit の差分生成と actual apply を分離する。
- shutil/move 操作の上書き/衝突/同名判定を厳密化する。
- create directory / write file / edit file / move file を個別 command service に割る。

#### Low
- logger メッセージの統一。

---

### 8. `write_server.py`

#### High
- route 群の重複処理を declarative registration に置き換える。
- server 層から singleton 依存を排除し、service 注入に変更する。
- `_dispatch_write_tool()` / `dispatch()` を共通 command registry に寄せる。
- 例外→HTTP 変換を統一し、logger/warning を個別 route に書かない。

#### Medium
- `health()` を設定・service ready 状態込みにする。
- list_tools を registry 由来に統一する。

#### Low
- endpoint 命名と docstring の整理。

---

### 9. `delete_models.py`

#### High
- `_get_cfg()` fallback を廃止し、設定ロードを fail-fast にする。
- `DeleteFileRequest` / `DeleteDirectoryRequest` の recursive・dry_run の意味と制約を厳密にする。
- delete 成功/失敗の戻り値が `deleted: bool` と info 文字列だけの構造を見直し、結果型を明確にする。

#### Medium
- dry-run と actual delete の差分情報を型で表現する。
- path 共通モデルと directory delete 専用モデルへ整理する。

#### Low
- description の表現を揃える。

---

### 10. `delete_service.py`

#### High
- service 層から `HTTPException` を除去し、domain/service 例外へ置き換える。
- file delete / directory delete / recursive delete / dry-run preview / info formatting の責務を分離する。
- recursive delete の安全境界（allowed_dirs, symlink, root path, empty dir 判定）を厳密化する。
- dry-run でも取得する情報と実 delete 時の監査・結果契約を統一する。
- `_LazyDeleteFileService` を廃止し、DI 化する。

#### Medium
- `shutil.rmtree` 相当の処理を直接呼ぶ場合のエラー分類を整理する。
- info 文字列生成を formatter へ分離する。
- delete preview と actual delete を別 service に分ける。

#### Low
- logger 粒度を統一する。

---

### 11. `delete_server.py`

#### High
- route 群の繰り返しを declarative registration に変更する。
- singleton 依存と `_dispatch_delete_tool()` の動的 dispatch を整理する。
- server 層を transport 専用にし、delete service の例外は統一ハンドラで HTTP response に変換する。

#### Medium
- `health()` を初期化状態まで返すようにする。
- list_tools と delete tool schema の整合性を registry で担保する。

#### Low
- endpoint 名と説明を整理する。

## 作業ステップ

1. 共通ポリシー固定
   - `common.py` の path/size/type 検証を domain 例外ベースへ改修する。
   - 読み書き削除で共通利用する policy と exception を定義する。

2. 設定とモデルの fail-fast 化
   - `read_models.py`, `write_models.py`, `delete_models.py` の `_get_cfg()` を廃止し、型付き設定注入へ変更する。
   - request/response モデルと schema の対応を整理する。

3. service 層の transport 非依存化
   - `read_service.py`, `write_service.py`, `delete_service.py` から `HTTPException` を除去する。
   - formatter、helper、I/O、dry-run、dispatch を service から切り離す。

4. server 層の thin transport 化
   - `read_server.py`, `write_server.py`, `delete_server.py` の route 群を declarative registration に変更する。
   - DI、統一例外ハンドラ、共通 dispatch registry を導入する。

5. schema / tools 単一化
   - `read_tools.py` を request model 由来の schema 生成へ変更する。
   - 将来的に write/delete 側も同じ仕組みへ拡張できる形にする。

6. 異常系テスト追加
   - config load failure
   - disallowed path access
   - symlink / path traversal
   - size limit exceeded
   - text edit target not found
   - move collision
   - recursive delete restrictions
   - read media encoding failure
   - schema と route / service の不一致

## 完了条件

- `except Exception` に依存した fallback が `*_models.py` から除去されている。
- `common.py` と `*_service.py` から `HTTPException` が除去され、domain/service 例外へ置き換わっている。
- `read/write/delete` すべてで path/size/type 検証が共通化され、厳密に fail-fast している。
- `read_tools.py` の schema と request model が単一ソースで管理されている。
- `*_server.py` が thin transport layer となり、route 関数内に業務ロジックや動的 dispatch 詳細を持っていない。
- singleton `_Lazy*Service` 依存が除去され、DI へ置き換わっている。
- dry-run と actual execution の契約が write/delete 系で統一されている。
- 不正入力、設定不備、権限違反、I/O 失敗が warning や暗黙 fallback に丸められず、明示的失敗として扱われている。
