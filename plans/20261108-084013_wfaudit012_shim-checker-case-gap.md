## Goal
Make the compatibility-leftover checker case-insensitive where the repository's own source uses capitalized forms, so phrases like the adapter's "Backward-compatible alias" block are caught by CI instead of silently passing — without flooding the docs scan with legitimate history prose.

## Priority
Medium

## Scope
- **In-Scope**:
  - `tools/check_compat_shims.py` — apply `re.IGNORECASE` to the `COMPAT_PATTERNS` search (`check_content` loop at L630-633), or case-fold `stripped` before matching (one chosen mechanism); verify the whole repository passes after the change.
  - Follow-through findings: any newly flagged active-source lines are fixed or exempted by the checker's existing historical-context convention — the `workflow_engine_adapter.py` alias block is expected to be flagged, and `wfaudit008`'s plan deletes it (landing order below).
  - Tests: `tests/tools/` checker tests with capitalized-vs-lowercase fixture pairs.
- **Out-of-Scope**:
  - Adding new patterns (the pattern vocabulary is unchanged; only matching semantics).
  - The `_REMOVED_NAME_PATTERNS` path — already case-insensitive with the `_HISTORICAL_CONTEXT_MARKERS` exemption (L345-347, L494); unchanged.
  - Docs history prose: legitimate capitalized "Backward" historical notes stay allowed via the existing exemption mechanism — the change must not require mass doc rewording.
- **Dependencies**: After `wfaudit008` (its alias block, the main live source of capitalized leftovers, is deleted there; making the checker strict afterwards protects a clean tree). If 012 lands first, its Phase 1 must exempt or fix the adapter lines that 008 will delete — 008-first avoids editing code twice.

## Background
Live verification at HEAD (issue `## Adversarial Validation`): `COMPAT_PATTERNS` matches run through `re.search(pattern, stripped)` with no flags (`tools/check_compat_shims.py:630-633`); the pattern `"backward-compatible keyword": r"backward-compatible"` (L95) does not match the capitalized "Backward-compatible public API" header (`scripts/agent/workflow_engine_adapter.py:106`) or the four "Backward-compatible alias for ..." docstrings (L121,128,135,144) — `re.search(r"backward-compatible", "Backward-compatible ...")` is False. A live run of `tools/check_compat_shims.py` (plain and with `--check-removed-names`) on both target files prints "All checks passed". CI wiring: `.github/workflows/backward-compat-check.yml:39` runs the checker with `--check-removed-names --check-doc-symbols`, and the checker file itself is a watched trigger path. `_REMOVED_NAME_PATTERNS` already uses `re.IGNORECASE` (L481 area) with the historical-context exemption, which is why `LEGACY_MARKER_TABLES` is not flagged there.

## Problem
The no-compatibility policy is enforced by a scanner that misses exactly the capitalized forms the codebase actually writes — the check passes not because the code is clean but because the pattern is case-blind in the wrong direction.

## Reason for Change
The removed-names scan already demonstrates the intended semantics (case-insensitive match + historical-context exemption); COMPAT_PATTERNS diverging from it is an implementation gap, not a policy.

## Implementation Intent
One mechanism change in one loop: case-fold the matched line (or add `re.IGNORECASE` to the search) so every COMPAT pattern is case-insensitive. Then run the full checker over the repository; newly flagged active-source lines are fixed per the policy (delete leftovers) or, where they are legitimate historical prose, handled by the existing exemption mechanism extended to the COMPAT scan only if the run proves docs need it — no speculative exemption is added before evidence.

## Requirements
- `REQ-001`: Every `COMPAT_PATTERNS` entry matches case-insensitively (fixture test: "Backward-compatible alias" and "backward compatibility Layer" both flagged in a code fixture).
- `REQ-002`: The full-repository run (`--check-removed-names --check-doc-symbols`, as CI invokes it) exits clean — either the tree is already clean under the new semantics or the newly-flagged active-source lines are fixed in this plan (docs prose exempted only via an explicitly added, narrowly scoped historical-context mechanism, mirroring `_HISTORICAL_CONTEXT_MARKERS`).
- `REQ-003`: No pattern text changes; only matching semantics (pattern inventory pinned by a count/list test so future edits are deliberate).
- `REQ-004`: CI workflow wiring (`backward-compat-check.yml`) passes unchanged (no workflow edits required).
- `REQ-005`: New checker tests pin case-insensitivity and the historical-context behavior for whichever exemption path Phase 1 proves necessary.

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_compat_shims.py` | Modify | Case-insensitive matching in the COMPAT_PATTERNS loop (L630-633); optional narrow historical-context exemption for docs if the repo run demands it | `REQ-001`/`REQ-002`/`REQ-005` | Case gap verified by live repro (Step 2) | `tests/tools/` checker tests | `Verified` |
| `tests/tools/` (checker test file) | Modify | Capitalized/lowercase fixture pairs; exemption behavior tests | `REQ-001`/`REQ-005` | Existing checker tests found via grep at implementation time | self | `Verified` |
| Newly flagged active-source files | Modify (evidence-driven) | Fix or (post-`wfaudit008`) none expected in the adapter after 008 lands | `REQ-002` | Repo-wide checker run in Phase 1 | n/a | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_compat_shims.py` (`_HISTORICAL_CONTEXT_MARKERS` L345-347, exemption loop L494) | The exemption mechanism to mirror if docs prose needs it | `REQ-002` |
| `.github/workflows/backward-compat-check.yml` | Exact CI invocation to reproduce locally | `REQ-004` |
| `scripts/agent/workflow_engine_adapter.py` (alias block L106-146) | The known capitalized leftover — deleted by `wfaudit008`; confirms landing order | Dependencies |

