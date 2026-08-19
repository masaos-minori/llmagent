## Goal

Standardize evidence labeling, uncertainty tracking, and area known issues across the project by establishing a unified framework for managing technical debt, verifying documentation, and tracking project uncertainties.

## Scope

**In-Scope:**
- Define the smallest verifiable unit as an "individual claim"; implement a standard evidence block including label, source module/document, symbol/section, test identifier, verification date, and notes; prefer stable symbols/test references over line numbers.
- Implement a process to scan area documents for uncertainty markers (e.g., "Needs Confirmation", "要確認"); extract these into a central inventory, linking each finding back to its source statement.
- Migrate all area-specific "Known Issues" (Agent, MCP, RAG, EventBus, Shared/DB) to a single, common template; ensure they include mandatory metadata: status, severity, type, owner, source, target, evidence, impact, and resolution criteria.
- Clearly distinguish confirmed design decisions from active technical defects during migration.
- Convert any tabular EventBus issue entries into individual, tracked issue entries.

**Out-of-Scope:**
- Changes to existing MCP server implementations unless required by the unified policy.
- Changes to deployment infrastructure beyond what's needed for security enforcement.
- Changes to other systems' integration points (only internal security architecture).

## Assumptions

- The project already has some governance documents (e.g., `00_governance_03_evidence-labels.md`, `00_governance_07_needs-confirmation-inventory.md`, `00_governance_04_known-issues-template.md`) but they're inconsistently applied (verify current implementation against each claim).
- Evidence blocks need to be standardized across all documentation (check current evidence block usage).
- Uncertainty markers need to be extracted into a central inventory (check current uncertainty marker usage).
- Known issues need to follow a common template (check current known issues format).

## Design decisions

- Create a single evidence label taxonomy — eliminates ambiguity and makes auditing possible.
- Extract uncertainty markers into a central inventory — prevents scattered "Needs Confirmation" items.
- Use a common template for all known issues — enables consistent reporting and prioritization.
- Prefer stable identifiers (symbols, test refs) over line numbers — survives code changes.

## Alternatives considered

- Keep evidence labels per-area — rejected because it causes inconsistency and makes cross-area auditing difficult.
- Leave uncertainty markers in place — rejected because it creates noise and makes tracking impossible.
- Delete known issues after resolution — rejected because it loses valuable historical context.

## Implementation

### Procedure

#### Part A: Standardize evidence labeling

1. Search for current evidence labels:
   ```bash
   rg -n "EVIDENCE\|evidence.*label\|evidence.*block" docs/
   ```
2. Define a unified evidence label taxonomy:
   ```markdown
   ## Evidence Label Taxonomy
   
   | Label | Description | Example |
   |-------|-------------|---------|
   | EVID-001 | Test passing | `pytest::test_agent_integration` |
   | EVID-002 | Code review | `PR#123` |
   | EVID-003 | Documentation reference | `docs/architecture.md` |
   | EVID-004 | Runtime observation | `log.info("loaded model")` |
   | EVID-005 | Configuration value | `config.toml::model_path` |
   ```

### Method

Part A — Add evidence label to a claim:

```markdown
<!-- BEFORE -->
The system supports 10 concurrent connections.

<!-- AFTER -->
The system supports 10 concurrent connections.
- **Evidence**: EVID-005 — `config/system.toml::max_connections=10`
- **Source**: `config/system.toml`
- **Symbol**: `MAX_CONNECTIONS`
- **Verified**: 2026-08-18
```

### Details

- Evidence block follows project convention — clear and actionable.
- Stable identifiers used instead of line numbers — survives code changes.

---

#### Part B: Scan for uncertainty markers

1. Search for uncertainty markers:
   ```bash
   rg -n "Needs Confirmation\|要確認\|uncertain\|TODO.*confirm" docs/ plans/
   ```
2. For each found item, extract into central inventory:
   ```markdown
   ## Needs Confirmation Inventory
   
   | ID | Statement | Source | Status | Resolution Date |
   |----|-----------|--------|--------|-----------------|
   | NC-001 | "The system should support 100 connections" | `docs/architecture.md:42` | Resolved | 2026-08-18 |
   | NC-002 | "Model dimension is 384" | `plans/20260818-181905_plan.md:15` | Active | — |
   ```

### Method

Part B — Extract uncertainty marker:

```python
#!/usr/bin/env python3
"""Extract uncertainty markers from documents."""

import re
from pathlib import Path

UNCERTAINTY_PATTERNS = [
    r"Needs Confirmation",
    r"要確認",
    r"uncertain",
    r"TODO.*confirm",
]

def find_uncertainty_markers(directory: str) -> list[tuple[str, int, str]]:
    """Find all uncertainty markers in a directory."""
    results = []
    for doc_path in Path(directory).rglob("*.md"):
        content = doc_path.read_text()
        for pattern in UNCERTAINTY_PATTERNS:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                results.append((str(doc_path), line_num, match.group()))
    return results

if __name__ == "__main__":
    markers = find_uncertainty_markers(".")
    for path, line, text in markers:
        print(f"{path}:{line}: {text}")
