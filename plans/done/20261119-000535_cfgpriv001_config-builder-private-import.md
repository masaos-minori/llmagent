## Goal
- Route `scripts/agent/memory/config_path.py::resolve_memory_jsonl_dir()` through a
  public config helper instead of importing the private `_get_str_or_default` from
  `scripts/agent/config_section_builders`, removing a cross-module private dependency
  while returning the identical path for identical input.

## Priority
Low

## Scope
- **In-Scope**:
  - Remove `from agent.config_section_builders import _get_str_or_default` from
    `resolve_memory_jsonl_dir()` and call a public accessor that resolves the flat
    `memory_jsonl_dir` key with the same default.
  - Add a public string-key resolver to `config_section_builders` when no suitable
    public accessor already exists; otherwise route through the existing one.
- **Out-of-Scope**:
  - Changing which config key is read (`memory_jsonl_dir`) or its default
    (`/opt/llm/memory`).
  - Refactoring any other builder or consumer in `config_section_builders`.
  - Any change to `memcfg001`'s original `KeyError('memory')` fix.
- **Dependencies**: `N/A: none`
  - **Depends on**: N/A: none

## Background
The refactor commit `e6233a903` centralized the three change-event writers on
`resolve_memory_jsonl_dir()` to avoid a `KeyError('memory')` from the nonexistent
nested config key. That fix introduced
`from agent.config_section_builders import _get_str_or_default` inside
`resolve_memory_jsonl_dir()`. `_get_str_or_default` is a private helper used only
internally by the `_build_*_config` builders; it is not part of any public API.

## Problem
`config_path.py` reaches into a private symbol (`_get_str_or_default`) of an
unrelated module. A rename, move, or removal of that helper breaks
`resolve_memory_jsonl_dir()` with an `ImportError` outside the memory module's
control and without any public contract guaranteeing its existence.

## Reason for Change
The coupling is latent today but is a maintainability risk: the next refactor of
`config_section_builders` can silently break memory path resolution. No open issue
tracks this residual; `memcfg001` fixed the `KeyError` but left the private import
in place.

## Implementation Intent
Introduce or reuse a public helper that resolves a flat string config key with a
default, and call it from `resolve_memory_jsonl_dir()`. Prefer exposing the helper
on the config-builders public surface; if a public accessor already exists, route
through it instead. Preserve the current default value and the returned value
(equal to `ctx.cfg.memory.memory_jsonl_dir` for the same input). Keep the late
import pattern (import `ConfigLoader` and the resolver inside the function) so the
memory module stays free of top-level config imports, but import only the public
symbol.

## Requirements
- `REQ-001`: `resolve_memory_jsonl_dir()` MUST NOT import any underscore-prefixed
  symbol from `config_section_builders`.
- `REQ-002`: `resolve_memory_jsonl_dir()` MUST resolve the flat `memory_jsonl_dir`
  key through a public accessor that returns the same value as before.
- `REQ-003`: the resolved default MUST remain `/opt/llm/memory` and the returned
  value MUST equal `ctx.cfg.memory.memory_jsonl_dir` for identical input.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/memory/config_path.py` | Modify | Replace the private `_get_str_or_default` import with a public accessor call; keep the late import pattern, import only the public symbol. | REQ-001, REQ-002, REQ-003 / no underscore import; same path | `config_path.py:20` imports `from agent.config_section_builders import _get_str_or_default`; `config_path.py:23` calls it with `"memory_jsonl_dir"` and `"/opt/llm/memory"` (checked in Step 3) | `tests/agent/memory/test_config_path.py` | Verified |
| `scripts/agent/config_section_builders.py` | Modify | Add a public string-key resolver (e.g. `get_str_or_default`) that wraps `_get_str_or_default`, when no public accessor already exists. | REQ-002, REQ-003 / lint-imports passes | `_get_str_or_default` is defined at `config_section_builders.py:79` and used only internally by the builders (checked in Step 3) | `tests/agent/test_config_builders.py:793` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/config_builders.py` | Confirm the current public export surface of the config-builders package to decide whether a public accessor already exists before adding one. | config_section_builders.py / REQ-002 |
| `tests/agent/memory/test_config_path.py` | Preserve the existing resolver contract and extend it with an assertion that the returned path equals the typed `cfg.memory.memory_jsonl_dir`. | config_path.py / REQ-003 |

## Acceptance Criteria
- `config_path.py` no longer imports any underscore-prefixed symbol from
  `config_section_builders` (REQ-001 / no underscore import).
- `resolve_memory_jsonl_dir()` returns the same path as before for identical input,
  equal to the typed `cfg.memory.memory_jsonl_dir` (REQ-002, REQ-003 / same path).
- `lint-imports` still passes with no new cross-layer violation (REQ-002 / lint-imports passes).

## Tests
- Run `tests/agent/memory/test_config_path.py` and confirm it still passes (REQ-001, REQ-002, REQ-003).
- Add a test asserting `resolve_memory_jsonl_dir()` equals the typed `cfg.memory.memory_jsonl_dir` for a sample config (REQ-003).
- `uv run ruff check` and `uv run mypy` on the touched files pass (REQ-001, REQ-002).

