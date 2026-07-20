---
title: "Local to Production Auth Migration"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Local to Production Auth Migration

## ローカルから本番への認証移行

ローカル開発環境から本番環境へ移行する際は、認証設定を変更する必要がある。以下の手順を注意深く実施すること。

### 移行手順

1. `config/agent.toml`で`security_profile`を`local`から`production`に切り替える
   - これにより起動時の認証要件の強制チェックが有効になる
   - `security_profile="local"`では空の`auth_token_env=""`が許容されるが、`security_profile="production"`では起動時に拒否される

2. すべてのHTTP MCPサーバーに空でない認証シークレットを設定する
    - `config/agent.toml`内の`transport="http"`を使用する各`[mcp_servers.*]`エントリには、空でない`auth_token_env`または`auth_token_file`が必須である
    - 環境変数による注入やシークレット管理(例: `conf.d/`配下のファイル)を使用し、設定ファイルにシークレットをハードコードしないこと

3. エージェントプロセスを再起動する(`/reload`は使用しないこと)
   - `/reload`は実行時に`[mcp_servers.*]`を変更しない — MCPサーバー定義の変更にはエージェントの完全な再起動が必要である
   - subprocessモードサーバーの自動再起動(`ensure_ready()`、次回のtool dispatch時)も既存の起動時設定を使うのみで、保留中の`/reload`設定変更は適用しない

4. `/mcp status`で確認する
   - すべてのサーバーが`OK`ステータスを示していることを確認する
   - 認証関連の失敗を報告しているサーバーがないことを確認する

5. 認証トークンの欠落・不一致について起動ログを確認する
   - 起動時に認証失敗に関するエラーがないか確認する
   - 新たに認証を要求するようになったサーバーについて、`/opt/llm/logs/agent.log`のトランスポート層エラーを確認する

### トラブルシューティング

#### `auth_token_env` / `auth_token_file` が空

症状: `security_profile="production"`の状態で、エージェントが認証エラーにより起動に失敗する。

原因: `security_profile="production"`であるにもかかわらず、少なくとも1つのHTTP MCPサーバーで`auth_token_env=""`または`auth_token_file`が未設定になっている。

対処: `config/agent.toml`で該当する各サーバーに有効な`auth_token_env`または`auth_token_file`を設定する。

#### 環境変数によるシークレットの欠落

症状: サーバーは起動するが、依存関係の失敗によりヘルスチェックが失敗する。

原因: `env`フィールドまたは設定キーが参照する環境変数が設定されていない。

対処: 起動前に、必要なシークレットがエージェントプロセスの環境で利用可能であることを確認する。

#### Bearerトークンの不一致

症状: `auth_token_env`または`auth_token_file`が設定されているにもかかわらず、ツール呼び出しが認証エラーを返す。

原因: Bearerトークンの値がMCPサーバーの期待値と一致していない。

対処: MCPサーバーが期待する認証情報とトークン値を照合する。トークンは`Authorization: Bearer <token>`ヘッダーとして渡される。

#### `/reload`とフル再起動の違い

症状: 設定内の`auth_token_env`または`auth_token_file`を変更した後、`/reload`を実行しても効果が反映されない。

原因: `/reload`は実行時に`[mcp_servers.*]`を変更することは一切ない。MCPサーバー定義(URL、認証トークン、起動モード、トランスポート、コマンド、環境)の変更には、常にエージェントの完全な再起動が必要である。

対処: エージェントプロセスを停止し、再起動して新しい認証設定を反映させる。


### Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

### Keywords

configuration
