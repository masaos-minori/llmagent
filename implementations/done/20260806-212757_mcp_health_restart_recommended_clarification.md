## Goal

Clarify why `restart_recommended` always returns `False` in `docs/04_mcp_02_02_startup-modes-and-health.md` and correct the stale present-tense descriptions of the (now removed) MCP watchdog.

## Scope

- **In-Scope**: Modifying `docs/04_mcp_02_02_startup-modes-and-health.md` to explain the permanent `False` status and adjust the phrasing around the watchdog.
- **Out-of-Scope**: Modifying `docs/04_mcp_06_12_watchdog-configuration-monitoring.md`, changing actual code behavior, or modifying any other documentation.

## Assumptions

1. The explanation must be added in Japanese to maintain consistency with the document.
2. The term "旧ウォッチドッグ" will be used to refer to the removed component.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire health section: rejected because scope is limited to adding clarifications.
- Create a separate document for watchdog deprecation: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/04_mcp_02_02_startup-modes-and-health.md`

### Procedure

1. Locate the "標準的な `/health` レスポンスのセマンティクス" subsection in the document.
2. Identify insertion points for:
   - Causal explanation for why `restart_recommended` always returns `False` (no restart-fixable failures + watchdog removal).
   - Tense correction for watchdog mentions (present → past/removed context).
3. Update the `restart_recommended` bullet point and the "注記（実装の現状）" paragraph.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the health response section
grep -n "標準的な.*health\|restart_recommended\|Health.*Response" docs/04_mcp_02_02_startup-modes-and-health.md

# Find watchdog mentions
grep -n "watchdog\|ウォッチドッグ\|Watchdog" docs/04_mcp_02_02_startup-modes-and-health.md

# Find the note paragraph
grep -n "注記.*実装\|注記.*現状" docs/04_mcp_02_02_startup-modes-and-health.md
```

Insertion pattern:
- After `restart_recommended` description, add causal explanation:
  - "この値が常にFalseになる理由：再起動で修復可能な障害がないため、かつ旧ウォッチドッグの削除により再起動推奨フラグが不要になったためです。"
- Correct watchdog tense from present to past:
  - Present tense → Past tense (e.g., "ウォッチドッグは監視しています" → "旧ウォッチドッグは監視していました")
- Update "注記（実装の現状）" paragraph to mention watchdog removal.

### Target file

Verification

### Procedure

1. Manually verify the addition using `grep` to ensure the explanation and corrected tense are present.
2. Run lint check on the modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify restart_recommended explanation added
grep -c "restart_recommended.*False\|False.*restart" docs/04_mcp_02_02_startup-modes-and-health.md

# Verify watchdog tense corrected
grep -c "旧ウォッチドッグ\|was.*watchdog\|watchdog.*was" docs/04_mcp_02_02_startup-modes-and-health.md

# Verify note paragraph updated
grep -c "注記.*実装.*現状" docs/04_mcp_02_02_startup-modes-and-health.md

# Run lint check
ruff check docs/04_mcp_02_02_startup-modes-and-health.md
```

Expected outcomes:
- Causal explanation for `restart_recommended = False` present
- Watchdog mentions use past tense / removed context
- Zero lint errors on the file

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/04_mcp_02_02_startup-modes-and-health.md` | Docs file | 0 errors |
| Manual | `grep` | Paragraph content | Explanation and corrected tense found |

## Out of scope

- Modifications to `docs/04_mcp_06_12_watchdog-configuration-monitoring.md`.
- Changes to actual code behavior.
- Modifications to any other documentation.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-153707_require.md
- Source plan: plans/20260805-122815_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-212757
- Related target files: docs/04_mcp_02_02_startup-modes-and-health.md
