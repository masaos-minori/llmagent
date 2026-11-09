## Goal

Update the `respect_robots` entry in the configuration reference (Plan Phase 4) from its current start-host-only/enqueue-time description to the corrected policy semantics (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

Row 5 of the frozen target table. Lightweight document row: the headings below are the full work item.

## Assumptions
- Line number revalidated 20261109: the `respect_robots` bullet is at `docs/21_rag/rag_05_01-configuration-reference.md` L35 and states only the start-host preload ("the start host's robots.txt is fetched and parsed once before the crawl ... skipped at enqueue time; it defaults to disabled") — Plan evidence claim accurate.
- Opt-in default remains disabled and accurately documented: `config/crawler.toml` L30 sets `respect_robots = false`; this fact is not changed by the Plan.
- This reference documents `config/crawler.toml` (used by `crawler.py`, which constructs `RobotsCache` at L84 and passes it through link discovery into the orchestrator crawl path where enforcement lands per procedure 03).

## Design decisions
- Rewrite only the `respect_robots` bullet (L35); the file's ownership-first style (L27: no per-key inventories) is preserved — describe intent and failure behavior only (Plan Documentation Impact).

## Alternatives considered
- None: the Plan names the exact location.

## Implementation
### Target file
`docs/21_rag/rag_05_01-configuration-reference.md`

### Procedure
1. Rewrite the L35 bullet: when enabled, robots.txt is ensured lazily per host (one fetch per host, `ensure_host` (new)) before that host's first page request, and each outcome maps to a policy decision — 200 parses; 404 and other 4xx except 401/403 allow all; 401/403, 5xx, and network errors disallow all (fail-closed); disallowed URLs (including the start URL) are refused at fetch time with a distinct log.
2. Keep the opt-in/default-disabled sentence and the "no robots.txt request when disabled" behavior unchanged (REQ-005).

### Method
In-place prose edit of one bullet, matching the file's bullet style.

### Details
- Terminology must match procedures 02/03; keep the entry short — full policy detail lives in `rag_02_02` (procedure 04).

## Compatibility considerations
- Related Tests column is "docs gates": run the Plan's docs gates — `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py`.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- Revert this file alone; no code coupling.

## Validation plan
- Docs gates listed in the Plan Validation plan (all five checkers) — no findings.
- `uv run pytest tests/rag/ingestion -q` remains green (docs-only change).

## Completion criteria
- L35 no longer states start-host-only/enqueue-time-only behavior; states per-host lazy fetch, outcome table, fetch-time refusal; AC-6 green; docs checkers clean.

## Out of Scope
- Any change to `config/crawler.toml` values (Out-of-Scope: making the policy non-opt-in).
- Other bullets of this configuration reference file.

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261108-131232_ragrev014_robots-policy-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170335_ragrev014_robots-policy-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-09 21:19:56
- **Related target files**: docs/21_rag/rag_05_01-configuration-reference.md
