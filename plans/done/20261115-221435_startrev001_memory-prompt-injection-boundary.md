## Goal
- Treat persisted memory text as untrusted data at the point where it crosses into a system-role message: build the memory block through one shared helper that neutralizes snippet text and frames the block as recalled data and not instructions, on both injection paths (session start and per turn).

## Priority
Medium

## Scope
- **In-Scope**: one shared block builder and one snippet neutralizer in `snippet_filter.py`; using them in `PromptSetup.setup_prompt` (session start) and `ConversationStateManager.handle_memory_injection` (per turn); tests for both paths and for the helper; documentation of the trust boundary and of the framing.
- **Out-of-Scope**: how memories are extracted, scored, deduplicated, retrieved or stored (`extract.py`, `retriever.py`, `ingestion.py` are not modified); PII redaction and length limits (unchanged, they run before the new step); removing or redesigning the memory feature; making the model immune to instructions in recalled data (the framing is defense in depth, not a hard boundary).
- **Dependencies**: N/A: none

## Background
- Found by an adversarial review of the agent startup path at commit `490fccc50` (Issue `issues/20261115-214901_startrev001_memory-prompt-injection-boundary.md`).
- `PromptSetup.setup_prompt` concatenates a block headed `--- USER MEMORY ---` and one `- {snippet.text}` line per snippet onto the system prompt; `ConversationStateManager.handle_memory_injection` builds the same block and appends it as a `system` message with `_memory_injected` per turn. The two copies of the block-building code are separate (Explicit in code, read in Step 3).
- The only transformations between storage and the system role are PII redaction and truncation in `MemoryInjectionService._build_snippets` (`filter_pii`, `truncate_snippet`). The documented trust boundary lists exactly these (`docs/91_security/security_01_architecture-and-trust-boundaries.md`, the "Agent → LLM" row), and the existing `tests/agent/memory/test_memory_injection_security.py` characterizes only PII filtering and truncation (Step 2).
- Exploitability, resolved in Step 2 (the Issue left it as an Unresolved Question). `extract_memories` stores assistant and user messages whose text matches imperative keywords (`always`, `never`, `must`, `rule`, `policy`, `should`, and others); a semantic memory starts at a base importance of 0.4 with a keyword and length bonus, and `top_semantic` selects `importance >= min_importance` (default 0.3) ordered by importance, so any such text is eligible and instruction-like language ranks highest (Explicit in code, `extract.py` and `retriever.py`). The injected text is the entry's summary, the first line or its first characters, falling back to the first 100 characters of the content, which can span lines. Whether attacker-controlled text reaches an assistant message in practice (for example a summary of a fetched page) was not observed; the mechanism that promotes it is confirmed.
- Existing tests assert the exact header line (`--- USER MEMORY ---` in `tests/agent/test_startup.py` and `tests/agent/test_startup_prompt_setup.py`); the header must stay as is.
- Related, already closed and not overlapping: `issues/done/20261012-124838_start004_startup-prompt-setup-swallows-all-memory-injection-errors-as-a-generic-disabled-flag.md` (error classification only).

## Problem
The system role carries the highest instruction authority. Memory text enters it unmarked, and instruction-like text is exactly what the extraction heuristic promotes. Recalled text is indistinguishable from operator-authored system content once injected, and a memory whose text spans lines or imitates the header can shape the block. Persistence makes one poisoned turn affect every later session until the memory is pruned.

## Reason for Change
A persistent prompt-injection channel survives across sessions. Nothing makes this urgent: exploitability depends on attacker-controlled text reaching an assistant or user message, so the change is a hardening step. It also fixes a duplication, because the block is built in two places that would otherwise drift apart, as the degraded-live check did.

## Implementation Intent
Treat memory snippets as untrusted data at the single point where they enter the system role. `snippet_filter.py` gains two functions and no new class: a neutralizer that turns a snippet into one line of text (line breaks and control characters become single spaces, text that imitates the block header is defused) without otherwise changing ordinary wording, and a block builder that returns the block string: the unchanged header line, one framing line saying the entries are recalled notes to be treated as data and not as instructions, then one bullet per neutralized snippet. Both injection paths call the builder, so the two blocks stay identical. PII redaction, truncation, counts, ordering and the `_memory_injected` marker are untouched. The framing is defense in depth; the residual risk is recorded.

