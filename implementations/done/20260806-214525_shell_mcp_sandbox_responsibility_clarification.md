## Goal

Update `docs/04_mcp_04_02_file-write-file-delete-shell.md` to explicitly state that shell-mcp itself does not enforce production sandboxing, but rather the Agent layer performs this enforcement during its startup sequence.

## Scope

- **In-Scope**: Modifying the "セキュリティ注記" (Security Note) section in `docs/04_mcp_04_02_file-write-file-delete-shell.md` to specify the exact component responsible for production-mode enforcement.
- **Out-of-Scope**:
  - Modifying any source code.
  - Modifying file-write-mcp or file-delete-mcp sections.

## Assumptions

1. The current text in `docs/04_mcp_04_02_file-write-file-delete-shell.md` already discusses the `sandbox_backend="none"` default and production error raising, but lacks the specific attribution.
2. The user wants to maintain the existing Japanese-primary/English-secondary heading style.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire shell-mcp doc: rejected because scope is limited to clarifying responsibility.
- Create a separate document for sandbox enforcement: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/04_mcp_04_02_file-write-file-delete-shell.md`

### Procedure

1. Verify existence of the target file.
2. Locate the "セキュリティ注記 — サンドボックスはデフォルトで無効:" section in the document.
3. Append/Update the text within the "本番環境での強制:" subsection to include:
   - Explicit statement that shell-mcp itself does not perform production-mode checks or enforcement.
   - Attribution of enforcement to the Agent layer via `scripts/agent/repl_health.py::audit_security_defaults()` called from `scripts/agent/startup.py`.
   - Mention that this enforcement is bypassed if shell-mcp is run independently of the Agent's startup path.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the security note section
grep -n "セキュリティ注記\|Security.*Note\|サンドボックス.*デフォルト.*無効" docs/04_mcp_04_02_file-write-file-delete-shell.md

# Find the production enforcement subsection
grep -n "本番環境.*強制\|production.*enforcement" docs/04_mcp_04_02_file-write-file-delete-shell.md

# Verify audit_security_defaults location
grep -rn "def audit_security_defaults" scripts/agent/repl_health.py

# Verify startup.py reference
grep -rn "audit_security_defaults" scripts/agent/startup.py
```

Insertion pattern:
- After the existing "本番環境での強制:" text, append:
  ```markdown
  > **注意**: shell-mcp 自体は本番モードのチェックや強制を行いません。本番環境での強制は、Agent の起動シーケンス（`scripts/agent/startup.py` から呼び出される `scripts/agent/repl_health.py::audit_security_defaults()`）によって行われます。shell-mcp が Agent の起動パスとは独立して実行された場合、この強制はバイパスされます。
  ```

### Target file

Verification

### Procedure

1. Manually verify the added information against the requirements.
2. Ensure the formatting matches the existing `>`-blockquote style.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify shell-mcp responsibility statement present
grep -c "shell-mcp.*本体.*強制.*しない\|shell-mcp.*itself.*does.*not.*perform" docs/04_mcp_04_02_file-write-file-delete-shell.md

# Verify Agent layer attribution present
grep -c "Agent.*層.*強制\|Agent.*layer.*enforcement" docs/04_mcp_04_02_file-write-file-delete-shell.md

# Verify audit_security_defaults reference present
grep -c "audit_security_defaults" docs/04_mcp_04_02_file-write-file-delete-shell.md

# Verify startup.py reference present
grep -c "startup\.py" docs/04_mcp_04_02_file-write-file-delete-shell.md

# Verify blockquote formatting preserved
sed -n '/本番環境.*強制/,/^$/p' docs/04_mcp_04_02_file-write-file-delete-shell.md

# Run lint check
ruff check docs/04_mcp_04_02_file-write-file-delete-shell.md
```

Expected outcomes:
- Shell-mcp responsibility clarification added
- Agent layer attribution with specific function references
- Blockquote formatting preserved
- Zero lint errors on the file
- Document structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/04_mcp_04_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Content accuracy | Correct responsibility attribution included |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-153919_require.md
- Source plan: plans/20260805-123130_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-214525
- Related target files: docs/04_mcp_04_02_file-write-file-delete-shell.md
