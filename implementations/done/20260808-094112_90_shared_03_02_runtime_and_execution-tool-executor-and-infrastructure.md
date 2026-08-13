## Goal
- Restructure `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` to remove overly detailed constructor signatures, method lists, and function signatures while explicitly preserving why RuntimeToolRegistry is the sole execution routing authority, why ToolRegistry is only drift-validation seed, why cache holds success results only, why side-effect tools need cache/parallelism caution, HealthRegistry dispatch gate purpose, HALF_OPEN experimental recovery concept, OTel tracer private provider rationale, exact-vs-estimated-fallback token counting design intent.

## Scope
- **In-Scope**: `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/runtime chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe "why tool execution infrastructure decisions exist"
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress Section 4 ToolExecutor full constructor signature (lines 27-37): replace with prose describing executor responsibilities (execute tool calls via transport, cache TTL, server configs, concurrency limits, lifecycle protocol injection, discovery map)
- Compress Section 4 execute() sequential processing steps (lines 44-58): replace with prose describing execute behavior at conceptual level (cache lookup, concurrent protection, health gate, transport resolution, per-server semaphore, success-only caching)
- Compress Section 4 helper function list (lines 65-69): replace with prose describing helper purposes (side-effect detection, transport error formatting, hash key generation)
- Compress Section 4a ToolRegistry method list (lines 92-98): replace with prose describing registry responsibilities (register, resolve server for tool, list tool names by server/all, validate config/live matches)
- Compress Section 4a ToolRouteResolver method list (line 118): replace with prose describing resolver responsibility (resolve tool_name → server_key using RuntimeToolRegistry as sole authority)
- Compress Section 4a validation function list (lines 128-133): replace with prose describing validation purposes (config/live routing validation, safety tier checks)
- Compress Section 5 token_counter function signature (lines 150-157): replace with prose describing token counting behavior (exact via API call, fallback to category-based estimation)
- Compress Section 6 otel_tracer function signature (lines 172-177): replace with prose describing tracer building behavior (NoOp when disabled, ConsoleSpanExporter when endpoint empty, OTLP HTTP exporter when endpoint set)
- Compress Section 7 git_helper function signature (lines 188-192): replace with prose describing git info retrieval behavior (returns branch/commit/message/author or None on error)
- Compress Section 8 formatters function list (lines 206-211): replace with prose describing formatter purposes (truncate text, format key-value logs, format sizes, format markdown links)
- Keep: RuntimeToolRegistry as sole execution routing authority, ToolRegistry as drift-validation seed only, cache holds success results only, side-effect tools need cache/parallelism caution, HealthRegistry dispatch gate purpose, HALF_OPEN experimental recovery concept, OTel private provider rationale, exact-vs-estimated-fallback token counting design intent

## Alternatives considered
- Remove Section 4 entirely: rejected — ToolExecutor is central to tool execution architecture
- Replace all tables with prose: rejected — tabular format for type overview is efficient for reference
- Merge Sections 4 and 5 into one: rejected — different conceptual domains (tool execution vs token counting)

## Implementation
### Target file
`docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which tool execution infrastructure design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Compress or remove Section 4 ToolExecutor full constructor signature (lines 27-37)
   - Compress or remove Section 4 execute() sequential processing steps (lines 44-58)
   - Compress or remove Section 4 helper function list (lines 65-69)
   - Compress or remove Section 4a ToolRegistry method list (lines 92-98)
   - Compress or remove Section 4a ToolRouteResolver method list (line 118)
   - Compress or remove Section 4a validation function list (lines 128-133)
   - Compress or remove Section 5 token_counter function signature (lines 150-157)
   - Compress or remove Section 6 otel_tracer function signature (lines 172-177)
   - Compress or remove Section 7 git_helper function signature (lines 188-192)
   - Compress or remove Section 8 formatters function list (lines 206-211)
   - Preserve: Routing authority distinction, cache design intent, side-effect tool caution, HealthRegistry dispatch gate, HALF_OPEN recovery, OTel private provider, exact-vs-estimated-fallback token counting

3. **Phase 3: Deployment & Verification**
   - Confirm routing authority distinction not weakened
   - Confirm cross-references to `scripts/shared/tool_executor.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/shared/tool_registry.py` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
- Section 4 (ToolExecutor): replace constructor/method listings with prose: "ToolExecutor inherits ToolTransportInvoker. Constructor accepts http client, cache_ttl, server_configs, optional cache_max_size/concurrency_limits/lifecycle/discovery_map. apply_config() hot-reloads without instance recreation. execute() resolves tool via transport, caches success results only. clear_cache()/get_error_counters() manage state."
- Section 4a (ToolRegistry): replace method listing with prose: "ToolRegistry registers ToolDefinition objects, resolves server for tool name, lists tool names by server/all, validates config/live tool name matches against registered tools. get_registry() returns global singleton auto-populated from tool_constants on first call."
- Section 4a (ToolRouteResolver): replace method listing with prose: "Resolves tool_name → server_key using RuntimeToolRegistry as sole authority; raises ValueError for unresolved names. server_configs accepted for backward compatibility but unused; discovery_map diagnostic-only; known_tools not passed in production."
- Section 4a (validation functions): replace listing with prose: "validate_routing_against_config/live/check_tool_safety_tiers/check_unknown_tool_safety_tiers return empty dict/list meaning no drift; safety tier checks short-circuit when tool_safety_tiers is empty/unset (opt-in feature)."
- Section 5 (token_counter): replace function signature with prose: "POST {tokenize_url}/tokenize for exact count (is_exact=True); falls back to category-based character-to-token estimation (text: 4.0, tool_calls: 2.5, system: 3.5) returning estimated count (is_exact=False). Connection errors silently fall back."
- Section 6 (otel_tracer): replace function signature with prose: "build_tracer returns NoOp stub when enabled=False; ConsoleSpanExporter when otlp_endpoint empty; OTLP HTTP exporter when endpoint set. Uses private TracerProvider — does not touch global OTel provider."
- Section 7 (git_helper): replace function signature with prose: "get_repo_info returns RepoInfoResult(success, data dict with branch/commit(8-char)/message/author, failure_reason). Returns None on any error. ImportError caught separately; GitPython/GitError/OSError/AttributeError=ValueError individually caught."
- Section 8 (formatters): replace function listing with prose: "truncate(text, max_chars) truncates text; fmt_kvlog(op, **kwargs) formats key=value log string; fmt_size(size) formats human-readable size; fmt_md_link(text, url) formats markdown link; MAX_SNIPPET_CHARS constant for snippet display limit."
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/shared/tool_executor.py`, `scripts/shared/tool_executor_helpers.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/shared/tool_registry.py`, `scripts/shared/route_resolver.py`, `scripts/shared/token_counter.py`, `scripts/shared/otel_tracer.py`, `scripts/shared/git_helper.py`, `scripts/shared/formatters.py` must remain valid after restructuring
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
| Routing Authority Distinction | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/shared/tool_executor.py / scripts/shared/runtime_tool_registry.py / scripts/shared/tool_registry.py |
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
- Source plan: plans/20260807-211051_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-094112
- Related target files: 90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
