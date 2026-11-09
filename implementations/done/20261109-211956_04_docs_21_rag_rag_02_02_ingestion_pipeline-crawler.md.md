## Goal

Update the crawler/ingestion pipeline documentation (Plan Phase 4) so the robots.txt paragraphs describe the per-outcome policy and fetch-time enforcement instead of the current start-host-preload/enqueue-time-only description (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

Row 4 of the frozen target table. Lightweight document row: the headings below are the full work item.

## Assumptions
- Line numbers revalidated 20261109: robots paragraph at L56-61 (Plan cited L54-59; shifted by the landed ragrev011 commit) and the "Robots.txt Policy" bullet at L75 (Plan cited L73). The paragraph currently describes only the start-host preload and enqueue-time filtering — Plan evidence claim accurate.
- Overlap with the ragrev012 plan on this file judged compatible (different paragraphs; Plan Assumptions).
- Documentation language: English, per `skills/DESIGN.md` Output language.

## Design decisions
- Edit only the two places the Plan names (L56-61 paragraph, L75 bullet); no restructuring of neighboring pipeline sections; redirect-trust text stays with ragrev012's procedure set.

## Alternatives considered
- None: the Plan names the exact locations.

## Implementation
### Target file
`docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`

### Procedure
1. Rewrite the robots paragraph (L56-61) with the outcome table: 200 parses the body; 404 and other 4xx except 401/403 allow all; 401/403 disallow all; 5xx and network errors (timeouts included) disallow all; each outcome logged with its class; one fetch per host (`ensure_host` (new), idempotent).
2. Describe fetch-time enforcement: before any URL request the orchestrator ensures the host's robots rules and skips a disallowed URL (start URL included) with a distinct log; the eager start-host preload remains.
3. Update the "Robots.txt Policy" bullet (L75) from "fetched once for the start host, filtered at enqueue time" to the corrected semantics (per-host lazy fetch + fetch-time refusal; enqueue-time `is_allowed` filtering remains as a pre-filter).

### Method
In-place prose edit keeping the file's existing list/heading style; terminology must match procedures 02/03 (`ensure_host` (new), outcome classes, skip log).

### Details
- State the opt-in nature (`respect_robots`, `config/crawler.toml`) unchanged: enabling is what activates the policy (REQ-005).

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
- The two places state the outcome table and fetch-time enforcement; AC-6 green; docs checkers clean.

## Out of Scope
- Other paragraphs of `rag_02_02` (ragrev011/ragrev012 own them).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 2026-11-10 | robots paragraph + Robots.txt Policy bullet rewritten per outcome table and fetch-time enforcement |
| 2 | Add or update tests per Validation plan | Completed | — | 2026-11-10 | docs gates: all five checkers clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-11-10 | check_docs_quality/structure/content_policy/consistency --domain rag/japanese: no findings; targeted pytest green |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-10 | N/A: this procedure IS the documentation change |

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
- **Related target files**: docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md