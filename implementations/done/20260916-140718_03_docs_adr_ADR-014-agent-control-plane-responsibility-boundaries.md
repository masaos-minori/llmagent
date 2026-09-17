## Goal

Resolve ADR-014's Known Deviations entry regarding the three-layer retry ownership gap — update the Known Deviations section to reflect that the gap is now documented rather than unresolved.

## Scope

- Update ADR-014's Known Deviations section (L198-L203) to mark the retry ownership gap as resolved by the documentation changes in the previous two procedure documents.
- The specific target is the second bullet point about `ToolLoopGuard.check_retry()` and `WorkflowEngine.retry_policy` relationship being undocumented.

## Assumptions

- The Known Deviations section currently exists at L198-L203 in the ADR.
- The second bullet point at L201 discusses the retry ownership gap.

## Design decisions

- Mark the Known Deviation as resolved in-place — do not create a new section or move the bullet.
- Update the text to indicate the gap is now documented in the three-layer retry landscape.

## Alternatives considered

- Creating a new "Resolved Deviations" section — rejected because the Plan's intent is to resolve the Known Deviation directly in its current location.

## Implementation
### Target file

`docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`

### Procedure

1. Locate the Known Deviations section (L198-L203).
2. Update the second bullet point (L201) to reflect that the retry ownership gap is now documented.

### Method

Current Known Deviations content:
```markdown
## Known Deviations

- `Orchestrator.__init__`（`scripts/agent/orchestrator.py`）が使用されない`LLMTurnRunner`インスタンスを`self._llm_runner`として生成しており、実際のLLM/Tool Call往復ループは`LlmTurnExecutor`（`scripts/agent/llm_turn_executor.py`）が内部で独自に生成する別インスタンスによって処理されている。これはINV-024（`LLMTurnRunner`生成の一元化）に対する現状の逸脱であり、修正issue（`issues/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md`）で追跡する。
- 「Workflow Engineが再試行を担う」という本ADRの定義自体はINV-023に反しないが、`ToolLoopGuard.check_retry()`（`scripts/agent/tool_loop_guard.py`）とLLM transport層（`llm_max_retries`等、`config/agent.toml`）にも別個の"retry"概念が存在し、WorkflowEngineの`retry_policy`との関係が未文書化。粒度が異なるため直ちにINV-023違反とは判定しないが、整理不足はドキュメント化issue（`issues/20260914-123659_arch03_retry_ownership_documentation_and_layering.md`）で追跡する。

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。
```

Required update for the second bullet (replace L201):
```markdown
- 「Workflow Engineが再試行を担う」という本ADRの定義自体はINV-023に反しないが、`ToolLoopGuard.check_retry()`（`scripts/agent/tool_loop_guard.py`）とLLM transport層（`llm_max_retries`等、`config/agent.toml`）にも別個の"retry"概念が存在し、WorkflowEngineの`retry_policy`との関係が未文書化。粒度が異なるため直ちにINV-023違反とは判定しないが、整理不足はドキュメント化issue（`issues/20260914-123659_arch03_retry_ownership_documentation_and_layering.md`）で追跡する。→ **RESOLVED**: 三層のリトライ範囲の説明は `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` に追加済み（REQ-002）。
```

### Details

The update should be made inline — append "→ **RESOLVED**: ..." to the end of the existing bullet point. Do not remove the original text; only add the resolution marker.

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The reference to REQ-002 links back to the three-layer retry landscape document.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If the resolution is found to be premature, simply revert the addition. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-014-*.md` | Documentation quality | `uv run python tools/check_docs_quality.py docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md` | Clean |
| `docs/adr/ADR-014-*.md` | Documentation structure | `uv run python tools/check_docs_structure.py docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md` | Clean |

## Completion criteria

- ADR-014's Known Deviations section explicitly marks the retry ownership gap as RESOLVED.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md` passes clean.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md` passes clean.

## Out of scope

- Adding a clarifying docstring note to `tool_loop_guard.py` — handled in the next procedure document (REQ-004).
- Changing any of the three retry mechanisms' behavior — this is documentation-only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-123659_arch03_retry_ownership_documentation_and_layering.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140718
- **Related target files**: docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md
