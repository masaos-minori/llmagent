## Goal

Standardize evidence labeling, uncertainty tracking, and area known issues across the project by establishing a unified framework for managing technical debt, verifying documentation, and tracking project uncertainties.

## Scope

**In-Scope:**
- Align evidence labels to the 7-category taxonomy defined in `00_governance_03_evidence-labels.md`; add minimal evidence blocks (label, source reference, notes) consistent with existing practice.
- Implement a process to scan area documents for uncertainty markers (e.g., "Needs Confirmation", "要確認"); extract these into a central inventory per `00_governance_07_needs-confirmation-inventory.md`, linking each finding back to its source statement.
- Migrate all area-specific "Known Issues" (Agent, MCP, RAG, EventBus, Shared/DB) to a single, common template; ensure they include mandatory metadata: ID, Title, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Current Description, Observed Implementation, Impact, Recommended Action, and Resolution Notes.
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

## Alternatives considered

- Keep evidence labels per-area — rejected because it causes inconsistency and makes cross-area auditing difficult.
- Leave uncertainty markers in place — rejected because it creates noise and makes tracking impossible.
- Delete known issues after resolution — rejected because it loses valuable historical context.

## Implementation

### Procedure

#### Part A: Align evidence labeling with existing governance

1. Verify current evidence label usage against `00_governance_03_evidence-labels.md`:
    ```bash
    rg -n "EVIDENCE\|evidence.*label\|evidence.*block" docs/
    ```
2. Ensure all evidence labels conform to the 7-category taxonomy defined in `00_governance_03_evidence-labels.md`:
    - Explicit in code
    - Strongly implied by code
    - Documentation only
    - Needs confirmation
    - Deprecated
    - Verified by test
    - Operationally observed

### Method

Part A — Add evidence label to a claim:

```markdown
<!-- BEFORE -->
The system supports 10 concurrent connections.

<!-- AFTER -->
The system supports 10 concurrent connections.
- **Evidence**: Operationally observed
- **Source**: `config/system.toml`
- **Notes**: max_connections=10
```

### Details

- Evidence label uses one of the 7 categories from `00_governance_03_evidence-labels.md`.
- Source field points to the verifiable artifact.
- Notes field provides additional context.

---

#### Part B: Scan for uncertainty markers

1. Search for uncertainty markers:
    ```bash
    rg -n "Needs Confirmation\|要確認\|uncertain\|TODO.*confirm" docs/
    ```
2. For each found item, extract into central inventory per `00_governance_07_needs-confirmation-inventory.md`:
    ```markdown
    ## Needs Confirmation Inventory
    
    ### NC-{NNN} Question text
    - **Source File**: `docs/area/file.md`
    - **Section**: Section name
    - **Line Number**: ~line number
    - **Question**: What needs to be confirmed
    - **Evidence**: What evidence exists for the current statement
    - **Impact**: Consequences if the statement is wrong
    - **Required Action**: What needs to happen to resolve this item
    - **Resolution**: Resolution details or "—" if unresolved
    - **Status**: open / investigating / resolved / deferred / wontfix
    - **Assigned To**: Unassigned / [Name]
    - **Last Reviewed**: YYYY-MM-DD
    - **Priority**: High / Medium / Low
    - **Related NC**: NC-XXX (if applicable)
    - **Resolution Target**: YYYY-MM-DD or milestone
    - **Blocking**: Yes / No
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
2. For each area, migrate to common template per `00_governance_04_known-issues-template.md`:
    ```markdown
    ## Known Issue Template
    
    ### {AREA}-{NNN} Title
    - **ID**: {AREA}-{NNN}
    - **Title**: Brief description of the issue
    - **Status**: open / investigating / fixed / deferred / deprecated / wontfix
    - **Severity**: High / Medium / Low
    - **Area**: Agent / MCP / RAG / EventBus / Shared/DB / Governance / Overview / Deployment
    - **Type**: document-code-mismatch / document-document-mismatch / obsolete-description / missing-documentation / ambiguous-behavior / implementation-bug / design-gap / operational-gap
    - **Owner**: Unassigned / [Name] / Team
    - **First Found**: YYYY-MM-DD
    - **Source**: `docs/area/knowledge.md:42`
    - **Target**: `scripts/area/module.py`
    - **Related**: N/A or related issue ID
    - **Summary**: Concise summary of the issue
    - **Current Description**: How the issue currently manifests
    - **Observed Implementation**: What the actual implementation shows
    - **Impact**: Consequences of the issue remaining unresolved
    - **Recommended Action**: Suggested resolution approach
    - **Resolution Notes**: History of resolution attempts
    ```

### Method

Part C — Migrate known issue:

```markdown
<!-- BEFORE: Agent area -->
## Known Issues
- Model loading fails when path contains spaces.

