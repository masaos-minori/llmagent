## Goal

Rebuild the shared/caching/retry/helper chapter by compressing or removing implementation details such as LlmRetryHandler signatures and method lists while explicitly preserving: retry limited to transient failures design decision, ToolResultCache currently unused by ToolExecutor note, caching duplication/disorganization flagged as known issue item, ToolSpec as DAG scheduling metadata, HealthRegistry circuit-breaker-like meaning, hot-reloadable LLM config can be changed at runtime.

## Scope

**In-Scope**: `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md` structure change only.

**Out-of-Scope**: Other shared/db related chapters (`docs/90_shared_*.md`), source code changes, tests.

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be maintained as the authoritative reference for caching/retry/helper design.
- This chapter focuses on design intent, not implementation details.
- Existing internal links and cross-references must remain valid after editing.

## Design decisions

- Compress full method lists into high-level capability categories.
- Replace exhaustive enum/state tables with "state machine exists" references.
- Retain explicit known-issue flags for caching duplication/disorganization.

## Alternatives considered

- Full removal of all method details: rejected because responsibility boundaries become unclear without any concrete anchors.
- Keeping full method lists: rejected because they drift from reality as methods evolve and add noise to the overview.

## Implementation

### Target file

`docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md`

### Procedure

1. Read current chapter content.
2. Identify McpServerHealthRegistry complete method list and replace with high-level capability categories (failure tracking, degraded tracking, success recovery).
3. Compress/remove McpServerHealthState complete enum table — replace with "states: HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN/UNKNOWN".
4. Compress/remove state transition table — replace with "transition rules exist per circuit-breaker pattern".
5. Compress/remove LlmPayloadHandler complete method list — replace with "payload construction and response parsing capabilities".
6. Compress/remove LlmHotConfigHandler complete method list and HOT_CONFIG_FIELDS table — replace with "hot-reloadable config management via apply_config()".
7. Compress/remove AI reference guide table — replace with high-level FAQ categories.
8. Verify preservation of: retry limited to transient failures design decision, ToolResultCache currently unused by ToolExecutor note, caching duplication/disorganization as known issue flag, ToolSpec as DAG scheduling metadata, HealthRegistry circuit-breaker-like meaning, hot-reloadable LLM config can be changed at runtime.
9. Validate all internal Markdown links and cross-references.
10. Confirm compliance with `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.

### Method

Document compression via selective deletion of exhaustive method lists, enum tables, and state transition tables while retaining structural responsibility declarations that point to source modules.

### Details

- **Preserve**: retry limited to transient failures design decision, ToolResultCache currently unused by ToolExecutor note (explicitly documented), caching duplication/disorganization as known issue flag (must be preserved per five-way classification), ToolSpec as DAG scheduling metadata, HealthRegistry circuit-breaker-like meaning (HEALTHY→DEGRADED→UNAVAILABLE→HALF_OPEN→HEALTHY/UNAVAILABLE transitions), hot-reloadable LLM config can be changed at runtime (apply_config() keyword-only args with None-skip partial update semantics).
- **Compress/remove**: McpServerHealthRegistry complete method list → replace with "methods track failure counts, degraded reasons, success recovery"; McpServerHealthState complete enum table → replace with "states: HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN/UNKNOWN"; state transition table → replace with "transitions follow circuit-breaker pattern with half-open probe window"; LlmPayloadHandler complete method list → replace with "static methods: build_payload(), parse_response(), parse_non_stream_response()"; LlmHotConfigHandler complete method list and HOT_CONFIG_FIELDS table → replace with "HOT_CONFIG_FIELDS maps instance attribute names to kwarg names for 9 fields; apply_config() accepts keyword-only args with None-skip semantics"; AI reference guide table → replace with "FAQ categories: config loading, ownership, cache usage, token counting, retry behavior, health gate states".
- **Verify**: cross-references to scripts/shared/ caching/retry/helper infrastructure modules exist; caching duplication note preserved as known issue item; internal Markdown links valid; template compliance.

## Compatibility considerations

N/A — document-only phase.

## Security considerations

N/A — document-only phase.

## Rollback considerations

N/A — document-only phase.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Retry Limited To Transient Failures Decision | Manual | Explicitly preserved |
| Tool Result Cache Currently Unused By Tool Executor Note | Manual | Explicitly preserved |
| Caching Duplication Disorganization As Known Issue | Manual | Explicitly preserved |
| Tool Spec Is Dag Scheduling Metadata | Manual | Explicitly preserved |
| Health Registry Circuit Breaker Like Meaning | Manual | Explicitly preserved |
| Hot Reloadable Llm Config Can Be Changed At Runtime | Manual | Explicitly preserved |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope

Other shared/db related chapters, source code changes, tests.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-233734_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-131643
- Related target files: 90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md
