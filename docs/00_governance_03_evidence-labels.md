---
title: "Evidence Labels"
category: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---
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

## Standard Evidence Block

When documenting implementation evidence, use the following standardized block format to ensure consistency and traceability across all documentation.

### Fields
- **Evidence label** — One of the seven labels defined above
- **Source module or document** — File path or document title where the claim originates
- **Symbol or section** — Specific function, class, section, or line number referenced
- **Test identifier** — Test file/method that verifies the claim (if applicable)
- **Verification date** — Date when the evidence was last confirmed
- **Notes** — Additional context, caveats, or related references

---

### Explicit in code
**Example:**
- **Evidence label**: Explicit in code
- **Source module or document**: `scripts/agent/config_builders.py`
- **Symbol or section**: `build_agent_config()` function, lines 478-497
- **Test identifier**: `tests/agent/test_config_builders.py::TestBuildAgentConfig::test_returns_agent_config_instance`
- **Verification date**: 2026-08-19
- **Notes**: Directly observable in source code; reload path reuses same builder

---

### Strongly implied by code
**Example:**
- **Evidence label**: Strongly implied by code
- **Source module or document**: `scripts/agent/workflow/workflow_engine.py`
- **Symbol or section**: `WorkflowEngine.process_tasks()` method
- **Test identifier**: `tests/agent/test_workflow_engine.py::TestWorkflowEngine::test_sequential_execution`
- **Verification date**: 2026-08-19
- **Notes**: Inferred from task queue implementation and sequential processing pattern

---

### Documentation only
**Example:**
- **Evidence label**: Documentation only
- **Source module or document**: `docs/05_agent_08_04_configuration-mcp-approval-obs.md`
- **Symbol or section**: §診断設定, `retention_days` parameter
- **Test identifier**: N/A
- **Verification date**: 2026-08-19
- **Notes**: Stated in docs but not verified against current code; treat as lower confidence

---

### Needs confirmation
**Example:**
- **Evidence label**: Needs confirmation
- **Source module or document**: `docs/04_mcp_04_05_git.md`
- **Symbol or section**: Line 89, protected-branch/force-push limits question
- **Test identifier**: N/A
- **Verification date**: 2026-08-19
- **Notes**: Whether absence of extra guards beyond `is_write` for git_checkout/git_pull/git_push is intentional. Registered as NC-018 in needs-confirmation inventory.

---

### Deprecated
**Example:**
- **Evidence label**: Deprecated
- **Source module or document**: `scripts/rag/models_audit.py`
- **Symbol or section**: `AuditLogRecord` / `ApprovalDecision` classes (removed)
- **Test identifier**: N/A
- **Verification date**: 2026-07-29
- **Notes**: Confirmed zero production callers via full-repo grep; classes removed. See NC-005 resolution.

---

### Verified by test
**Example:**
- **Evidence label**: Verified by test
- **Source module or document**: `scripts/agent/memory/jsonl_store.py`
- **Symbol or section**: `JsonlMemoryStore.read_all()` method
- **Test identifier**: `tests/agent/memory/test_jsonl_store.py::TestJsonlMemoryStore::test_read_all_returns_all_entries`
- **Verification date**: 2026-08-19
- **Notes**: Test coverage exists and passes for the described behavior

---

### Operationally observed
**Example:**
- **Evidence label**: Operationally observed
- **Source module or document**: `scripts/agent/diagnostic_store.py`
- **Symbol or section**: `DiagnosticStore.save(encrypt=True)` path
- **Test identifier**: `tests/agent/test_diagnostic_store.py::TestEncryption::test_save_encrypt_true_with_configured_key`
- **Verification date**: 2026-08-19
- **Notes**: Derived from operational metrics and test verification of encryption round-trip