## Acceptance Criteria
- `REQ-001`: Fixture test shows capitalized and lowercase forms both produce findings.
- `REQ-002`: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` (the CI command) exits 0 over the whole repository after fixes.
- `REQ-003`: Pattern-dict size/keys unchanged (test pins the inventory).
- `REQ-004`: CI workflow file byte-identical; local reproduction of its command green.
- `REQ-005`: Full `tests/tools/` green; new tests fail on HEAD (capitalized fixture passes the old checker).

## Tests
- Parametrized case fixtures (code content scan): lowercase, Capitalized, UPPERCASE forms of "backward compatibility layer", "backward-compatible", "compatibility layer".
- Repo-clean regression: a test running the checker over the repository (already CI's behavior) — kept green by fixing findings, not by loosening patterns.
- Exemption-path test if the docs-exemption mechanism is added (docs historical prose stays unflagged; active-source prose with the same phrase IS flagged — the exemption must not leak into code paths).

## Documentation Impact
- Check `docs/` for the compat-checker usage description (the tool's own docs row in `tools/TOOL_DESCRIPTIONS.md`); update the matching-semantics sentence if documented.
- Run `tools/` docs/tooling registration checks per `routing.md` Tools (AGENTS.md rule 9 applies because `tools/` is edited).

## Assumptions
- After `wfaudit008` lands, the adapter alias block (the largest known capitalized leftover) is gone, so the strict run's remaining findings are small and fixable within this plan (Phase 1 run proves the actual count — no speculation).
- Docs contain capitalized "Backward" history prose (validation confirmed legitimate history prose exists); whether the existing exemption mechanism covers the COMPAT scan (it currently does not — COMPAT has no exemption) is settled by the Phase 1 repo run.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | exact count/location of newly flagged lines under case-insensitive matching (docs vs active source) | repo run not yet performed with the fix | Phase 1 run records the finding list; fix vs exemption decided per finding | `False` |
| `UNK-02` | whether adding an exemption to COMPAT_PATTERNS risks hiding future active-source leftovers | policy preference | prefer fixing findings; add exemption only for docs-path scanning if run evidence demands it | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_compat_shims.py` | Modify | CI gate behavior for every future commit | 13 | N/A | not applicable (not deployed; CI tool) |
| `tests/tools/` | Modify | tests only | N/A | N/A | not applicable |

## Design
**Match semantics, one loop.** Case-fold `stripped` (chosen over per-pattern flags: one edit covers all 60+ patterns and keeps pattern strings readable) at the COMPAT scan site only; the removed-names scan keeps its own already-correct mechanism.

**Strict-first, exempt-later.** The plan orders evidence: run the strict checker, list findings, fix active-source findings outright (policy: no leftovers), and consider a narrowly scoped docs-path exemption only for prose that is legitimate history (the same distinction `_REMOVED_NAME_PATTERNS` already draws via `_HISTORICAL_CONTEXT_MARKERS`). No exemption is written before a finding proves one needed (repo rule: no speculative code).

**Landing order.** After `wfaudit008`: the biggest capitalized block disappears first, minimizing dual edits.

## Implementation steps
1. **Phase 1: Semantics flip + repo census (`REQ-001`).** Implement case-insensitive matching; run the full CI command; record the findings list (UNK-01).
2. **Phase 2: Finding resolution (`REQ-002`).** Fix flagged active-source lines; add docs-path exemption only if evidence requires (UNK-02); repo run exits 0.
3. **Phase 3: Tests + tool docs (`REQ-003`-`REQ-005`).** Checker tests; `TOOL_DESCRIPTIONS.md`/doc row update if the semantics sentence exists.

### Release units
**Unit**: wfaudit012-full | **Phases**: 1, 2, 3 | **Reason**: a strictened CI gate must ship green — flipping semantics without resolving its findings would break every future CI run.

## Validation plan
- After Phase 1: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` full run; findings list recorded in the Execution Status notes.
- After Phase 2: same command exits 0; `uv run pytest tests/tools/ -q` green.
- Full `uv run pytest tests/ -q` before completion; lint/type gates per `rules/toolchain.md`.
- CI parity: local command identical to `.github/workflows/backward-compat-check.yml:39`.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Strict run floods findings (docs prose) | Medium | Medium (scope creep) | Phase 1 census before any exemption; narrow docs-path-only exemption if proven |
| Case-folding makes a pattern match a false positive in code (e.g. legitimate capitalized identifier) | Low | Low | Findings are reviewed per line in Phase 2; patterns are phrase-based, not identifier-based |
| Landing before `wfaudit008` forces edits to the adapter alias block that 008 deletes anyway | Medium | Low | Preferred order: 008 first; if unavoidable, exempt-by-deletion-timing note in the procedure doc |

## Execution Status
### Execution Status
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: semantics flip + census | Planned | engineer | | | |
| Phase 2: finding resolution | Planned | engineer | | | |
| Phase 3: tests + tool docs | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084013
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem + live repro | `tools/check_compat_shims.py` | case-insensitive matches | fixture tests |
| `REQ-002` | Issue constraint (CI must stay green) | whole repo run | CI command exits 0 | repo run + CI parity |
| `REQ-003` | Plan Design (no pattern changes) | checker | inventory pinned | inventory test |
| `REQ-004` | Issue Evidence (CI wiring) | workflow file | unchanged | file byte-check |
| `REQ-005` | Issue Testing Expectations | `tests/tools/` | fail on HEAD | pytest |

## Notes
- Source verified against HEAD `926dbc109`; the issue's `LEGACY_MARKER_TABLES` mechanism description was corrected during validation (it lives in `_REMOVED_NAME_PATTERNS` deliberately — see the issue's `## Adversarial Validation`).
- Sequence: after `wfaudit008`.