```

### Details

- Script scans all Markdown files in the repository.
- Output format matches project convention — machine-readable and human-readable.
- No behavioral changes — purely observability.

---

#### Part C: Migrate known issues to common template

1. Search for area-specific known issues:
   ```bash
   rg -n "Known Issues\|既知の問題\|KNOWN_ISSUES" docs/
   ```
2. For each area, migrate to common template:
   ```markdown
   ## Known Issue Template
   
   ### [KISSUE-001] Title
   - **Status**: Open / In Progress / Resolved / Deferred
   - **Severity**: Critical / High / Medium / Low
   - **Type**: Bug / Feature Gap / Technical Debt / Security
   - **Owner**: @username
   - **Source**: `docs/area/knowledge.md:42`
   - **Target**: `scripts/area/module.py`
   - **Evidence**: EVID-001 — `pytest::test_area_bug`
   - **Impact**: Brief description of business impact
   - **Resolution Criteria**: Steps to resolve
   ```

### Method

Part C — Migrate known issue:

```markdown
<!-- BEFORE: Agent area -->
## Known Issues
- Model loading fails when path contains spaces.

<!-- AFTER: Common template -->
### [KISSUE-001] Model loading fails with space-containing paths
- **Status**: Open
- **Severity**: High
- **Type**: Bug
- **Owner**: @agent-team
- **Source**: `docs/agent/knowledge.md:15`
- **Target**: `scripts/agent/model_loader.py`
- **Evidence**: EVID-004 — `log.error("failed to load model")`
- **Impact**: Users cannot use models in directories with spaces
- **Resolution Criteria**: Escape paths correctly in model loader
```

### Details

- Migration preserves full history — enables future audits.
- Common template ensures consistency across areas.
- Mandatory metadata fields enforced — no missing information.

---

#### Part D: Convert tabular EventBus issues to individual entries

1. Search for tabular EventBus issues:
   ```bash
   rg -n "EventBus.*issue\|eventbus.*bug" docs/
   ```
2. For each table entry, create individual issue entry:
   ```markdown
   ### [KISSUE-002] EventBus delivery guarantee undefined
   - **Status**: Open
   - **Severity**: Medium
   - **Type**: Feature Gap
   - **Owner**: @eventbus-team
   - **Source**: `docs/eventbus/specification.md:42`
   - **Target**: `scripts/eventbus/publisher.py`
   - **Evidence**: EVID-003 — `docs/eventbus/specification.md`
   - **Impact**: Consumers cannot rely on delivery semantics
   - **Resolution Criteria**: Define at-least-once delivery guarantee
   ```

### Method

Part D — Convert table row to issue entry:

```markdown
<!-- BEFORE: Table row -->
| EventBus | Delivery undefined | Medium | Open |

<!-- AFTER: Individual issue -->
### [KISSUE-003] EventBus delivery undefined
- **Status**: Open
- **Severity**: Medium
- **Type**: Feature Gap
- **Owner**: @eventbus-team
- **Source**: `docs/eventbus/specification.md:42`
- **Target**: `scripts/eventbus/publisher.py`
- **Evidence**: EVID-003 — `docs/eventbus/specification.md`
- **Impact**: Consumers cannot rely on delivery semantics
- **Resolution Criteria**: Define at-least-once delivery guarantee
```

### Details

- Conversion preserves full history — enables future audits.
- Individual entries are easier to track than table rows.
- Mandatory metadata fields enforced — no missing information.

---

#### Part E: Distinguish confirmed design decisions from active defects

1. Search for design decisions:
   ```bash
   rg -n "design decision\|Design Decision\|ADR" docs/
   ```
2. For each design decision, add status field:
   ```markdown
   ## Design Decision Template
   
   ### [ADR-001] Use SQLite for persistence
   - **Status**: Confirmed / Proposed / Rejected
   - **Date**: 2026-08-18
   - **Author**: @author
   - **Rationale**: Brief explanation
   - **Alternatives Considered**: List alternatives
   ```

### Method

Part E — Add status to existing design decision:

```markdown
<!-- BEFORE -->
## Use SQLite for persistence
We chose SQLite for its simplicity and zero-config deployment.

<!-- AFTER -->
## [ADR-001] Use SQLite for persistence
- **Status**: Confirmed
- **Date**: 2026-08-18
- **Author**: @author
- **Rationale**: Simplicity and zero-config deployment
- **Alternatives Considered**: PostgreSQL, Redis
```

### Details

- Status field added — distinguishes confirmed vs. proposed decisions.
- Rationale preserved — provides context for future reviewers.
- Alternatives listed — shows trade-offs were considered.

## Compatibility considerations

- Adding evidence labels does not affect runtime behavior.
- Extracting uncertainty markers does not change documentation content — only adds metadata.
- Migrating known issues does not affect code — purely documentation.
- Converting tabular issues to individual entries does not affect code — purely documentation.
- Adding status to design decisions does not affect code — purely documentation.

## Security considerations

- N/A — no new secrets, keys, or sensitive data introduced.
- No changes to authentication, authorization, or data access patterns.

## Rollback considerations

- Revert evidence labels: remove evidence blocks from documents.
- Revert uncertainty extraction: delete central inventory.
- Revert known issue migration: restore original area-specific formats.
- Revert tabular conversion: restore original tables.
- Revert design decision status: remove status fields.
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
- Source issue: issues/20260818_08_issue.md
- Source requirement: requires/20260818-172100_require.md
- Source plan: plans/20260818-185139_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-215020
- Related target files: docs/**/*.md, routing.md, AGENTS.md