## Requirements
- `REQ-001`: A snippet neutralizer in `snippet_filter.py` returns single-line text without control characters, defuses text that imitates the block header, and leaves ordinary snippets word-for-word unchanged.
- `REQ-002`: A block builder in `snippet_filter.py` returns the block with the unchanged header line, a framing line that marks the content as recalled data and not instructions, and one bullet per neutralized snippet; an empty snippet list yields no block.
- `REQ-003`: `PromptSetup.setup_prompt` builds the session-start block through the builder; the snippet count limit, order, PII redaction, truncation and the failure handling are unchanged.
- `REQ-004`: `ConversationStateManager.handle_memory_injection` builds the per-turn block through the same builder; the message role, the `_memory_injected` marker, the source and the degraded-state handling are unchanged.
- `REQ-005`: Tests cover the neutralizer, the builder and both injection paths, including header forgery, multi-line text, role-style instructions inside the block, and unchanged output for ordinary snippets.
- `REQ-006`: The trust-boundary documentation states that memory content is untrusted data, how it is framed and neutralized, and the residual risk.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/memory/snippet_filter.py | Own the neutralizer and the block builder | Add a snippet neutralizer function and a block builder function (functions only, no new class, so the generated reference table is unaffected); keep `filter_pii` and `truncate_snippet` as they are | REQ-001, REQ-002; AC-1, AC-2 | The module holds `PII_PATTERNS`, `FilteredSnippet`, `TruncatedSnippet`, `filter_pii` (line 46) and `truncate_snippet` (line 63); 2559 bytes (checked in Step 3) | `tests/agent/memory/test_memory_injection_security.py` | Verified |
| scripts/agent/startup_prompt_setup.py | Use the builder at session start | Replace the inline block construction in `setup_prompt` (the `memory_block` assignment at line 74) with the builder call; keep the snippet cap, the warning, the failure handling and the two leading blank lines that `setup_prompt` places before the block (the builder returns the block without them) | REQ-003; AC-3 | `setup_prompt` builds `"\n\n--- USER MEMORY ---\n" + "\n".join(f"- {snippet.text}" ...)` after the cap; radon B (10) (checked in Step 3 and Step 5) | `tests/agent/test_startup_prompt_setup.py` | Verified |
| scripts/agent/conversation_state_manager.py | Use the builder per turn | Replace the inline block construction in `handle_memory_injection` (line 130) with the builder call; keep the `system` role, `_memory_injected`, `source="memory_injection"` and the degraded-state handling | REQ-004; AC-4 | `handle_memory_injection` builds `"--- USER MEMORY ---\n" + "\n".join(f"- {snippet.text}" ...)` and appends it as a `system` message; radon B (9) (checked in Step 3 and Step 5) | `tests/agent/test_memory_injection_recovery.py` | Verified |
| tests/agent/memory/test_memory_injection_security.py | Helper tests | Add classes for the neutralizer and the builder: header lookalike, line breaks and control characters, role-style text, ordinary text unchanged, empty list, header and framing line present once | REQ-001, REQ-002, REQ-005; AC-1, AC-2, AC-5 | The file characterizes PII filtering and truncation only (classes `TestSensitiveDataFiltering` and the truncation tests, lines 18-156) (checked in Step 2 and Step 3) | tests/agent/memory/test_memory_injection_security.py | Verified |
| tests/agent/test_startup_prompt_setup.py | Session-start path tests | Add tests: the system prompt block uses the framing line and neutralized text for a snippet with line breaks and a header lookalike; the existing header assertions keep passing | REQ-003, REQ-005; AC-3, AC-5 | The file asserts `"--- USER MEMORY ---" in ctx.conv.system_prompt_content` (lines 133, 166) (checked in Step 3) | tests/agent/test_startup_prompt_setup.py | Verified |
| tests/agent/test_memory_injection_recovery.py | Per-turn path tests | Add tests: the per-turn `system` message block uses the same framing and neutralized text; the role, marker and source are unchanged | REQ-004, REQ-005; AC-4, AC-5 | The file drives `ConversationStateManager.handle_memory_injection("hello")` (lines 58, 62) (checked in Step 3) | tests/agent/test_memory_injection_recovery.py | Verified |
| docs/91_security/security_01_architecture-and-trust-boundaries.md | State the trust boundary | In the "Agent → LLM" row (line 174), say that memory snippets are untrusted data, framed as recalled notes and neutralized in addition to PII redaction and length limiting, and note the residual risk | REQ-006; AC-6 | Line 174 lists memory snippets as "PII-redacted and length-limited by `snippet_filter.py`" and nothing else (checked in Step 2 and Step 3) | N/A: documentation | Verified |
| docs/23_agent/agent_11_01_memory-overview-and-modes.md | State the injection rule | Near lines 46-47 (injection at session start), add that recalled memory is injected as data under a fixed framing line on both paths, never as instructions | REQ-006; AC-6 | Lines 46-47 describe the importance threshold and pinned entries for session-start injection without the framing (checked in Step 3) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/memory/injection.py | `MemoryInjectionService._build_snippets` runs PII filtering and truncation before the new step and produces `MemorySnippet.text` | REQ-001, REQ-002 |
| scripts/agent/memory/extract.py | The keyword scoring that promotes instruction-like text; documents why the neutralizer exists | REQ-001 |
| scripts/agent/memory/models.py | `MemorySnippet` carries the formatted text the builder receives | REQ-002 |
| scripts/agent/context.py | `append_message` and `TRUSTED_SOURCES` handle the `_memory_injected` marker; unchanged | REQ-004 |
| tests/agent/test_startup.py | Asserts the exact header line after startup; must keep passing | REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-001): The neutralizer returns a single line without control characters; text imitating the header is defused (it no longer equals the header line); a typical snippet such as `[Semantic memory] Use uv for all commands` is returned unchanged.
- AC-2 (REQ-002): The builder returns the unchanged header line, one framing line, and one bullet per snippet; with no snippets it returns an empty result and no block is added.
- AC-3 (REQ-003): The session-start prompt contains the block from the builder; the snippet cap, order, PII redaction, truncation and failure handling are unchanged; the existing header assertions pass.
- AC-4 (REQ-004): The per-turn message is a `system` message built by the builder with `_memory_injected` and `source="memory_injection"` unchanged.
- AC-5 (REQ-005): `uv run pytest tests/agent/memory/test_memory_injection_security.py tests/agent/test_startup_prompt_setup.py tests/agent/test_memory_injection_recovery.py tests/agent/test_startup.py tests/agent/test_orchestrator.py` passes with the new cases, and the forgery and multi-line tests fail against the pre-change code.
- AC-6 (REQ-006): Both documents state the untrusted-data rule and the residual risk; `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py` pass.
- AC-7 (REQ-001 to REQ-004): `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass; `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check` pass.

## Tests
- REQ-001: helper tests over: a snippet that contains the header text, one with embedded line breaks and tabs, one with control characters, one ordinary snippet, an empty snippet.
- REQ-002: builder tests: exact header line and framing line once each, bullet per snippet, no block for an empty list.
- REQ-003: a `setup_prompt` test with a fake memory service returning a hostile snippet; assert the framed block and unchanged cap behavior.
- REQ-004: a `handle_memory_injection` test with a fake memory service; assert the appended message's role, marker, source and framed block.
- REQ-005: write the forgery and multi-line tests first and confirm they fail on the current code.
- REQ-006: documentation checks listed under AC-6.

## Documentation Impact
`docs/91_security/security_01_architecture-and-trust-boundaries.md` (the "Agent → LLM" row) and `docs/23_agent/agent_11_01_memory-overview-and-modes.md` must be updated (REQ-006). Describe the trust boundary and the framing as policy, with the residual risk; no marker texts beyond the existing header name, no limits, no file lists (`skills/DESIGN.md` Docs content policy). The generated reference `docs/23_agent/agent_11_04_memory-module-reference-generated.md` lists classes of `snippet_filter.py`; no class is added, so it needs no change.

## Assumptions
- Normalizing line breaks and control characters is safe for ordinary snippets because injected snippets are bullet lines built from a summary (the first line or about a hundred characters) or the first 100 characters of content; falsifiable by the unchanged-wording test on a typical snippet.
- Keeping the header line exactly as is keeps the existing tests and any consumer that looks for it valid; the framing is a separate line below it.
- The framing line reduces but does not remove the chance that a model follows instructions in recalled text; the residual risk is accepted and documented, and the extraction heuristic is deliberately left alone.
- Overlap judgment (Step 8b): `tools/check_plan_target_overlaps.py` reports no finding that names this Plan; none of its eight target files is a target of another Frozen Plan at the time of freezing.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether attacker-controlled text (tool output, fetched content) reaches an assistant or user message and is then memorized in normal use | An observed end-to-end case; the promoting mechanism is confirmed (Step 2) but the entry path was not exercised | Implementation phase: add the hostile-snippet tests; operationally review the memory store for instruction-like entries after deployment | False |
| UNK-02 | The exact wording of the framing line and of the header-defusing rule | A decision of wording only; no behavior depends on it beyond the unchanged header | Decide at implementation time, keep the header line unchanged | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/memory/snippet_filter.py | Modify | Low: two new functions; existing functions unchanged; imported by `injection.py` and the tests | 0 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| scripts/agent/startup_prompt_setup.py | Modify | Medium: every session start with memory enabled builds its system prompt here | 1 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| scripts/agent/conversation_state_manager.py | Modify | Medium: every turn with memory enabled passes through `handle_memory_injection` | 5 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| tests/agent/memory/test_memory_injection_security.py | Modify | Low: tests only | 0 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| tests/agent/test_startup_prompt_setup.py | Modify | Low: tests only | 0 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| tests/agent/test_memory_injection_recovery.py | Modify | Low: tests only | 1 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| docs/91_security/security_01_architecture-and-trust-boundaries.md | Modify | Low: one table row of one design document | 8 | High: one author | not applicable (rsynced): `docs/` is not deployed |
| docs/23_agent/agent_11_01_memory-overview-and-modes.md | Modify | Low: one passage of one design document | 2 | High: one author | not applicable (rsynced): `docs/` is not deployed |

## Design
- **Design decision (scope of the boundary)**: options weighed. (1) Sanitize only at session start, as the Issue assumed: rejected, the per-turn path builds the same block with the same header and role, so the same text would be injected unchecked one turn later. (2) Filter at extraction or storage time: rejected, it would change what is remembered and cannot protect entries already stored. (3) One shared builder applied where text enters the system role, on both paths: chosen. Compatibility impact: the block gains one framing line and snippet text is normalized to one line; the header line and every limit are unchanged.
- **Design decision (what the neutralizer does)**: it removes what lets a snippet change the block's structure (line breaks, control characters, a copy of the header) and does not rewrite ordinary wording; it does not try to detect instructions, because instruction-like language is also the legitimate content of rule memories.
- **Block prefix and builder input (added in the plan-to-implementation-procedure cycle, Step 3a)**: the two inline builders differ today: `setup_prompt` places two blank lines before the header (it appends the block to the system prompt), `handle_memory_injection` starts the message with the header. The builder therefore returns the block starting at the header line and `setup_prompt` keeps prepending its own separator; the per-turn message content stays byte-identical to the header-first form. The builder takes the snippet texts (a sequence of strings), not `MemorySnippet` objects, so `snippet_filter.py` keeps importing only the standard library.
- **Residual risk**: the model may still follow an instruction written as plain text inside a bullet; the framing line lowers that likelihood but is not a boundary. Recorded in the documentation and in Risks.
- **Architecture analysis**: `lint-imports` reports 6 contracts kept, 0 broken at this commit; `snippet_filter.py` imports only the standard library; both callers already live in `agent`; no cross-layer import is added (checked in Step 5).
- **Dependency graph**: `snippet_filter` is imported by `injection.py` and the tests; the block-building code is duplicated in `startup_prompt_setup.py` and `conversation_state_manager.py` (checked in Step 3).
- **Historical analysis**: `conversation_state_manager.py` 5 commits, `startup_prompt_setup.py` 1, `test_memory_injection_recovery.py` 1, `security_01` 8 and `agent_11_01` 2 in the last 30 days; one contributor (two spellings of one name) in the last 90 days (checked in Step 5).
- **Operational dependency inspection**: no port, database or service is touched; the memory store content is not changed (checked in Step 5).
- **Validation quality baseline**: radon: `setup_prompt` B (10) and `handle_memory_injection` B (9); the change removes inline construction from both, so no increase is expected; vulture and bandit: no finding in the target files; diff-cover baseline: the working tree equals `master`, so the diff has no coverage lines (no current number); baseline test run 12261 passed, 2 failed, 7 skipped, the two failures being the pre-existing posture tests `tests/mcp_servers/test_posture_gate_start_path.py::test_running_the_mdq_entry_module_goes_through_real_run_http` and `tests/mcp_servers/mdq/test_mdq_health_posture.py::TestBindGate::test_validated_posture_does_not_block_bind`, unrelated to this Plan; the Plan must raise diff coverage to the `rules/toolchain.md` threshold.

## Implementation steps
1. **Phase 1: Shared helper**
   - [ ] Write the neutralizer and builder tests first and confirm the forgery and multi-line cases fail on the current code (REQ-001, REQ-002, REQ-005; tests/agent/memory/test_memory_injection_security.py)
   - [ ] Add the neutralizer and the builder to the filter module as functions (REQ-001, REQ-002; scripts/agent/memory/snippet_filter.py)
2. **Phase 2: Session-start path**
   - [ ] Add the hostile-snippet `setup_prompt` test (REQ-003, REQ-005; tests/agent/test_startup_prompt_setup.py)
   - [ ] Build the block through the builder in `setup_prompt` (REQ-003; scripts/agent/startup_prompt_setup.py)
3. **Phase 3: Per-turn path**
   - [ ] Add the `handle_memory_injection` test (REQ-004, REQ-005; tests/agent/test_memory_injection_recovery.py)
   - [ ] Build the block through the builder in `handle_memory_injection` (REQ-004; scripts/agent/conversation_state_manager.py)
4. **Phase 4: Documentation**
   - [ ] State the untrusted-data rule, the framing and the residual risk (REQ-006; docs/91_security/security_01_architecture-and-trust-boundaries.md, docs/23_agent/agent_11_01_memory-overview-and-modes.md)
5. **Phase 5: Deployment & verification**
   - [ ] Run the validation plan; hand off to `skills/deploy/SKILL.md` only after the change is committed and pushed, and deploying is the user's decision (REQ-001 to REQ-004; scripts/agent/memory/snippet_filter.py, scripts/agent/startup_prompt_setup.py, scripts/agent/conversation_state_manager.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/memory/snippet_filter.py | Unit | `uv run pytest tests/agent/memory/test_memory_injection_security.py tests/agent/memory/test_snippet_filter.py -q` | New helper cases pass; existing PII and truncation tests pass |
| scripts/agent/startup_prompt_setup.py | Unit | `uv run pytest tests/agent/test_startup_prompt_setup.py tests/agent/test_startup.py tests/agent/test_startup_memory_failures.py -q` | Framed block present; header assertions and failure-handling tests pass |
| scripts/agent/conversation_state_manager.py | Unit | `uv run pytest tests/agent/test_memory_injection_recovery.py tests/agent/test_orchestrator.py -q` | Per-turn block framed; role, marker and source unchanged |
| Changed Python files | Static | `uv run ruff check scripts/ && uv run mypy --no-namespace-packages scripts/ && PYTHONPATH=scripts uv run lint-imports` | No findings; 6 contracts kept |
| Module size and reference table | Static | `uv run python tools/check_module_size.py && uv run python tools/generate_reference_table.py --check` | No module over its limit; no drift |
| Documentation | Documentation | `uv run python tools/check_docs_quality.py && uv run python tools/check_docs_content_policy.py` | No findings |
| Diff coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At or above the threshold in `rules/toolchain.md` |

## Risks
- **Risk**: The model still follows an instruction embedded in a recalled bullet (likelihood unknown) → **Mitigation**: the framing line and structural neutralization lower it; the residual risk is documented and the extraction heuristic is a candidate for a separate issue.
- **Risk**: Normalizing text changes how legitimate multi-line memories read (likelihood low; injected text is already a summary or a 100-character prefix) → **Mitigation**: the unchanged-wording test on typical snippets; only line breaks and control characters change.
- **Risk**: A consumer matches the old block text (likelihood low) → **Mitigation**: the header line is unchanged and the repository search found only the two builders and the tests that assert the header.
- **Risk**: Changing both paths at once enlarges the diff (likelihood low) → **Mitigation**: the phases are independently revertable and each path has its own tests.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Shared helper and its tests (scripts/agent/memory/snippet_filter.py, tests/agent/memory/test_memory_injection_security.py) | Completed | — | 20261116-222000 |  |
| 2 | Session-start path (scripts/agent/startup_prompt_setup.py, tests/agent/test_startup_prompt_setup.py) | Completed | — | 20261116-224500 |  |
| 3 | Per-turn path (scripts/agent/conversation_state_manager.py, tests/agent/test_memory_injection_recovery.py) | Completed | — | — |  |
| 4 | Documentation (docs/91_security/security_01_architecture-and-trust-boundaries.md, docs/23_agent/agent_11_01_memory-overview-and-modes.md) | Completed | — | — |  |
| 5 | Deployment and verification (scripts/agent/memory/snippet_filter.py, scripts/agent/startup_prompt_setup.py, scripts/agent/conversation_state_manager.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261116-095914_01_scripts_agent_memory_snippet_filter.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261116-095914_02_scripts_agent_startup_prompt_setup.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261116-095914_03_scripts_agent_conversation_state_manager.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261116-095914_07_docs_91_security_security_01_architecture-and-trust-boundaries.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261116-095914_08_docs_23_agent_agent_11_01_memory-overview-and-modes.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261115-214901_startrev001_memory-prompt-injection-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-221435
- **Related target files**: scripts/agent/memory/snippet_filter.py, scripts/agent/startup_prompt_setup.py, scripts/agent/conversation_state_manager.py, tests/agent/memory/test_memory_injection_security.py, tests/agent/test_startup_prompt_setup.py, tests/agent/test_memory_injection_recovery.py, docs/91_security/security_01_architecture-and-trust-boundaries.md, docs/23_agent/agent_11_01_memory-overview-and-modes.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (1); `extract.py` keyword scoring and `top_semantic` (Step 2) | scripts/agent/memory/snippet_filter.py | Phase 1 | AC-1 | neutralizer tests | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (2); Implementation Intent (delimit and frame the block) | scripts/agent/memory/snippet_filter.py | Phase 1 | AC-2 | builder tests | Derived from confirmed evidence |
| REQ-003 | Issue Required Changes (2); `setup_prompt` block construction | scripts/agent/startup_prompt_setup.py | Phase 2 | AC-3 | hostile-snippet `setup_prompt` test | Confirmed by repository evidence |
| REQ-004 | Issue Unresolved Questions (per-turn path); `handle_memory_injection` builds the same block | scripts/agent/conversation_state_manager.py | Phase 3 | AC-4 | `handle_memory_injection` test | Derived from confirmed evidence |
| REQ-001 | Issue Required Changes (4); Testing Expectations | tests/agent/memory/test_memory_injection_security.py | Phase 1 | AC-1, AC-5 | `uv run pytest tests/agent/memory/test_memory_injection_security.py -q` | Explicit in issue |
| REQ-002 | Issue Acceptance Criteria (1), (2) | tests/agent/memory/test_memory_injection_security.py | Phase 1 | AC-2, AC-5 | builder tests | Explicit in issue |
| REQ-005 | Issue Testing Expectations | tests/agent/memory/test_memory_injection_security.py | Phase 1 | AC-5 | forgery tests fail on the pre-change code | Explicit in issue |
| REQ-003 | Issue Acceptance Criteria (3) | tests/agent/test_startup_prompt_setup.py | Phase 2 | AC-3, AC-5 | `uv run pytest tests/agent/test_startup_prompt_setup.py -q` | Explicit in issue |
| REQ-005 | Issue Testing Expectations | tests/agent/test_startup_prompt_setup.py | Phase 2 | AC-5 | new tests fail on the pre-change code | Explicit in issue |
| REQ-004 | Issue Out of Scope (the per-turn path beyond reusing the same helper) | tests/agent/test_memory_injection_recovery.py | Phase 3 | AC-4, AC-5 | `uv run pytest tests/agent/test_memory_injection_recovery.py -q` | Derived from confirmed evidence |
| REQ-005 | Issue Testing Expectations | tests/agent/test_memory_injection_recovery.py | Phase 3 | AC-5 | new tests fail on the pre-change code | Explicit in issue |
| REQ-006 | Issue Documentation Impact; the "Agent → LLM" row of the trust-boundary table (Step 2) | docs/91_security/security_01_architecture-and-trust-boundaries.md | Phase 4 | AC-6 | `check_docs_quality`, `check_docs_content_policy` | Confirmed by repository evidence |
| REQ-006 | Issue Documentation Impact; injection passage near lines 46-47 | docs/23_agent/agent_11_01_memory-overview-and-modes.md | Phase 4 | AC-6 | `check_docs_quality`, `check_docs_content_policy` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261116-095914 -->