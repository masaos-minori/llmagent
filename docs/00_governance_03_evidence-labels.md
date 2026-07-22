## Purpose

This document defines evidence labels used throughout the design documentation set to indicate the strength of implementation grounding and confirmation status for each statement. These labels help readers assess confidence levels and identify areas needing verification.

## Evidence Labels

The following seven labels define the spectrum of implementation grounding:

### 1. Explicit in code

Statement is directly observable in source code.

- **Usage condition:** Code line or function call directly matches the description.
- **Example:** "The CLI command `/reload` reads config/agent.toml" — verifiable by reading the reload handler.
- **Caution:** Ensure the observed code is not dead code or legacy.

### 2. Strongly implied by code

Statement is inferred from code structure/patterns.

- **Usage condition:** Multiple related code elements consistently support the description.
- **Example:** "WorkflowEngine processes tasks sequentially" — inferred from the task queue implementation.
- **Caution:** Inference may be incorrect; verify periodically.

### 3. Documentation only

Statement exists only in documentation without code verification.

- **Usage condition:** No direct code reference found; rely on documented intent.
- **Example:** "The system supports hot-reload of configuration" — stated but not yet verified against code.
- **Caution:** May be outdated; treat as lower confidence.

### 4. Needs confirmation

Statement's accuracy is unverified against implementation.

- **Usage condition:** Description exists but has not been verified against current code.
- **Example:** A claim about MCP tool behavior that has not been traced through the codebase.
- **Caution:** Must have required fields; cannot remain indefinitely in this state.

### 5. Deprecated

Statement describes an obsolete feature no longer in use.

- **Usage condition:** Feature was removed or replaced; description remains for historical context.
- **Example:** "The old diagnostics.jsonl file stores session diagnostics" — no longer written.
- **Caution:** Clearly distinguish from current specifications.

### 6. Verified by test

Statement is confirmed through automated tests.

- **Usage condition:** Test coverage exists and passes for the described behavior.
- **Example:** "The memory layer correctly persists state across turns" — confirmed by test assertions.
- **Caution:** Tests may become stale; re-verify when tests change.

### 7. Operationally observed

Statement is based on runtime behavior observations.

- **Usage condition:** Observed in production/staging environment logs or metrics.
- **Example:** "MCP tool invocation latency averages 50ms" — derived from operational metrics.
- **Caution:** Observations may be environment-specific.

## Needs Confirmation Required Fields

When using "Needs confirmation", include all six required fields:

- **Question:** What specifically needs to be verified?
- **Evidence:** What evidence supports the need for confirmation?
- **Impact:** What is the consequence if this is wrong?
- **Required Action:** What action resolves the uncertainty?
- **Target Document:** Where should the result be recorded?
- **Review Timing:** When should this be reviewed?

## Handling Ambiguous Cases

When uncertain which label applies:

- Default to the lower-confidence label (e.g., "Documentation only" over "Strongly implied").
- Record the ambiguity in the label's Notes field.
- Flag for periodic review rather than immediate correction.

## Non-Goals

- Defining how to implement evidence labeling in tooling
- Specifying label transition workflows between states
- Requiring all statements to carry an evidence label

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
- [Needs Confirmation Inventory](00_governance_07_needs-confirmation-inventory.md)
