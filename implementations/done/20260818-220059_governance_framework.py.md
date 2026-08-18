## Goal

Establish a deterministic documentation governance framework that resolves conflicts between code, design docs, config, and other sources. Define canonical-source precedence, area-specific canonical maps, area dependency graph, change-impact matrix, RACI model, and merge conditions.

## Scope

**In-Scope:**
- Define project-wide canonical-source precedence rules.
- Create area-specific canonical document maps.
- Build area dependency graph with permitted directions/cycles.
- Develop change-impact matrix for architecture/config/behavior changes.
- Implement documentation RACI model.
- Define merge conditions for open issues and deferred decisions.

**Out-of-Scope:**
- Modifying existing governance documents directly.
- Changing source code behavior.
- Adding new MCP servers.
- Database schema changes.

## Assumptions

- Existing governance documents (`00_governance_01_documentation-governance.md`, `00_governance_02_canonical-source-rule.md`) provide foundational rules that must be extended, not replaced.
- Eight areas defined in governance doc are stable: Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance.
- Current governance structure is incomplete — needs concrete canonical maps and dependency graphs.
- RACI model must cover all eight areas with clear reviewer/approver assignments.
- Merge conditions must prevent merging when critical open issues exist.

## Design decisions

- Canonical-source precedence follows Code > Tests > ADRs > Specs > Config > Docs — ensures source of truth is always the most authoritative.
- Area-specific canonical maps created per area — eliminates ambiguity about which document is authoritative.
- Area dependency graph uses explicit direction constraints — prevents circular dependencies.
- Change-impact matrix distinguishes architecture/config/behavior/document-only changes — enables accurate impact assessment.
- RACI model assigns specific roles per area — ensures accountability.
- Merge conditions tied to open issue status — prevents merging when critical issues exist.

## Alternatives considered

- Keep governance implicit — rejected because it causes inconsistency and makes auditing difficult.
- Use binary approval (yes/no) — rejected because it doesn't capture nuanced risk levels.
- Apply same merge conditions everywhere — rejected because different areas need different thresholds.

## Implementation

### Procedure

#### Part A: Define canonical-source precedence hierarchy

1. Search for existing precedence rules:
   ```bash
   rg -n "canonical.*source\|precedence\|優先順位" docs/
   ```
2. Define canonical-source precedence hierarchy:
   ```markdown
   ## Canonical-Source Precedence
   
   When conflicts arise between documentation and code/config, the following precedence applies:
   
   | Rank | Source Type | Example | Notes |
   |------|-------------|---------|-------|
   | 1 | Code | `scripts/eventbus/publisher.py` | Authoritative for runtime behavior |
   | 2 | Tests | `tests/eventbus/test_publisher.py` | Authoritative for expected behavior |
   | 3 | ADRs | `docs/adrs/ADR-001.md` | Authoritative for architectural decisions |
   | 4 | Specifications | `docs/specification.md` | Authoritative for functional requirements |
   | 5 | Configuration | `config/system.toml` | Authoritative for operational parameters |
   | 6 | Documentation | `docs/architecture.md` | Authoritative for conceptual understanding |
   ```

### Method

Part A — Add precedence table to governance document:

```markdown
<!-- BEFORE -->
When conflicts arise, refer to the latest version of each document.

<!-- AFTER -->
When conflicts arise, apply the following precedence:
1. Code
2. Tests
3. ADRs
4. Specifications
5. Configuration
6. Documentation
```

### Details

- Precedence follows project convention — clear and actionable.
- Six tiers defined — eliminates ambiguity.
- Examples provided — helps readers understand scope.

---

#### Part B: Create area-specific canonical document maps

1. Search for existing canonical document maps:
   ```bash
   rg -n "canonical.*map\|Canonical.*Map" docs/
   ```
2. For each area, create canonical document map:
   ```markdown
   ## Area Canonical Maps
   
   ### Overview
   | Document | Authority | Status |
   |----------|-----------|--------|
   | docs/00_index.md | Primary | Active |
   | docs/architecture.md | Secondary | Active |
   
   ### Deployment
   | Document | Authority | Status |
   |----------|-----------|--------|
   | docs/deployment_guide.md | Primary | Active |
   | deploy.sh | Operational | Active |
   
   ### RAG
   | Document | Authority | Status |
   |----------|-----------|--------|
   | docs/rag/specification.md | Primary | Active |
   | scripts/rag/embedding.py | Runtime | Active |
   
   ### MCP
   | Document | Authority | Status |
   |----------|-----------|--------|
   | docs/mcp/specification.md | Primary | Active |
   | scripts/mcp_servers/*.py | Runtime | Active |
   
   ### Agent
   | Document | Authority | Status |
   |----------|-----------|--------|
   | docs/agent/specification.md | Primary | Active |
   | scripts/agent/*.py | Runtime | Active |
   
   ### EventBus
   | Document | Authority | Status |
   |----------|-----------|--------|
   | docs/eventbus/specification.md | Primary | Active |
   | scripts/eventbus/*.py | Runtime | Active |
   
   ### Shared/DB
   | Document | Authority | Status |
   |----------|-----------|--------|
   | docs/shared/specification.md | Primary | Active |
   | scripts/shared/*.py | Runtime | Active |
   
   ### Governance
   | Document | Authority | Status |
   |----------|-----------|--------|
   | docs/00_governance_01_documentation-governance.md | Primary | Active |
   | docs/00_governance_02_canonical-source-rule.md | Primary | Active |
   ```

