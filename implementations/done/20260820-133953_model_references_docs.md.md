# Implementation Procedure: Reconcile Model/Embedding References in Overview, Deployment, and RAG Config Docs

## Goal
Establish `docs/02_deployment.md` §1.4 as the single canonical model-reference table. Update `docs/01_overview-files-01-build.md` §3 and `docs/03_rag_05_1-configuration-reference.md` `embedding_dims` row to match or link to the canonical table.

## Scope
- Target files:
  - `docs/02_deployment.md` — canonical model table (§1.4)
  - `docs/01_overview-files-01-build.md` — §3 model list
  - `docs/03_rag_05_1-configuration-reference.md` — `embedding_dims` row
- Make all three agree on chat LLM and embedding model filenames/dimensions

## Assumptions
- `docs/02_deployment.md` §1.4 is the most natural canonical source (operator-facing provisioning guide)
- Embedding model is multilingual-e5-small variant (384 dims) in both `docs/01` and `docs/02`; `docs/03`'s "all-MiniLM-L6-v2" is a doc-only naming error
- Exact GGUF quantization suffix and chat LLM identity cannot be determined from repo (served by external llama-server on remote hosts) — UNK-01 blocks final literal values

## Design decisions
- Mark `docs/02_deployment.md` §1.4 as canonical with inline note
- `docs/01_overview-files-01-build.md` §3: replace model list with cross-reference to canonical table (or match values if UNK-01 answered)
- `docs/03_rag_05_1-configuration-reference.md` `embedding_dims` row: drop "all-MiniLM-L6-v2", reference canonical embedding model name/link
- If UNK-01 unanswered at implementation time: use "see `docs/02_deployment.md` §1.4 for current canonical filename" placeholder

## Implementation
### Target files
1. `docs/02_deployment.md`
2. `docs/01_overview-files-01-build.md`
3. `docs/03_rag_05_1-configuration-reference.md`

### Procedure
1. Re-confirm line numbers in all three files immediately before editing
2. Edit `docs/02_deployment.md` §1.4: add canonical annotation; insert confirmed filenames if UNK-01 answered, else leave current best-known with "unconfirmed — see issue #{UNK-01}" marker
3. Edit `docs/01_overview-files-01-build.md` §3: replace model list with cross-reference link to `docs/02_deployment.md` §1.4 (or match values if UNK-01 answered)
4. Edit `docs/03_rag_05_1-configuration-reference.md` `embedding_dims` row: replace "all-MiniLM-L6-v2" with canonical embedding model name or cross-reference link

### Method
Direct Markdown editing with exact line matching

### Details
**`docs/02_deployment.md` §1.4 (around line 45):**
```markdown
### 1.4 LLM モデルの取得

モデルファイルは `/opt/llm/models/` に配置します。ファイル名は、各サービスの構成（`model-path` 等）で使用される名称と一致させる必要があります。

> **Canonical source** — このテーブルがモデルファイル名の正典です。`docs/01_overview-files-01-build.md` と `docs/03_rag_05_1-configuration-reference.md` はここを参照します。

| モデル | ファイル名 |
|---|---|
| multilingual-e5-small (埋め込み) | multilingual-e5-small-Q8_0.gguf |
| gemma-4-e4b-it (LLM) | gemma-4-e4b-it-Q4_K_M.gguf |
| Qwopus3.6-35B-A3B-v1 (LLM) | Qwopus3.6-35B-A3B-v1-MTP-Q4_K_M.gguf |
```
(If UNK-01 answered, replace filenames with confirmed values; else add "unconfirmed — see issue #{UNK-01}" marker next to each filename)

**`docs/01_overview-files-01-build.md` §3 (around line 30-33):**
```markdown
## 3. ファイル構成

デプロイ先のディレクトリ構成:

``` text
/opt/llm/
├─ llama.cpp/                                 # llama.cpp ソース・ビルド成果物
├─ models/
│   ├─ Qwen3.6-Instruct-Q4_K_M.gguf           # チャット/コード生成用 LLM (MQE・再ランク兼用, :8080)
│   └─ multilingual-E5-small.gguf             # 埋込用 LLM (384 次元, :8081)
```
```
Replace with:
```markdown
## 3. ファイル構成

デプロイ先のディレクトリ構成:

``` text
/opt/llm/
├─ llama.cpp/                                 # llama.cpp ソース・ビルド成果物
├─ models/
│   ├─ (chat LLM)  # 正典ファイル名は [docs/02_deployment.md §1.4](02_deployment.md#14-llm-モデルの取得) 参照
│   └─ (embedding LLM)  # 正典ファイル名は [docs/02_deployment.md §1.4](02_deployment.md#14-llm-モデルの取得) 参照
```
```
Or if UNK-01 answered, use the confirmed filenames directly.

**`docs/03_rag_05_1-configuration-reference.md` `embedding_dims` row (around line 68):**
```markdown
| `embedding_dims` | `384` | float32埋め込みベクトルの次元数 (モデルと一致必須: all-MiniLM-L6-v2 = 384) |
```
Replace with:
```markdown
| `embedding_dims` | `384` | float32埋め込みベクトルの次元数 (モデルと一致必須: 正典モデル名は [docs/02_deployment.md §1.4](02_deployment.md#14-llm-モデルの取得) 参照) |
```

## Compatibility considerations
- Documentation-only changes
- No code behavior changes
- Cross-references are bidirectional

## Security considerations
- None — documentation only

## Rollback considerations
- Git revert of modified files

## Validation plan
- Manual diff: all three docs agree on model names/dimensions or correctly cross-reference canonical table
- `uv run check-mcp-docs` — no new broken links
- No `scripts/` files changed (`git diff --stat -- scripts/` empty)

## Out of scope
- Determining actual GGUF filenames (UNK-01 — requires operator input)
- Changing external llama-server configurations

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221506_require.md
- Source plan: plans/20260819-174858_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-133953
- Related target files: docs/01_overview-files-01-build.md, docs/02_deployment.md, docs/03_rag_05_1-configuration-reference.md