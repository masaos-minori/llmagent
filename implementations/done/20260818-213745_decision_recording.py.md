## Goal

Investigate and record formal decisions for five ambiguous areas in the system's configuration and behavior, converting uncertainty into actionable direction for future development.

## Scope

**In-Scope:**
- Investigate each ambiguity item against current source.
- Document decisions for all five items.
- Create follow-up issues for items requiring technical implementation.

**Out-of-Scope:**
- Implementation of follow-up issues (document only).
- Changes to any Python code beyond documentation updates.

## Assumptions

- The require document's claims about ambiguities are real but may be partially incorrect based on current source state (verify each claim against current source).
- Decisions should be recorded as formal documents in `decisions/` directory following project conventions.
- Follow-up issues should be created in `issues/` directory when implementation is needed.

## Design decisions

- Record decisions as separate documents in `decisions/` — ensures traceability and allows future re-evaluation.
- Create follow-up issues in `issues/` when implementation is needed — separates decision-making from implementation.
- Include evidence and reasoning in each decision document — prevents future confusion about why a decision was made.

## Alternatives considered

- Merge all five decisions into a single document — rejected because it would make individual decisions harder to find and update.
- Create implementation tasks directly instead of decision documents — rejected because decisions should be recorded before implementation begins.
- Leave ambiguities unresolved — rejected because the goal is converting uncertainty into actionable direction.

## Investigation Procedures

### Item 1: Git-MCP write guard asymmetry

1. Compare TOOL_LIST entries in git-mcp vs github-mcp:
   ```bash
   rg -n "TOOL_LIST\|is_write" scripts/mcp_servers/git/ scripts/mcp_servers/github/
   ```
2. Identify which server(s) have write tools without proper guards.
3. Determine if the asymmetry is intentional or a bug.

### Item 2: Workflow approval gate default state

1. Review workflow approval gate implementation:
   ```bash
   rg -n "approval.*gate\|approve.*workflow\|workflow.*approval" scripts/
   ```
2. Determine what the default state is (approved/denied/pending).
3. Document whether the default is correct or needs adjustment.

### Item 3: Diagnostics config hot-reloadability

1. Check if diagnostics config is used in hot paths:
   ```bash
   rg -n "diagnostics.*config\|diag_config\|DiagnosticConfig" scripts/
   ```
2. Determine if changes to diagnostics config are expected at runtime.
3. If yes, document that `/reload` should support diagnostics config reload.

### Item 4: RagPipelineConfig defaults vs. TOML settings

1. Compare RagPipelineConfig defaults against operational TOML:
   ```bash
   rg -n "RagPipelineConfig\|rag_pipeline.*toml" scripts/
   ```
2. Diff defaults vs. actual config values.
3. Document whether defaults should be aligned with TOML or vice versa.

### Item 5: Unused DTOs for RAG-003/RAG-004

1. Search for DTO references across repo:
   ```bash
   rg -n "RAG.*DTO\|dto.*rag" scripts/ tests/
   ```
2. Determine if DTOs are truly unused.
3. If unused, document that they should be removed.

## Decision Recording

### Procedure

For each ambiguity item:
1. Create a decision document in `decisions/` with the following structure:
   ```markdown
   ## Title
   ## Context
   ## Decision
   ## Rationale
   ## Evidence
   ## Follow-up Actions
   ```
2. Include evidence gathered during investigation.
3. Document rationale for the decision.
4. List follow-up actions if implementation is needed.

### Method

Decision document template:

```markdown
## [Item Title]

### Context
[Brief description of the ambiguity]

### Decision
[The formal decision — e.g., "Remove X", "Keep Y", "Add Z"]

### Rationale
[Why this decision was made — include evidence]

### Evidence
[Grep results, diffs, or other verification steps taken]

### Follow-up Actions
[List of actions needed — e.g., "Create issue in issues/", "Update docs/"]
```

### Details

- Use concise, direct sentences per project convention.
- Include specific file paths and line numbers in evidence sections.
- Link to relevant source files where decisions apply.

## Compatibility considerations

- Decision documents do not affect runtime behavior.
- Follow-up issues do not change anything until implemented.
- No API contract changes.

## Security considerations

- N/A — no new secrets, keys, or sensitive data introduced.
- No changes to authentication, authorization, or data access patterns.

## Rollback considerations

- Revert decision documents: delete them from `decisions/`.
- Revert follow-up issues: delete them from `issues/`.
- No schema changes — rollback is purely document-level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All decision documents | Manual review: verify decisions are clear and actionable | Visual inspection of each decision doc | No ambiguity remains |
| All follow-up issues | Manual review: verify issues are actionable | Visual inspection of each issue doc | Each issue has clear acceptance criteria |
| Repo-wide | Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept, 0 broken |

## Out of scope

- Sign-off gate enforcement (manual step before implementation).
- Deployment steps (Phase 3 of the plan).
- Documentation updates beyond decision documents and follow-up issues.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260817_09_issue.md
- Source requirement: requires/20260818-171400_require.md
- Source plan: plans/20260818-183845_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-213745
- Related target files: None
