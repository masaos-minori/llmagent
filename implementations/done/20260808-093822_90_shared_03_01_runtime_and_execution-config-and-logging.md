## Goal
- Restructure `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` to remove overly detailed method signatures, configuration file tables, and pseudo-code while explicitly preserving why ConfigLoader has process-isolation policy, why each process reads only its own config file, how restrict_to() enforces boundaries, RAG vs production config validation responsibility split, why production strengthens strict/security validation, Logger's operational role, structured logging + contextvars concurrent task log cross-prevention rationale, and stderr fallback on write failure.

## Scope
- **In-Scope**: `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/runtime chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe "why config/log design decisions exist"
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress Section 2 ConfigLoader full method signature listing (lines 33-41): replace with prose describing loader responsibilities (load files, merge dicts, exclude `_` keys, raise typed errors)
- Compress Section 2a process separation table (lines 82-98): replace with prose describing ownership rule (each process reads its own config only; no shared config files; DB paths/URLs duplicated per-process)
- Compress Section 2a config loading flow pseudo-code (lines 103-119): replace with prose describing load/load_all/restrict_to behavior at conceptual level
- Compress Section 2b ConfigValidationResult dataclass definition (lines 125-136, 141-155): replace with prose describing validation result structure (errors/warnings lists, ok property)
- Keep: process isolation policy, restrict_to() boundary enforcement, agent loads agent.toml only decision, shared config file creation avoidance, RAG vs production validation responsibility split, production strengthens strict/security validation, Logger operational role, structured logging + contextvars concurrent task log cross-prevention, stderr fallback on write failure

## Alternatives considered
- Remove Section 2 entirely: rejected — ConfigLoader is central to config isolation architecture
- Replace all tables with prose: rejected — tabular format for type overview is efficient for reference
- Merge Sections 2 and 2b into one: rejected — different conceptual domains (loader vs validator)

## Implementation
### Target file
`docs/90_shared_03_01_runtime_and_execution-config-and-logging.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which config/log design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Compress or remove Section 2 ConfigLoader full method signature listing (lines 33-41)
   - Compress or remove Section 2a process separation table (lines 82-98)
   - Compress or remove Section 2a config loading flow pseudo-code (lines 103-119)
   - Compress or remove Section 2b ConfigValidationResult dataclass definition (lines 125-136, 141-155)
   - Preserve: process isolation policy, restrict_to() boundary enforcement, agent loads agent.toml only decision, shared config file creation avoidance, RAG vs production validation responsibility split, production strengthens strict/security validation, Logger operational role, structured logging + contextvars concurrent task log cross-prevention, stderr fallback on write failure

3. **Phase 3: Deployment & Verification**
   - Confirm process isolation/config isolation policies not weakened
   - Confirm cross-references to `scripts/shared/config_loader.py` and `scripts/shared/logger.py` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
- Section 2 (ConfigLoader): replace method listings with prose: "ConfigLoader loads TOML/JSON files sequentially, merges via dict.update (shallow only), excludes `_`-prefixed keys, raises ConfigMissingError/ConfigParseError/ConfigReadError subclasses of ValueError". Drop detailed load/load_all/restrict_to descriptions
- Section 2a (process separation table): replace with prose: "Each process reads its own config file only. No shared config files — DB paths and external service URLs are duplicated per-process. MCPServer subclasses declare own_config_file class variable; run_http() calls restrict_to() before uvicorn startup. Crawler/ingester/chunk_splitter call restrict_to() in main guard. EventBus uses custom loader."
- Section 2a (config loading flow): remove pseudo-code block entirely — behavioral description suffices
- Section 2b (ConfigValidationResult): replace dataclass listings with prose: "Both validators return ConfigValidationResult(errors, warnings) with ok property. RagConfigValidator checks rag section cross-file consistency (embedding_dim/vec_dim mismatch, use_rrf=False, cache thresholds). ProductionConfigValidator adds security_profile-aware validation: local/development degrades violations to warnings with [local/development] prefix; production elevates them to errors. Checks required_strict_keys, tool safety tier bidirectional diff, allowed_tools empty-list warning. known_tools defaults to registry lookup."
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/shared/config_loader.py`, `scripts/shared/config_validator.py`, `scripts/shared/production_config_validator.py`, `scripts/shared/logger.py` must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` directory
- No change to source code contracts — document-only modification

## Security considerations
- N/A — document-only modification, no security-sensitive content affected

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files for verification

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Process Isolation Policy | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/shared/config_loader.py / scripts/shared/logger.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Source code changes
- Test modifications
- Cross-chapter structural changes beyond this single file
- Auto-generation of documentation (future work)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-210946_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-093822
- Related target files: 90_shared_03_01_runtime_and_execution-config-and-logging.md