<!-- AFTER: Common template -->
### AGENT-001 Model loading fails with space-containing paths
- **ID**: AGENT-001
- **Title**: Model loading fails with space-containing paths
- **Status**: open
- **Severity**: High
- **Area**: Agent
- **Type**: implementation-bug
- **Owner**: Unassigned
- **First Found**: 2026-08-18
- **Source**: `docs/agent/knowledge.md:15`
- **Target**: `scripts/agent/model_loader.py`
- **Related**: N/A
- **Summary**: Model loader crashes on paths containing spaces
- **Current Description**: Model loading fails when path contains spaces
- **Observed Implementation**: Path is passed without escaping to subprocess
- **Impact**: Users cannot use models in directories with spaces
- **Recommended Action**: Escape paths correctly in model loader
- **Resolution Notes**: —
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
2. For each table entry, create individual issue entry per `00_governance_04_known-issues-template.md`:
    ```markdown
    ### EVENTBUS-{NNN} Title
    - **ID**: EVENTBUS-{NNN}
    - **Title**: Brief description of the issue
    - **Status**: open / investigating / fixed / deferred / deprecated / wontfix
    - **Severity**: High / Medium / Low
    - **Area**: EventBus
    - **Type**: document-code-mismatch / document-document-mismatch / obsolete-description / missing-documentation / ambiguous-behavior / implementation-bug / design-gap / operational-gap
    - **Owner**: Unassigned / [Name] / Team
    - **First Found**: YYYY-MM-DD
    - **Source**: `docs/eventbus/specification.md:42`
    - **Target**: `scripts/eventbus/publisher.py`
    - **Related**: N/A or related issue ID
    - **Summary**: Concise summary of the issue
    - **Current Description**: How the issue currently manifests
    - **Observed Implementation**: What the actual implementation shows
    - **Impact**: Consequences of the issue remaining unresolved
    - **Recommended Action**: Suggested resolution approach
    - **Resolution Notes**: History of resolution attempts
    ```

### Method

Part D — Convert table row to issue entry:

```markdown
<!-- BEFORE: Table row -->
| EventBus | Delivery undefined | Medium | Open |

<!-- AFTER: Individual issue -->
### EVENTBUS-001 Delivery semantics undefined
- **ID**: EVENTBUS-001
- **Title**: Delivery semantics undefined
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Owner**: Unassigned
- **First Found**: 2026-08-18
- **Source**: `docs/eventbus/specification.md:42`
- **Target**: `scripts/eventbus/publisher.py`
- **Related**: N/A
- **Summary**: EventBus delivery guarantees not specified
- **Current Description**: Delivery semantics undefined
- **Observed Implementation**: No documentation of at-least-once delivery guarantee
- **Impact**: Consumers cannot rely on delivery semantics
- **Recommended Action**: Define at-least-once delivery guarantee
- **Resolution Notes**: —
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
2. For each design decision, add status field per `00_governance_04_known-issues-template.md`:
    ```markdown
    ## Design Decision Template
    
    ### {AREA}-{NNN} Title
    - **ID**: {AREA}-{NNN}
    - **Title**: Brief description of the decision
    - **Status**: confirmed / proposed / rejected
    - **Severity**: N/A (informational)
    - **Area**: Governance / Overview
    - **Type**: design-gap
    - **Owner**: Unassigned / [Name] / Team
    - **First Found**: YYYY-MM-DD
    - **Source**: `docs/governance/design-decision.md:42`
    - **Target**: `scripts/governance/module.py`
    - **Related**: N/A or related issue ID
    - **Summary**: Concise summary of the decision
    - **Current Description**: How the decision was made
    - **Observed Implementation**: What the actual implementation shows
    - **Impact**: Consequences of the decision
    - **Recommended Action**: Suggested resolution approach
    - **Resolution Notes**: History of resolution attempts
    ```

### Method

Part E — Add status to existing design decision:

```markdown
<!-- BEFORE -->
## Use SQLite for persistence
We chose SQLite for its simplicity and zero-config deployment.

<!-- AFTER -->
### GOVERNANCE-001 Use SQLite for persistence
- **ID**: GOVERNANCE-001
- **Title**: Use SQLite for persistence
- **Status**: confirmed
- **Severity**: N/A
- **Area**: Governance
- **Type**: design-gap
- **Owner**: Unassigned
- **First Found**: 2026-08-18
- **Source**: `docs/governance/design-decision.md:42`
- **Target**: `scripts/governance/module.py`
- **Related**: N/A
- **Summary**: SQLite chosen for persistence layer
- **Current Description**: We chose SQLite for its simplicity and zero-config deployment
- **Observed Implementation**: SQLite is used in production
- **Impact**: Zero-config deployment enables simpler operations
- **Recommended Action**: Maintain current approach
- **Resolution Notes**: —
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
- Source issue: N/A
- Source requirement: N/A
- Source plan: N/A
- Source implementation procedure: N/A
- Generated at: 20260818-215020
- Related target files: docs/**/*.md, routing.md, AGENTS.md