### Method

Part B — Add canonical maps to governance document:

```markdown
<!-- BEFORE -->
Each area has its own documentation.

<!-- AFTER -->
See §Area Canonical Maps above for authoritative documents per area.
```

### Details

- Maps follow project convention — clear and actionable.
- Both primary and secondary authorities defined — eliminates ambiguity.
- Status field included — enables tracking of document health.

---

#### Part C: Build area dependency graph

1. Search for existing dependency definitions:
   ```bash
   rg -n "depend.*area\|依存関係\|dependency.*graph" docs/
   ```
2. Define area dependency graph:
   ```markdown
   ## Area Dependency Graph
   
   Permitted dependency directions:
   
   ```mermaid
   graph TD
       Overview --> Deployment
       Overview --> RAG
       Overview --> MCP
       Overview --> Agent
       Overview --> EventBus
       Overview --> Shared/DB
       Overview --> Governance
       
       Deployment --> RAG
       Deployment --> MCP
       Deployment --> Agent
       Deployment --> EventBus
       Deployment --> Shared/DB
       
       RAG --> Agent
       RAG --> EventBus
       
       MCP --> Agent
       MCP --> EventBus
       
       Agent --> EventBus
       Agent --> Shared/DB
       
       EventBus --> Shared/DB
       
       Governance --> Overview
       Governance --> Deployment
       Governance --> RAG
       Governance --> MCP
       Governance --> Agent
       Governance --> EventBus
       Governance --> Shared/DB
   ```
   
   **Cycles prohibited**: No circular dependencies allowed.
   **Direction constraint**: Dependencies only flow downward (Overview → Governance).
   ```

### Method

Part C — Add dependency graph to governance document:

```markdown
<!-- BEFORE -->
Areas can depend on each other freely.

<!-- AFTER -->
See §Area Dependency Graph above for permitted dependency directions.
```

### Details

- Graph follows project convention — clear and actionable.
- Direction constraints defined — prevents circular dependencies.
- Text alternative provided — ensures accessibility.

---

#### Part D: Develop change-impact matrix

1. Search for existing change-impact assessments:
   ```bash
   rg -n "change.*impact\|影響評価\|impact.*matrix" docs/
   ```
2. Define change-impact matrix:
   ```markdown
   ## Change-Impact Matrix
   
   | Change Type | Architecture Impact | Config Impact | Behavior Impact | Doc-Only Impact | Approval Required |
   |-------------|---------------------|---------------|-----------------|-----------------|-------------------|
   | Architecture | High | Medium | High | Low | Yes (RACI) |
   | Config | Low | High | Medium | Low | Yes (Owner) |
   | Behavior | Medium | Low | High | Low | Yes (RACI) |
   | Doc-Only | Low | Low | Low | High | No |
   ```

### Method

Part D — Add change-impact matrix to governance document:

```markdown
<!-- BEFORE -->
Changes require review based on their severity.

<!-- AFTER -->
See §Change-Impact Matrix above for impact assessment criteria.
```

### Details

- Matrix follows project convention — clear and actionable.
- Four change types defined — covers all scenarios.
- Approval requirements specified — ensures accountability.

---

#### Part E: Implement RACI model

1. Search for existing RACI definitions:
   ```bash
   rg -n "RACI\|Responsible\|Accountable\|Consulted\|Informed" docs/
   ```
