## Goal
- Restructure `docs/90_shared_01_03_overview-constraints-and-reference.md` to remove overly detailed constraint value tables and AI reference guide question tables while explicitly preserving import direction constraints, import-linter enforcement, persistent DB overview, cross-cutting constraints (JSON/orjson, httpx, English-only logs, SQLite WAL), and SecurityProfile/ProductionConfigValidator operational semantics.

## Scope
- **In-Scope**: `docs/90_shared_01_03_overview-constraints-and-reference.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe import direction constraints
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress Section 9 constraint value table into prose — individual values like `embedding_dims default=384`, `_` prefix exclusion rule are implementation details that can be deferred to config docs
- Compress Section 11 AI reference guide question table into a brief prose list — the 5-row mapping is redundant with section headers already present in each target doc
- Keep Section 7 import direction constraints as-is (design boundary critical)
- Keep Section 8 persistent DB overview table but compress column-level detail to just DB filenames and purposes
- Keep cross-cutting constraints (orjson bytes return, httpx.AsyncClient, English-only logs, WAL mode) as concise prose bullets

## Alternatives considered
- Remove Section 9 entirely: rejected — SecurityProfile/ProductionConfigValidator operational semantics are needed for deployment configuration validation understanding
- Replace Section 11 with auto-generated TOC: not yet decided — manual list is simpler and avoids dependency on tooling
- Merge Section 8 into Section 10 summary: rejected — table format provides quick lookup that prose does not

## Implementation
### Target file
`docs/90_shared_01_03_overview-constraints-and-reference.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which constraint design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Compress or remove Section 9 overly detailed constraint value table (embedding_dims default=384, `_` prefix exclusion rule, etc.)
   - Compress or remove Section 11 AI reference guide question table (5-row question/reference mapping)
   - Compress or remove Section 8 mechanical DB table enumeration (per-DB-file table listing)
   - Compress or remove Sections 12-13 duplicate Related Documents/Keywords sections
   - Preserve: import direction constraints, import-linter enforcement, persistent DB overview, cross-cutting constraints (JSON/orjson, httpx, English-only logs, SQLite WAL), SecurityProfile/ProductionConfigValidator operational semantics

3. **Phase 3: Deployment & Verification**
   - Confirm import direction constraints are not weakened
   - Confirm cross-references to `scripts/shared/` and `scripts/db/` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Prose compression: convert tables to bullet lists where the tabular format adds no semantic value beyond what prose conveys
- Table reduction: keep only DB filename + purpose columns in Section 8, drop per-table row enumeration
- Section consolidation: merge Related Documents and Keywords into existing section headers

### Details
- Section 7 (import direction): keep as-is — design boundary critical
- Section 8 (persistent DB overview): reduce from 3-column table (DB file | tables | purpose) to 2-column table (DB file | purpose). Per-table row enumeration is implementation detail
- Section 9 (constraints): replace table with prose bullets. Keep: import direction, JSON library choice (orjson), HTTP client (httpx.AsyncClient), log language (English only), WAL mode. Remove: embedding_dims value, `_` prefix rule, agent.toml ownership reference (deferred to config doc), SecurityProfile enum values (deferred to security doc)
- Section 10 (summary): keep as-is — high-level synthesis
- Section 11 (AI reference): replace question table with brief prose list pointing to relevant chapters by name
- Remove Sections 12-13 (Related Documents, Keywords) — content duplicated in frontmatter and section headers

## Compatibility considerations
- Cross-references to `scripts/shared/` and `scripts/db/` must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` directory
- No change to source code contracts — document-only modification

## Security considerations
- Import direction constraints must survive cleanup unchanged (no-auth premise, network-boundary-protection judgment)
- SecurityProfile/ProductionConfigValidator operational meaning must be preserved (deployment-time validation gate)
- ProductionConfigValidator's strict key/tool_safety_tiers/allowed_tools validation behavior must remain documented

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files (`scripts/shared/` / `scripts/db/`) for verification

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Import Direction Constraints | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/shared/ / scripts/db/ |
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
- Source plan: plans/20260807-210733_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-092413
- Related target files: 90_shared_01_03_overview-constraints-and-reference.md
