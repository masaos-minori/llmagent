# Implementation Procedure: docs/03_rag_{02,05,90}_*.md (file:// 再取り込み統一)

## Goal

`file://` 再取り込み動作の記述を 3 つのドキュメントで統一する。

## Scope

**In:**
- `docs/03_rag_02_ingestion_pipeline.md` — 用語標準化
- `docs/03_rag_05_configuration_and_operations.md` — 用語標準化 + `rag_crawler.toml` → `config/rag_pipeline.toml`
- `docs/03_rag_90_inconsistencies_and_known_issues.md` — DESIGN-4 クローズノート確認

**Out:** crawler.py / ingester.py コード変更

## Procedure

### Phase 1: 3 ファイルの file:// セクションを読む

- `03_rag_02` lines 118-160
- `03_rag_05` lines 246-291
- `03_rag_90` lines 80-95

### Phase 2: 用語統一ルール

| 非標準 | 標準表記 |
|---|---|
| sha256 / SHA256 | SHA-256 |
| `last_modified` / mtime | `last_modified` (コード), mtime (散文) |
| 強制再取込 / 強制再インジェスト | `--force` による強制再取り込み |

### Phase 3: 各ドキュメントを更新

矛盾を解消し、正規表現 `SHA-256` / `mtime` / `--force` のみを使用する。

## Validation plan

| Check | Command | Expected |
|---|---|---|
| 用語一貫 | `grep -n "sha-256\|sha256\|SHA256\|SHA-256" docs/03_rag_{02,05,90}*.md` | SHA-256 のみ |
| コード変更なし | `git diff scripts/` | no changes |