2. Define RACI model per area:
   ```markdown
   ## RACI Model
   
   ### Overview
   | Role | Responsible | Accountable | Consulted | Informed |
   |------|-------------|-------------|-----------|----------|
   | Architect | @architect | @lead | @dev-team | @stakeholders |
   | Developer | @developer | @architect | @reviewer | @team |
   | Reviewer | @reviewer | @architect | @developer | @team |
   
   ### Deployment
   | Role | Responsible | Accountable | Consulted | Informed |
   |------|-------------|-------------|-----------|----------|
   | DevOps | @devops | @lead | @architect | @team |
   | Developer | @developer | @devops | @reviewer | @team |
   | Reviewer | @reviewer | @devops | @developer | @team |
   
   ### RAG
   | Role | Responsible | Accountable | Consulted | Informed |
   |------|-------------|-------------|-----------|----------|
   | Data Engineer | @data-eng | @lead | @architect | @team |
   | Developer | @developer | @data-eng | @reviewer | @team |
   | Reviewer | @reviewer | @data-eng | @developer | @team |
   
   ### MCP
   | Role | Responsible | Accountable | Consulted | Informed |
   |------|-------------|-------------|-----------|----------|
   | MCP Developer | @mcp-dev | @lead | @architect | @team |
   | Developer | @developer | @mcp-dev | @reviewer | @team |
   | Reviewer | @reviewer | @mcp-dev | @developer | @team |
   
   ### Agent
   | Role | Responsible | Accountable | Consulted | Informed |
   |------|-------------|-------------|-----------|----------|
   | Agent Developer | @agent-dev | @lead | @architect | @team |
   | Developer | @developer | @agent-dev | @reviewer | @team |
   | Reviewer | @reviewer | @agent-dev | @developer | @team |
   
   ### EventBus
   | Role | Responsible | Accountable | Consulted | Informed |
   |------|-------------|-------------|-----------|----------|
   | EventBus Developer | @eventbus-dev | @lead | @architect | @team |
   | Developer | @developer | @eventbus-dev | @reviewer | @team |
   | Reviewer | @reviewer | @eventbus-dev | @developer | @team |
   
   ### Shared/DB
   | Role | Responsible | Accountable | Consulted | Informed |
   |------|-------------|-------------|-----------|----------|
   | DB Admin | @db-admin | @lead | @architect | @team |
   | Developer | @developer | @db-admin | @reviewer | @team |
   | Reviewer | @reviewer | @db-admin | @developer | @team |
   
   ### Governance
   | Role | Responsible | Accountable | Consulted | Informed |
   |------|-------------|-------------|-----------|----------|
   | Governance Lead | @governance-lead | @executive | @all-areas | @team |
   | Reviewer | @reviewer | @governance-lead | @all-areas | @team |
   ```

### Method

Part E — Add RACI model to governance document:

```markdown
<!-- BEFORE -->
Roles are assigned per area as needed.

<!-- AFTER -->
See §RACI Model above for role assignments per area.
```

### Details

- RACI follows project convention — clear and actionable.
- Three roles defined per area — ensures accountability.
- Escalation paths defined — prevents bottlenecks.

---

#### Part F: Define merge conditions

1. Search for existing merge conditions:
   ```bash
   rg -n "merge.*condition\|マージ条件\|merge.*gate" docs/
   ```
2. Define merge conditions:
   ```markdown
   ## Merge Conditions
   
   ### Blocking Conditions (Prevent Merge)
   - Critical open issue exists in affected area
   - RACI approval not obtained from accountable party
   - Canonical source conflict unresolved
   - Test suite failing
   
   ### Non-Blocking Conditions (Allow Merge with Warning)
   - High-severity open issue exists in affected area
   - Documentation outdated but code is correct
   - Config drift detected but no behavioral impact
   
   ### Merge Workflow
   1. Check blocking conditions — if any fail, reject merge.
   2. If non-blocking conditions exist, add warning to PR description.
   3. Obtain RACI approval from accountable party.
   4. Resolve canonical source conflicts before merging.
   5. Verify test suite passes before merging.
   ```

### Method

Part F — Add merge conditions to governance document:

```markdown
<!-- BEFORE -->
Merges are allowed after review.

<!-- AFTER -->
See §Merge Conditions above for merge workflow.
```

### Details

- Conditions follow project convention — clear and actionable.
- Blocking vs non-blocking distinguished — prevents unnecessary delays.
- Workflow defined — ensures consistency.

## Compatibility considerations

- Adding canonical-source precedence does not affect runtime behavior.
- Creating canonical maps does not change code — purely documentation.
- Building dependency graph does not affect code — purely documentation.
- Developing change-impact matrix does not affect code — purely documentation.
- Implementing RACI model does not affect code — purely documentation.
- Defining merge conditions does not affect code — purely documentation.

## Security considerations

- N/A — no new secrets, keys, or sensitive data introduced.
- No changes to authentication, authorization, or data access patterns.

## Rollback considerations

- Revert canonical-source precedence: remove precedence table.
- Revert canonical maps: remove area-specific maps.
- Revert dependency graph: restore original dependency descriptions.
- Revert change-impact matrix: remove matrix.
- Revert RACI model: restore original role assignments.
- Revert merge conditions: restore original merge workflow.
- No schema changes — rollback is purely documentation-level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All modified docs | Manual review: verify no broken cross-references | Visual inspection of each changed document | No broken links, no misleading content |
| All modified docs | Automated: verify no duplicate sections remain | `rg -n "Deprecated Items\|Canonical Source Rule" docs/` — check for remaining raw text vs. links | Only links to canonical docs remain |
| Repo-wide | Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept, 0 broken |
| Generated inventory | Manual verification against active configuration | Visual inspection | Inventory matches config |
| CI pipeline | Stale output detection | Trigger CI build | Warning displayed for stale output |

## Out of scope

- Sign-off gate enforcement (manual step before implementation).
- Deployment steps (Phase 3 of the plan).
- Documentation updates beyond docstring notes and inline comments.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260818-171500_require.md
- Source plan: plans/20260818-191705_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-220059
- Related target files: docs/**/*.md, routing.md, AGENTS.md
