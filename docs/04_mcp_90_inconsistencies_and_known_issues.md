---
title: "MCP Inconsistencies and Known Issues"
category: mcp
tags:
  - mcp
  - inconsistencies
  - known-issues
  - bugs
related:
  - 04_mcp_00_document-guide.md
---

# MCPにおける不整合と既知の問題

このファイルは、ドキュメント再構成の過程で発見されたMCPレイヤーにおけるバグ、未実装の機能、
仕様間の矛盾、未定義動作をカタログ化するものである。

各エントリの形式:
- **Type:** `Implementation bug` / `Unimplemented` / `Document inconsistency` / `Undefined` / `Needs confirmation`
- **Impact scope:** 影響を受けるモジュール/動作
- **Statement A / B:** 矛盾する事実(該当する場合)
- **Current safe interpretation:** 不明な場合に前提とすべき内容
- **Recommended action:** 必要な修正または調査
- **Notes for AI reference:** この問題についてAIが推論する際の指針

---

## SPEC-01: `04_mcp_06_11` からの `04_mcp_90 §SPEC-01` 参照が本ファイル内に存在しない（解決済み）

- **Type:** `Document inconsistency` — **Resolved**(本エントリの追加によりリンク切れは解消済み)
- **Impact scope:** `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` から本ファイルへのリンク（ドキュメント内リンクの整合性のみ。実装動作には影響しない）
- **Statement A:** `04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` の冒頭注記は「ルーティングのドリフト検出（`route_resolver.py` の `validate_routing_against_live`）と tool definitions チェック（`repl_health.py`）は異なる機能である — `04_mcp_90 §SPEC-01` も参照」と記載している。
- **Statement B:** 本ファイル（`04_mcp_90_inconsistencies_and_known_issues.md`）には `SPEC-01` という見出し・エントリは（本エントリを追記する前の時点で）存在しなかった。参照先が実体を欠いた壊れた内部リンクになっていた。
- **Current safe interpretation:** 2つの検証機構は実装上明確に分離されている（根拠: `scripts/shared/tool_routing_validation.py` に `validate_routing_against_config` / `validate_routing_against_live` / `validate_all_routing` が定義され、`scripts/agent/repl_health.py` に `check_tool_definitions_startup` / `check_tool_definitions_runtime` が別途定義されている）。したがって `04_mcp_06_11` の技術的記述自体は実装と矛盾しない。矛盾していたのはリンク先の欠落のみであり、本エントリの追加によって解消したとみなしてよい。
- **Recommended action:** 対応不要（本エントリの追加により参照先が実体を持った）。今後 `04_mcp_06_11` 側を編集する場合は、参照テキストを本エントリ名（`SPEC-01`）に合わせて更新すること。
- **Notes for AI reference:** ルーティングのドリフト検出（config/live 突合）と tool definitions strict チェック（起動時の `/v1/tools` 比較）を混同しないこと。前者は `ToolRegistry` を正とした運用時ドリフト検知、後者は `config/agent.toml` の `tool_definitions` と実サーバー応答の起動時整合性チェックであり、責務が異なる。(根拠分類: Explicit in code)

---

## SPEC-02: `workflow_allowlist` empty-list behavior: RuntimeError vs Warning

- **Type:** `Document inconsistency` — **Resolved**(実装とドキュメントの乖離を解消)
- **Impact scope:** MCP security model documentation, pre-production checklist
- **Statement A:** 一部のドキュメントでは `workflow_allowlist=[]` の挙動が「warning」または「空リスト = すべてのワークフローを許可」として記述されていた
- **Statement B:** 実際のコード (`tests/test_cicd_mcp_service.py:129-130`) では、空の `workflow_allowlist` は起動時に **RuntimeError/CicdAuthorizationError** を発生させる (fail-closed)
- **Current safe interpretation:** 空の `workflow_allowlist` は fail-closed であり、startup に RuntimeError を投げる。`trigger_workflow` は常に拒否される。
- **Recommended action:** 影響を受けるすべてのドキュメントを更新し、empty-list → RuntimeError の関係を明確にする
- **Notes for AI reference:** `workflow_allowlist=[]` は fail-open ではない。これは fail-closed であり、startup に致命的な RuntimeError を投げる。この挙動は CI/CD サーバーのセキュリティポリシーの核心である。

---

## SPEC-03: `allowed_repos_mode` がコードから削除されたがドキュメントに残っている

- **Type:** `Document inconsistency` — **Resolved**(ドキュメントのクリーンアップが必要)
- **Impact scope:** `docs/05_agent_08_04_configuration-mcp-approval-obs.md`
- **Statement A:** ドキュメントに `GitHub allowed_repos / allowed_repos_mode` の記載が残っている
- **Statement B:** コードでは `allowed_repos_mode` は完全に削除済み (previous cleanup: `implementations/done/20260710-122419_github_config_fail_open_removal.md`)
- **Current safe interpretation:** `allowed_repos_mode` は存在しない。GitHub MCP は fail-closed-only で動作する (空の `allowed_repos` = deny all)。
- **Recommended action:** ドキュメントから `allowed_repos_mode` の参照を削除
- **Notes for AI reference:** このフィールドは過去に fail-open が削除された際に完全に除去されている。コードベース内にこのフィールドへの参照は存在しない。

---

## SPEC-04: ドキュメントに DB MCP サーバーの言及があるがサーバーは存在しない

- **Type:** `Document inconsistency` — **Resolved**(ドキュメントのクリーンアップが必要)
- **Impact scope:** MCP security model documentation, configuration references
- **Statement A:** ドキュメントに `db_allowlist` や DB MCP サーバーの設定に関する言及が存在する可能性がある
- **Statement B:** リポジトリ内には DB MCP サーバーの設定ファイルもコードも存在しない
- **Current safe interpretation:** DB MCP サーバーは存在しない。`db_allowlist` や関連設定はデッドコードである。
- **Recommended action:** ドキュメントから DB MCP サーバーおよび `db_allowlist` の参照を削除
- **Notes for AI reference:** このリポジトリには DB MCP サーバーの実装は存在しない。grep で `config/*db*_mcp_server.toml` と `scripts/` 内の db_mcp 参照を確認すること。

---

## MDQ ハイブリッド検索はstub（未実装）

- **Type:** `Unimplemented`
- **Impact scope:** `scripts/mcp_servers/mdq/search.py`, `scripts/mcp_servers/mdq/tools.py`
- **Current behavior:** `use_embedding = true` でハイブリッド検索が有効になるが、`_search_vector()` は常に空リストを返す。セマンティック検索の結果は得られない。
- **Affected config:** `config/mdq_mcp_server.toml` の `use_embedding = true`
- **Recommended action:** ハイブリッド検索を本番投入するには、`_search_vector()` の実装が必要
- **Notes for AI reference:** MDQ のハイブリッド検索（`use_embedding = true`）は未実装（stub）。セマンティック検索が必要な場合は RAG パイプラインを使用すること。

---

## Related Documents

- `04_mcp_00_document-guide.md`

## Keywords

mcp
inconsistencies
known-issues
bugs