## Documentation Impact
`N/A: no docs change` — the issue notes that if `config_section_builders` documents
its public API surface, the newly exposed helper should be noted there; verify that
surface exists before concluding.

## Assumptions
- Exposing a public resolver on `config_section_builders` does not violate the
  `.importlinter` layer contract, because `config_path.py` already imports from that
  module today and the layer relationship is unchanged.
- The late import pattern inside `resolve_memory_jsonl_dir()` is intentional (keeps
  the memory module free of top-level config imports) and should be preserved.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a suitable public accessor already exists in `config_section_builders` that was not identified, or whether one must be added. | Public export surface of `config_section_builders` vs. `config_builders` re-exports. | Inspect `config_builders.py` public exports during implementation; add `get_str_or_default` wrapping `_get_str_or_default` only if none exists. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/memory/config_path.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/config_section_builders.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A classification (small task): affects 2 files, no public/runtime interface
change beyond one additive internal helper, no database schema change. Path B
analysis (architecture graphing, historical churn) is skipped per `SKILL.md`; the
qualitative `Blast Radius` above is judged from Step 3 direct verification.

Design decision (carries UNK-01 to implementation): the public resolver's home.
Two options — (a) add a new public `get_str_or_default(cfg, key, default="")` to
`config_section_builders` that delegates to `_get_str_or_default`, or (b) route
through an already-public accessor if inspection of `config_builders.py` reveals one.
Option (a) is preferred: it matches the issue's stated preference ("expose the helper
on the config-builders public surface"), keeps the change localized, and preserves the
existing `_get_str_or_default` internals used by the builders. The choice stays open at
this phase and is recorded as UNK-01; it is non-blocking because either option yields
identical behavior.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Add public accessor (if needed)**
    - [ ] Add `get_str_or_default(cfg, key, default="")` to
      `scripts/agent/config_section_builders.py` wrapping `_get_str_or_default`, unless a
      public accessor already exists (REQ-002 / `scripts/agent/config_section_builders.py`)
2. **Phase 2: Route through the public accessor**
    - [ ] Replace `from agent.config_section_builders import _get_str_or_default` with an
      import of the public accessor in `resolve_memory_jsonl_dir()` and call it with
      `"memory_jsonl_dir"` and `"/opt/llm/memory"` (REQ-001, REQ-002, REQ-003 /
      `scripts/agent/memory/config_path.py`)
3. **Phase 3: Deployment & Verification**
    - [ ] Add a test asserting `resolve_memory_jsonl_dir()` equals the typed
      `cfg.memory.memory_jsonl_dir`; run `tests/agent/memory/test_config_path.py`,
      `uv run ruff check`, and `uv run mypy` on the touched files (REQ-001, REQ-002,
      REQ-003 / `scripts/agent/memory/config_path.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/config_path.py` | Unit: resolver returns typed config value; no underscore import | `uv run pytest tests/agent/memory/test_config_path.py` | all pass |
| `scripts/agent/config_section_builders.py` | Unit: new public accessor mirrors `_get_str_or_default` | `uv run pytest tests/agent/test_config_builders.py` | all pass |
| Both | Static: format, lint, type | `uv run ruff format --check` / `uv run ruff check` / `uv run mypy` | clean |

## Risks
- **Risk**: adding a second public name for the same logic could itself become a
  duplication the next refactor targets. → **Mitigation**: the new accessor delegates
  to `_get_str_or_default` (single implementation), so no logic is duplicated.
- **Risk**: importing the public accessor at a different scope than the current late
  import could introduce a top-level config import the memory module wants to avoid. →
  **Mitigation**: keep the resolver import inside `resolve_memory_jsonl_dir()` (late
  import), matching the existing pattern.
- **Risk**: `lint-imports` could flag a new cross-layer violation if the accessor's
  module relationship is misjudged. → **Mitigation**: the import direction is unchanged
  from today; verify with `lint-imports` in Phase 3.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add public accessor to config_section_builders if none exists | Completed | — | 20261119-102153 |  |
| 2 | Route resolve_memory_jsonl_dir() through the public accessor | Completed | — | 20261119-102153 |  |
| 3 | Add test and run ruff/mypy/tests | Completed | — | 20261119-102153 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261119-072220_01_scripts_agent_memory_config_path.py.md | 2, 3 | Procedure | Completed | — | — |
| implementations/20261119-072220_02_scripts_agent_config_section_builders.py.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261118-224540_cfgpriv001_config-builder-private-import.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-000535
- **Related target files**: scripts/agent/memory/config_path.py, scripts/agent/config_section_builders.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; AI Implementation Instruction | scripts/agent/memory/config_path.py | Phase 2 | no underscore import | ruff check / test_config_path.py | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; Required Changes | scripts/agent/memory/config_path.py, scripts/agent/config_section_builders.py | Phase 1, Phase 2 | same path; lint-imports passes | test_config_path.py | Confirmed by repository evidence |
| REQ-003 | Constraints; Acceptance Criteria | scripts/agent/memory/config_path.py | Phase 2 | default /opt/llm/memory preserved | test_config_path.py (new assertion) | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261119-072220 -->
