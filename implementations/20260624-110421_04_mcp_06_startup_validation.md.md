# Implementation: Unify Strict Tool-Definition Validation Behavior

## Goal

Make `docs/04_mcp_06_configuration_and_operations.md` §"Startup Validation Behavior" the single normative source for `tool_definitions_strict`. Mark SPEC-01 in `04_mcp_90` as Resolved. Add a cross-reference in `04_mcp_03`.

## Scope

**In:**
- `docs/04_mcp_06_configuration_and_operations.md` — verify completeness of behavior table (lines 303–316)
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` — update SPEC-01 to "Resolved"
- `docs/04_mcp_03_routing_lifecycle_and_execution.md` — add cross-reference sentence

**Out:** No code changes.

## Assumptions

1. `04_mcp_06` lines 303–316 already cover all 4 startup validation cases.
2. SPEC-01 is stale; it predates the `04_mcp_06` update.
3. `04_mcp_03` does not currently reference startup validation.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`, `docs/04_mcp_90_inconsistencies_and_known_issues.md`, `docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. Read `docs/04_mcp_06_configuration_and_operations.md` lines 295–325 to verify the 4-case behavior table.
2. If any of the 4 cases is missing, add it before proceeding.
   - Case 1: schema mismatch, `tool_definitions_strict = false` → WARNING, agent starts
   - Case 2: schema mismatch, `tool_definitions_strict = true` → FATAL, agent exits
   - Case 3: partial server unreachable → WARNING, remaining tools used
   - Case 4: all servers unreachable → validation skipped, WARNING
3. Read `docs/04_mcp_90_inconsistencies_and_known_issues.md` to find SPEC-01 (lines 16–22).
4. Update SPEC-01 status from "Open" / "Undocumented" to `**Resolved** — normative behavior in \`04_mcp_06\` §Startup Validation Behavior`.
5. Remove any duplicate normative text from SPEC-01 body (keep only the status + reference).
6. Read `docs/04_mcp_03_routing_lifecycle_and_execution.md` startup/lifecycle section.
7. After the lifecycle section heading, add cross-reference:
   ```
   ツール定義の起動時バリデーション動作については `04_mcp_06` §Startup Validation Behavior を参照。
   ```

### Method

File reads then Edit tool patches. No shell commands required.

### Details

**SPEC-01 updated text pattern:**
```markdown
### SPEC-01: tool_definitions_strict startup behavior
**Status:** Resolved
Normative behavior is documented in `04_mcp_06` §Startup Validation Behavior.
```

**Cross-reference placement in `04_mcp_03`:**
Find the `## Lifecycle` or `## Startup` heading and insert the reference sentence as the first paragraph after that heading.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| SPEC-01 resolved | `grep -n "Resolved" docs/04_mcp_90_inconsistencies_and_known_issues.md` | found near SPEC-01 |
| Cross-reference in 04_mcp_03 | `grep -n "04_mcp_06" docs/04_mcp_03_routing_lifecycle_and_execution.md` | found |
| 4 cases in 04_mcp_06 | `grep -n "unreachable\|mismatch\|strict" docs/04_mcp_06_configuration_and_operations.md` | 4+ matches |
| No code changes | `git diff scripts/` | empty |
