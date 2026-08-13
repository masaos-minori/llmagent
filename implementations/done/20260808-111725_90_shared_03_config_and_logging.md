# Implementation Procedure: Shared — Runtime Config and Logging Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed method signatures, configuration file tables, and other implementation specifics while preserving critical operational guidance on why ConfigLoader enforces process isolation, why there is no shared configuration file, why production strengthens strict/security validation, that each process reads only its own config file, boundary enforcement mechanism via restrict_to(), agent's load_all() reads only agent.toml, decision not to create shared config files, RAG config validation vs production config validation responsibility split, Logger's operational role, structured logging + contextvars concurrent task log interleaving prevention rationale, and stderr fallback policy on log write failure.

## Scope

**In-Scope:**
- `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` — compress ConfigLoader full method signatures, configuration file enumeration tables, per-process restrict_to() caller site tables, configuration loading flow pseudocode, ConfigValidationResult dataclass definitions, Logger full method lists, complete list of log format fields; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for config separation and logging decisions
- Configuration ownership separation is an intentional cross-process boundary judgment and must NOT be lost
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full signatures, configuration tables, and verbose processing explanations but keep references to where they live (`scripts/shared/config_loader.py`, `scripts/shared/logger.py`, etc.)
- **Preserve ConfigLoader design intent**: Keep explicit note of ConfigLoader's design intent
- **Preserve process isolation policy**: Keep explicit statement of process isolation policy
- **Preserve each process reads only own config file rule**: Keep explicit note of rule that each process reads only its own config file
- **Preserve restrict_to() boundary enforcement mechanism**: Keep explicit note of boundary enforcement via restrict_to()
- **Preserve agent's load_all() reads only agent.toml**: Keep explicit note of agent's load_all() reading only agent.toml
- **Preserve decision not to create shared config files**: Keep explicit note of decision not to create shared config files
- **Preserve RAG config validation vs production config validation responsibility split**: Keep explicit note of responsibility split between RAG and production config validation
- **Preserve production strengthens strict/security validation**: Keep explicit note of why production strengthens strict/security validation
- **Preserve Logger operational role**: Keep explicit note of Logger's operational role
- **Preserve structured logging + contextvars concurrent task log interleaving prevention**: Keep explicit note of rationale for preventing log interleaving
- **Preserve stderr fallback policy on log write failure**: Keep explicit note of stderr fallback policy

## Alternatives Considered

1. **Full deletion of method signatures** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` | Compress ConfigLoader methods, config file tables, restrict_to() callers, loading flow pseudocode, ConfigValidationResult dataclass, Logger methods, log format fields; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (ConfigLoader design intent, process isolation policy, each process reads only own config file rule, restrict_to() boundary enforcement, agent's load_all() reads only agent.toml, decision not to create shared config files, RAG config validation vs production config validation responsibility split, production strengthens strict/security validation, Logger operational role, structured logging + contextvars concurrent task log interleaving prevention, stderr fallback policy on log write failure)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `ConfigLoader`, `restrict_to()`, `Logger`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/shared/config_loader.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_03_01_runtime_and_execution-config-and-logging.md`**
- ConfigLoader full method signatures: Replace with prose summary referencing `scripts/shared/config_loader.py`
- Configuration file enumeration tables: Replace with prose summary
- Per-process restrict_to() caller site tables: Replace with prose summary
- Configuration loading flow pseudocode: Replace with prose summary
- ConfigValidationResult dataclass definitions: Replace with prose summary
- Logger full method lists: Replace with prose summary referencing `scripts/shared/logger.py`
- Complete list of log format fields: Replace with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/shared/config_loader.py` and `scripts/shared/logger.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about process isolation policy and restrict_to() boundary enforcement
- Known issue note about caching duplication must be preserved
- Process isolation policy must be verified as clear
- restrict_to() boundary enforcement rationale must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| Process isolation policy preserved | Manual | Explicitly stated |
| restrict_to() boundary enforcement preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/shared/config_loader.py` / `logger.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full method signatures/configuration tables remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-215824_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_03_01_runtime_and_execution-config-and-logging.md
