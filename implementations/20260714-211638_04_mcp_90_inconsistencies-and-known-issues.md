# Implementation Procedure: Normalize MCP Security Policy Documentation (Known Issues Inconsistencies)

## Goal

Update `04_mcp_90_inconsistencies_and_known_issues.md` to add entries documenting resolved discrepancies between documentation assumptions and actual implementation behavior.

## Scope

- `docs/04_mcp_90_inconsistencies_and_known_issues.md` only
- Add entries for known issues discovered during security policy normalization

## Assumptions

1. The requirement `requires/20260714_11_require.md` is the canonical specification for this task.
2. Implementation inspection has confirmed the following actual values:
   - `tool_definitions_strict` default = **False** (not true as implied by pre-production checklist)
   - Empty `workflow_allowlist` produces **RuntimeError/CicdAuthorizationError** (fail-closed), NOT a warning
   - `allowed_repos_mode` does **NOT** exist in codebase (was removed previously)
   - No DB MCP server exists

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

Add new inconsistency entries documenting the discrepancies found between documentation assumptions and actual implementation behavior.

### Method

- Append new entries to the existing file using the established format.
- Each entry follows the format: Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference.

### Details

#### Entry 1: workflow_allowlist RuntimeError vs Warning discrepancy

```markdown
## SPEC-02: `workflow_allowlist` empty-list behavior: RuntimeError vs Warning

- **Type:** `Document inconsistency` — **Resolved**(実装とドキュメントの乖離を解消)
- **Impact scope:** MCP security model documentation, pre-production checklist
- **Statement A:** 一部のドキュメントでは `workflow_allowlist=[]` の挙動が「warning」または「空リスト = すべてのワークフローを許可」として記述されていた
- **Statement B:** 実際のコード (`tests/test_cicd_mcp_service.py:129-130`) では、空の `workflow_allowlist` は起動時に **RuntimeError/CicdAuthorizationError** を発生させる (fail-closed)
- **Current safe interpretation:** 空の `workflow_allowlist` は fail-closed であり、startup に RuntimeError を投げる。`trigger_workflow` は常に拒否される。
- **Recommended action:** 影響を受けるすべてのドキュメントを更新し、empty-list → RuntimeError の関係を明確にする
- **Notes for AI reference:** `workflow_allowlist=[]` は fail-open ではない。これは fail-closed であり、startup に致命的な RuntimeError を投げる。この挙動は CI/CD サーバーのセキュリティポリシーの核心である。
```

#### Entry 2: allowed_repos_mode removal

```markdown
## SPEC-03: `allowed_repos_mode` がコードから削除されたがドキュメントに残っている

- **Type:** `Document inconsistency` — **Resolved**(ドキュメントのクリーンアップが必要)
- **Impact scope:** `docs/05_agent_08_04_configuration-mcp-approval-obs.md`
- **Statement A:** ドキュメントに `GitHub allowed_repos / allowed_repos_mode` の記載が残っている
- **Statement B:** コードでは `allowed_repos_mode` は完全に削除済み (previous cleanup: `implementations/done/20260710-122419_github_config_fail_open_removal.md`)
- **Current safe interpretation:** `allowed_repos_mode` は存在しない。GitHub MCP は fail-closed-only で動作する (空の `allowed_repos` = deny all)。
- **Recommended action:** ドキュメントから `allowed_repos_mode` の参照を削除
- **Notes for AI reference:** このフィールドは過去に fail-open が削除された際に完全に除去されている。コードベース内にこのフィールドへの参照は存在しない。
```

#### Entry 3: No DB MCP server

```markdown
## SPEC-04: ドキュメントに DB MCP サーバーの言及があるがサーバーは存在しない

- **Type:** `Document inconsistency` — **Resolved**(ドキュメントのクリーンアップが必要)
- **Impact scope:** MCP security model documentation, configuration references
- **Statement A:** ドキュメントに `db_allowlist` や DB MCP サーバーの設定に関する言及が存在する可能性がある
- **Statement B:** リポジトリ内には DB MCP サーバーの設定ファイルもコードも存在しない
- **Current safe interpretation:** DB MCP サーバーは存在しない。`db_allowlist` や関連設定はデッドコードである。
- **Recommended action:** ドキュメントから DB MCP サーバーおよび `db_allowlist` の参照を削除
- **Notes for AI reference:** このリポジトリには DB MCP サーバーの実装は存在しない。grep で `config/*db*_mcp_server.toml` と `scripts/` 内の db_mcp 参照を確認すること。
```

## Validation plan

1. Verify three new entries are added to the file.
2. Confirm each entry follows the established format.
3. Verify no stale references to `allowed_repos_mode`, `db_allowlist`, or DB MCP remain in any MCP-related documents.
4. Verify no broken cross-references from updated sections.
5. Run `pre-commit run --all-files` if linting is configured.
