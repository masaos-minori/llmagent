# tools/ Directory Overview

`tools/` holds scripts that run documentation-consistency CI checks and bulk documentation/source edits. Most were created under the `AGENTS.md` rule: "if the same operation is performed three or more times, extract it into a script and place it under `tools/`".

Naming convention: `<verb>_<target>.py`.

- `check_*`: pass/fail judgment or detection.
- `fix_*`: applies a correction.
- `generate_*`: generates output.
- `manage_*`: several subcommands for managing one kind of object.
- `rename_*`: a single specific operation.

Drift in this file itself is detected by `check_tool_descriptions_sync.py`, which cross-checks `tools/*.py` against the backticked `*.py` names mentioned here.

## Index (44 modules)

| File | Category | Purpose |
|---|---|---|
| `_docs_consistency_lib.py` | Shared base | DocFile/Issue data types, file discovery, generic checks |
| `_front_matter_schema.py` | Shared base | Single source of truth for the Front Matter schema |
| `check_adr_invariant_matrix.py` | ADR | Verify that test node IDs in the ADR Invariant Verification Matrix exist |
| `check_adr_reference.py` | ADR | Verify source-file references in the ADR Invariant Verification Matrix |
| `check_adr_structure.py` | ADR | Verify ADR structure: Known Deviations heading, Implementation Notes/References consistency, allowed heading list and order, leftover template instructions and legacy `INV-NNN` IDs |
| `check_canonical_document_prose.py` | Canonical Source | Scan `docs/*.md` for unregistered canonical-document prose assertions |
| `check_canonical_source_conflicts.py` | Canonical Source | Detect semantic conflicts in the Canonical Source Registry |
| `check_canonical_source_registry.py` | Canonical Source | Validate the Canonical Source Registry schema |
| `check_compat_shims.py` | Consistency checker | Detect leftover backward-compatibility stubs and shims |
| `check_docs_consistency.py` | Consistency checker | Cross-check `docs/` claims (ports, config keys, symbol references, command contracts) against `config/agent.toml` and `scripts/`, per `--domain` |
| `check_docs_content_policy.py` | Docs policy | Detect implementation-detail content that violates `skills/DESIGN.md` "Docs content policy — remove" and "Avoid implementation-reference duplication" (16 categories) |
| `check_adr_preservation.py` | ADR lightweighting | Compare changed `docs/10_adr/*.md` files with a Git ref and report content-preservation errors plus before/after sizes |
| `check_docs_japanese.py` | Docs policy | List Markdown files containing hiragana, katakana, or kanji (exit code 1 if any) |
| `check_docs_quality.py` | Docs quality | Core checks plus custom rules for documentation quality |
| `check_docs_structure.py` | Docs structure | Validate structural conventions of `docs/*.md` |
| `check_dependency_graph_cycles.py` | Dependency | Detect cycles in the software runtime dependency graph |
| `check_known_deviation_sync.py` | ADR | Check that ADR Known Deviations reference the canonical source (`governance_03`) consistently, and detect leaked Resolved items (rule ID `GV-022`) |
| `check_mock_patch_targets.py` | Test | Detect `unittest.mock.patch()` targets that are ineffective |
| `check_needs_confirmation_inventory.py` | Consistency checker | Verify that every Needs confirmation mention is registered in the central inventory |
| `check_issue_inventory_conformance.py` | Consistency checker | Validate the vocabulary, template, and reference integrity of the Issue inventory |
| `check_plan_target_overlaps.py` | Work item | Detect the same file path targeted by multiple Frozen Plans |
| `check_suppression_justification.py` | Lint/Suppression | Detect `# noqa` / `# type: ignore` / `# nosec` comments that lack a justification |
| `check_workitem_traceability.py` | Work item | Check consistency of `## Traceability` sections |
| `check_workitem_structure.py` | Work item | Verify that all canonical template headings are present |
| `check_conftest_integrity.py` | Test | Verify that `tests/conftest.py` defines the required autouse fixtures |
| `generate_mcp_inventory.py` | Reference generation | Output the MCP server list from agent config as JSON/CSV |
| `generate_reference_table.py` | Reference generation | Generate reference tables for RAG/MCP/deployment/agent/EventBus (the Memory type is pending a decision on its target document); `--check` exits 1 when a generated guarded block drifted from live code (runs in CI) |
| `generate_workitem.py` | Work item generation | Generate work item skeletons with placeholders. `--kind implementation-procedure --all-rows` generates every row of the Plan's `Implementation Target Files` table in one run (rows whose file already exists are skipped and processing continues) |
| `manage_frontmatter.py` | Front Matter management | Detect missing Front Matter, remove duplicates, rename `area`, merge body Related sections into `related:` |
| `manage_workitem_stage.py` | Work item management | Archive moves, status updates, stale detection |
| `manage_binaries.py` | Deploy | Write build info for the Nuitka binaries, check their freshness against a source revision, swap a staged set into the bin directory with the previous set saved, roll back, and record the deployed revision |
| `rename_doc.py` | Rename helper | `git mv` a `docs/*.md` file and update internal links and Front Matter `related:`. Also reports mentions of the old filename in tracked files outside `docs/` (scripts/tools/tests/skills, etc.) |
| `fix_docstring_blank_line.py` | Formatting helper | Bulk-fix D205 violations (missing blank line after docstring summary) |
| `fix_docs_section_marks.py` | Formatting helper | Replace the `§` symbol with plain English wording |
| `fix_docstring_paths.py` | Formatting helper | Update the path in the module docstring header of scripts modules |
| `check_docstrings.py` | Docs quality | Validate script docstring format; existing violations are grandfathered in `check_docstrings_baseline.txt` (`--update-baseline`, `--no-baseline`) |
| `check_tool_descriptions_sync.py` | Consistency checker | Cross-check this file against the actual `tools/*.py`. Also verifies that every `tools/<name>.py` / `-m tools.<name>` reference in `.github/workflows/*.yml`, `.pre-commit-config.yaml`, and `tox.ini` points to an existing tool |
| `check_chunks_fts_invariant.py` | Consistency checker | Detect direct INSERT/UPDATE statements on `chunks_fts` in Python sources under `scripts/`, outside the allowed paths (`rag_maintenance_service.py::rebuild_fts()` and `scripts/db/schema_sql.py`). `scripts/mcp_servers/mdq/` and `tests/` are excluded |
| `check_db_separation.py` | Consistency checker | Verify the ADR-008 SQLite 4DB separation: table ownership per database, cross-DB `REFERENCES`, distinct DB file paths, sqlite-vec scope, and `ATTACH`/schema-qualified access in `scripts/` SQL strings (exit code 1 on violation) |
| `check_skills_references.py` | Consistency checker | Verify that backticked file references in `AGENTS.md`, `routing.md`, `skills/DESIGN.md`, `rules/*.md`, `skills/**/*.md`, and `prompts/*.md` exist. Only references under `rules/`, `skills/`, `templates/`, or to `AGENTS.md` / `routing.md` themselves are checked |
| `check_skills_heading_cycles.py` | Consistency checker | Detect heading-level circular references among `AGENTS.md`, `routing.md`, `skills/DESIGN.md`, `rules/*.md`, `skills/**/*.md`, and `prompts/*.md` (`prompts/05_skills.md` "Circular reference check"). Builds `(file, heading)` edges from backticked `.md` references followed by a quoted heading, `Step N`/`Phase N`, or an unquoted heading name; bare file references, references inside fenced code blocks, and same-file references create no edge (cross-file cycles only). Reports each strongly connected component with more than one node as an ERROR. `--format json` for machine-readable output |
| `stale_detector.py` | Consistency checker | Verify that line numbers, symbol names, imports, and `# Before:` blocks cited by an implementation procedure still exist in the current source, using regular expressions. A single mismatch marks the procedure stale and blocks execution. The CLI reports the result by exit code (1 if stale). Details are in the "Stale detector rules" section below |
| `mark_procedure_new_symbols.py` | Work item | `list` reports the symbol names `stale_detector.py` reports as missing in one procedure document with the lines of their unmarked backticked occurrences; `mark` inserts the `(new)` marker for the names the operator supplies, and refuses any name `stale_detector.py` does not report as missing |
| `set_execution_status.py` | Work item | Mark the selected rows of one procedure document's `### Execution Status` table `Completed`, stamp the `Started` and `Completed` columns, and set `Notes` from `--note STEP:TEXT`. `--all` or `--step 1,4` selects rows; a step the table does not contain is refused. Updates the table state `manage_workitem_stage.py close-implementation` gates on |
| `run_refactor_validation.py` | Validation runner | Runs the per-file refactor gate (`rules/toolchain.md`): ruff format and check, mypy, radon grade gate, targeted tests, coverage plus diff-cover scoped to the changed files |

## Domain Documentation Consistency Checkers

All of these share DocFile/Issue/`discover_md_files` and related helpers from `_docs_consistency_lib.py`. Each checks only its own domain under `docs/`, using its own logic. They compare docs against source-of-truth code and config (`config/agent.toml`, `scripts/mcp_servers/`, `scripts/db/config.py`, etc.).

| File | Target domain | What it checks |
|---|---|---|
| `_docs_consistency_lib.py` | (shared base; cannot run standalone) | DocFile/Issue data types and file discovery. Generic checks: broken internal links, references to deleted files, slash-command drift, completeness of directory listings, existence of `scripts/` path references and function references |
| `_front_matter_schema.py` | (shared base; cannot run standalone) | Single source of truth for the Front Matter schema shared by `check_docs_structure.py` and `manage_frontmatter.py`. If `schemas/doc_front_matter.json` exists, it is the canonical source (loaded as a draft-07 JSON Schema: `required`, `properties.area.enum`, `properties.status.enum`). If it does not exist, falls back to the built-in default (`title`/`area`/`tags`/`related`, no enum constraints). Prevents the schema values and required-field list from being defined twice across tools |
| `check_docs_consistency.py` | `--domain agent\|mcp\|rag\|deployment\|overview` | Integrates the checks for the five domains above. `--skip <check>` skips a specific check. The agent domain also runs `commandcoverage` (rule `GV-023`): every `_COMMANDS` command must be in the `agent_07_03` Built-in Command Index and named in a per-command chapter, and every index row must be registered or REPL-reserved. It also runs `commandcontract` (GV-023): usage lines rendered from the registry (`SubcommandSpec`/`ArgSpec`) must match the per-command chapters in both directions, including stated defaults |
| `check_needs_confirmation_inventory.py` | All of `docs/*.md` | Checks that every "Needs confirmation" mention is registered in the central inventory in `governance_03` (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`); that no marker remains at the location of a resolved NC item; and that the declared field count equals the actual number of list items. `_GOVERNANCE_META_DOCS` (the list of excluded governance documents) was corrected on 2026-09-03 to the four current `docs/00_governance_*.md` files (none of the seven old filenames still existed) |
| `check_canonical_document_prose.py` | `config/documentation_canonical_sources.toml` | Warning-level scan of `docs/*.md` for prose that asserts a document or code path is the canonical / normative / authoritative source for a topic or claim type. Extracts the subject (a `.py` path, a `scripts/`/`docs/` path, or a `decision_target`-like token; bare filenames in markdown links are rejected) and flags (a) overlap with a registered source/target (CANONICAL-PROSE-001, REQ-002) and (b) subjects asserted by two or more distinct claims (CANONICAL-PROSE-002, REQ-003). Negated mentions ("is not the canonical source"), the label form ("- Canonical Source: `path`"), and incidental "authoritative source of truth" are excluded; the assertion-keyword regex only needs a negation keyword in the preceding window because the matched phrase already begins with the keyword. Only WARNING findings and always exits 0, preserving the CI exit contract. `scan_claims()` returns `CanonicalClaim` objects (subject + context) for reuse by area-grouping extensions. Tuned against the current corpus so it yields zero benign false positives (REQ-004) |
| `check_canonical_source_conflicts.py` | Same as above | Detects semantic conflicts in the Canonical Source Registry (prefixes CANONICAL-C/HIGH/MEDIUM/CANONICAL-W/CONFIG/NEEDS/GOV/KNOWN). Supports the REQ-001 eight-rule classification (FindingRoute Enum + `classify_finding()`), the REQ-008 duplicate-active-record prevention (`detect_duplicate_active_records()`), and the 12-field template for CANONICAL_CONFLICT |
| `check_canonical_source_registry.py` | `config/documentation_canonical_sources.toml` | Validates the Canonical Source Registry schema (versioned dataclass definitions). Checks that each registered `source_paths` entry exists relative to the repository root; the single-canonical-source constraint (only one path, except for claim-types that allow multiple files such as `runtime-behavior`); that all 13 claim-types of `M-01-01` are covered; and that ADR-derived entries have `## Status` equal to `Accepted`. `load_registry()` and `validate_registry_schema()` are reused by `check_canonical_source_conflicts.py` |
| `check_known_deviation_sync.py` | `docs/**/*.md` (ADRs for Known Deviations; every other doc for stale IDs), `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (formerly `docs/*_90_inconsistencies_and_known_issues.md`) | Rule ID `GV-022` in `governance_04`. Wired into pre-commit as the `known-deviation-sync` hook and into `governance-docs-consistency.yml`. Detects (a) dangling references (WARNING): Known Issue IDs (e.g. `MCP-004`) referenced by an ADR's `## Known Deviations` that have no matching heading in the canonical source; (b) the reverse direction (WARNING): a Known Issue whose `Target` names an ADR that the ADR's `## Known Deviations` does not cite; (c) Known Issue IDs cited anywhere else under `docs/` (ADR bodies outside `## Known Deviations` included) that have no entry in the canonical source (ERROR; catches an ID deleted at resolution whose references were left behind; prefixes come from the canonical source's ID-prefix convention); and (d) Resolved items (ERROR): bullets of the form `- **Resolved**:` or continuation bullets `Status: Resolved` inside `## Known Deviations` (the Current-Specification-Only Policy forbids keeping resolved items). The canonical source is `governance_03` (Part 1, `#### <ID>` headings; Part 2 NC items are excluded). Read-only (detects only; never auto-fixes). `--format json` gives machine-readable output |
| `check_issue_inventory_conformance.py` | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Validates the Issue inventory: (a) vocabulary of Status/Type/Severity/Area/Owner values (applies to the `### Status Values` definitions in Parts 1-4, the Status column of the Part 1 Active Items table, and `- **Status**:` in Parts 3/4; resolved-type Status values such as `resolved` are forbidden in every Part); (b) template (field count); (c) reference integrity (dangling Related / Related NC / Target references). Tracked by the GV-008 Governance Verification Matrix. Read-only. `--format json` gives machine-readable output |
| `check_adr_invariant_matrix.py` | `docs/10_adr/adr_01_index.md` | For backticked pytest node IDs in the `Verification Status` column of the ADR Invariant Verification Matrix (e.g. `` `tests/agent/test_startup.py::test_name` ``), verifies that the target file exists (does not run the tests). Out of scope: rows with no test yet ("no test yet", etc.) and code references (cells containing only `.py` without `::`). Read-only. `--format json` gives machine-readable output (GV-012) |
| `check_adr_reference.py` | `docs/10_adr/adr_01_index.md`, `scripts/**/*.py` | For source files that the ADR Invariant Verification Matrix cites by full path in the form `scripts/<path>.py`, verifies that the file contains a comment referencing the ADR ID of that row (e.g. `ADR-004`). Out of scope: bare filenames without a path, and test-node citations of the form `tests/*.py::test_name`. Read-only. `--format json` gives machine-readable output (GV-012) |
| `check_adr_structure.py` | `docs/10_adr/*.md` | For each ADR, verifies: (a) the `## Known Deviations` heading exists (Error if missing); (b) drift of scripts/tests path citations between `## Implementation Notes` and `## Implementation References` (Warning if a path appears only in Notes; ADRs whose Notes cite zero such paths are out of scope for this check); (c) the `##` headings of `adr_02_NNN_*.md` match the allowed list and order in governance_01 "ADR Section Header Standardization", with all required headings present (violations are Errors); (d) no template instruction text (e.g. "Briefly describe") and no legacy serial `INV-NNN` IDs remain in the ADR body (Error). Read-only. `--format json` gives machine-readable output |
| `check_workitem_traceability.py` | `issues/`, `plans/`, `implementations/` (including each `done/`) | Parses the `## Traceability` section of each document and detects five finding types. (1) missing-source-file: a file referenced by `Source *` does not exist. (2) no-plan-yet: an issue is not linked to a plan. (3) no-procedure-yet: a plan is not linked to a procedure. (4) stale-target-heuristic: a referenced document may have been updated after the issue was written (candidates only; not a definitive judgment). (5) target-file-mismatch (`implementation` kind only): the `Related target files` value in Traceability differs from the `### Target file` value in the body, which suggests a copy-paste error or content from another document leaking in. Read-only (never writes, renames, moves, or deletes under `issues/`, `plans/`, `implementations/`). `--format json\|csv` gives machine-readable output. `--active-only` excludes findings about history files under `done/` (used by the pre-commit hook `workitem-traceability`). When comparing `Related target files` with `### Target file`, trailing punctuation, escaped backticks, and trailing prose are normalized away |
| `check_workitem_structure.py` | `issues/`, `plans/`, `implementations/` (each `done/` only with `--include-done`) | Verifies that each document contains every `## ` heading defined inside the `` ```markdown `` fence of its canonical template (`templates/issue.md` / `templates/plan.md` / `templates/implementation-procedure.md`). Detects structural defects such as a missing `Implementation Target Files` or `Traceability` section. (`check_workitem_traceability.py` validates only the contents of the `## Traceability` section, not its presence.) `--file <path>` targets a single file (kind is inferred from the path); `--kind` narrows the target kind. Read-only. `--format json\|csv` gives machine-readable output |
| `check_compat_shims.py` | `scripts/`, `docs/`, `tests/`, `tools/` | Detects leftover backward-compatibility stubs and shims. `--check-removed-names` (default OFF) additionally checks `docs/*.md` for reappearance of removed identifiers: it checks that `_update_null_fill` is absent, and detects co-occurrence of `ToolRouteResolver` and `server_configs` within one section; history/resolved contexts are excluded in both. The live corpus reports zero findings — the section-scoped `ToolRouteResolver`+`server_configs` matcher exempts lines that deny the stale argument (the corrections made by `plans/20260903-090104_plan.md`). The flag is not included in the default `.pre-commit-config.yaml` invocation (flagless), i.e. report-only operation |
| `check_docs_quality.py` | All of `docs/*.md` | Core checks (broken headings, invalid Markdown tables, unclosed code blocks, JSON examples missing a fence, duplicate heading numbers, Migration Notes placement, etc.) plus custom rules. Custom rules are loaded dynamically from `config/doc_quality_rules.json`; a rule with `exempt_historical_context: false` also inspects lines containing history markers such as `resolved` / `removed`. Current rules cover history/changelog markers (ERROR) and unverified expressions (WARNING). Filter with `--core-only` / `--custom-only` / `--skip <check>` / `--only <check>`. The cross-document content-similarity check excludes same-named section pairs that are intentional boilerplate: ADR standard template sections (Approval Record, etc.) and area-guide boilerplate sections (Canonical Sources, etc.) |
| `check_docs_content_policy.py` | All of `docs/*.md` (recursive, including subdirectories such as `docs/10_adr/`) | Detects 16 categories of implementation detail that `skills/DESIGN.md` "Docs content policy — remove" and related sections prohibit: ASCII file trees; one-line descriptions embedded in trees/tables; class/function/method index tables; implementation-location mappings; literal port numbers; default values restated outside tables; Field/Type/Default tables; config-file inventory mapping tables; CLI command enumerations; environment-setup command sequences; DDL/schema blocks; TypedDict/DTO field tables; CLI argument tables; exception-handling tables; full JSON examples; comparisons of code fallback values against operational values. Findings are Warnings: report-only by default, `--strict` exits 1 on any warning (CI, blocking). `rules/env.md` is outside `docs/*.md` and therefore not scanned (`GV-018`) |
| `check_adr_preservation.py` | Changed `docs/10_adr/*.md` vs a Git ref (default `HEAD`; `--base <ref>`; explicit file paths allowed) | Proves an ADR size reduction kept its content. ERROR (exit 1): front matter, H2 sequence, `INV-NN` ids or text, Related ADRs, Implementation References, `path.py::test` citations, or the `Known Deviations` / `Approval` text differ. WARNING: `Decision`, `Failure Policy`, `Data Ownership and Persistence`, or `Invariants` text differs (needs a sentence-level mapping), a `MUST NOT`/`MUST`/`SHOULD`/`MAY` count decreased, or a backtick-quoted path/symbol disappeared. Non-ADR documents (`--dir docs/24_eventbus`) use a generic rule set: ERROR for front matter, `AUTO-GENERATED` block, or unbalanced code fence changes; WARNING for an HTTP `METHOD /path`, status code, or backtick-quoted path/symbol that no longer appears anywhere in the compared set, an H2 sequence change, or a decreased normative-keyword count. Prints per-file and total byte reduction; tokens are not measured |
| `check_docs_japanese.py` | All of `docs/*.md` | Lists Markdown files containing hiragana, katakana, or kanji (`U+3040`-`U+9FFF`). Used to find violations of the English-only policy for `docs/` in `skills/DESIGN.md` "Output language". Exits with code 1 if any file matches (used by the pre-commit hook `docs-japanese`) |

## Reference Generators

These scripts generate reference tables in `docs/` from values in source code and config files, and write them between `<!-- AUTO-GENERATED: ... -->` guard comments. Re-running refreshes the content, so never hand-edit that region. `--dry-run` prints to stdout only.

| File | Source | Destination |
|---|---|---|
| `generate_reference_table.py` | Selected by `--type rag\|mcp\|deployment\|agent\|eventbus` (`memory` will be added once its target document is decided) | The reference sections for RAG/MCP/deployment/Agent/EventBus. `--check` (optionally with `--type`) writes nothing and exits 1 when a doc's `AUTO-GENERATED` block is missing or differs from the generator output |
| `generate_mcp_inventory.py` | Selected by `--format json\|csv` | Outputs the MCP server list from agent config as JSON or CSV |
| `generate_workitem.py` | Selected by `--kind issue\|plan\|implementation-procedure\|unknowns\|risks` | Extracts a placeholder-only skeleton from the matching `templates/*.md` and writes it to `issues/`, `plans/`, or `implementations/` using the naming convention (never generates substantive content). For `unknowns` / `risks`, on a name collision, retry with an explicit zero-padded sequence number via `--seq` (no auto-numbering; reject-only) |

## Docs Structure Validation and Formatting Helpers

| File | Description |
|---|---|
| `check_docs_structure.py` | Validates structural conventions of `docs/*.md`: file size (an individual size-limit exception exists only for documents the owner has allowed); H1 heading count; Front Matter; Keywords section; reachability of internal `.md` links. ADR bodies (`ADR-*.md`) require `## Related ADRs`. In every document including ADRs, a body Related-type section (`## Related Documents` / `## Related Docs` / `## Related Chapters`, at any heading level) is reported if it remains. ADR documents are also checked for whether the Front Matter `related:` covers every body reference. Each `related:` entry must be a bare filename ending in `.md` (no path, no anchor). Usage: `uv run python tools/check_docs_structure.py [glob ...]`. `--schema [PATH]` (default `schemas/doc_front_matter.json` when the value is omitted) additionally runs schema-driven Front Matter validation (required fields and `area`/`status` enum constraints); it is disabled by default and does not affect existing behavior. The schema itself is loaded via `tools/_front_matter_schema.py`; if it does not exist, falls back to the current four required fields |
| `check_dependency_graph_cycles.py` | Parses the edge list (`- A → B` format) from the `## Software Runtime Dependency Graph` section of `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, and exits non-zero if a cycle exists among the five nodes Agent/MCP/RAG/EventBus/Shared-DB. Edges under both `Confirmed edges` and `Needs Confirmation` are included in cycle detection |
| `manage_frontmatter.py` | Subcommands. `add-missing`: detect and add missing Front Matter (if `area` cannot be inferred from the filename with confidence, it is not guessed as `overview` etc.; the file is only reported as `[AMBIGUOUS]`). `dedupe-lists`: remove duplicate entries from list fields. `rename-category-to-area` (new): rename the `category:` key inside valid fenced (`---`) Front Matter to `area:`, keeping the value (if both keys coexist, report only and do not rename). `merge-related` (one-off migration aid; `## ` level only): merge entries of body `## Related Documents` / `## Related Docs` / `## Related Chapters` into Front Matter `related:` (default is dry-run; `--fix` writes; walks `docs/**/*.md` recursively; path arguments narrow the target; for ADR documents only Front Matter is updated and the body is left unchanged; sections containing non-link lines or nonexistent references are reported, not deleted; deeper `### ` blocks are out of scope and need manual migration; body blocks at any level are detected by `check_docs_structure.py`). Bug fix on 2026-09-03: `AREA_PREFIX_MAP` lacked the `06_eventbus` prefix (nonexistent `06_config` / `91_eventbus` were registered by mistake, so existing `06_eventbus_*.md` files were wrongly inferred as `area: overview`) |
| `rename_doc.py` | Takes `<old-path> <new-path>` and runs `git mv` on a `docs/*.md` file (including `docs/10_adr/*.md`). Scans all Markdown files under `docs/` and rewrites Markdown link paths to that file and Front Matter `related:` entries (bare filename or `../` form; other forms are reported, not rewritten). If both `--old-title` and `--new-title` are given, link text is also replaced (non-link plain-text mentions are reported, not rewritten). Writes are limited to `docs/`. Mentions of the old filename (including with a path) in tracked text files outside `docs/` (excluding `*/done/` and `*/superseded/`) are reported, not rewritten. Without `--apply`, it behaves as `--dry-run` (default) and only displays the changes |
| `fix_docstring_blank_line.py` | Bulk-fixes D205 (no blank line right after the docstring summary line) by inserting a blank line. Triple-quoted string detection is hardened to avoid false positives on SQL string literals. `--dir` sets the directory to scan |
| `fix_docs_section_marks.py` | Removes the section symbol `§` (a cause of rendering problems) from Markdown files under `docs/` and `skills/` and replaces it with plain English (`section N`, `sections N-M`, etc.). `--dir <path...>` changes the scan target (default `docs skills`). Dry-run unless `--apply` is given |
| `fix_docstring_paths.py` | Rewrites the module-level docstring header path of `scripts/**/*.py` to the repository-root-relative form (`scripts/<relpath>`). A first line with no self-reference becomes `scripts/<relpath> — <existing text>`, matching `check_docstrings.py`. Files with no docstring, or whose first line already contains an em-dash, are reported for manual review, not edited. `--dry-run` shows the changes; `--apply` applies them |

## Test-Related Checkers

Static checks of test-environment health. This group includes both heuristic report-only tools and gate tools that detect definite defects.

| File | Target | Description |
|---|---|---|
| `check_mock_patch_targets.py` | `tests/**/test_*.py` | Uses AST static analysis to detect `unittest.mock.patch("module.Symbol")` calls that are ineffective (`ineffective-patch-target`): the target string names a symbol that the module under test (a known source module imported by the test file itself) has already bound into its own namespace via a module-level `from module import Symbol`. A bound reference is not rewritten by patch. Deferred imports inside functions and imports under `if TYPE_CHECKING:` are not treated as module-level (only direct children of `ast.Module.body` are examined), so they are not false positives. `patch.object(...)` is out of scope (the target is not a dotted string). Because it is heuristic, false positives are possible; any finding makes the exit code 1 (exclude a false positive individually with a marker). Used by the pre-commit hook `mock-patch-targets`. Read-only. `--format json\|csv` gives machine-readable output. Appending `# mock-patch-ok: <reason>` to the end of the physical line containing `patch(` excludes that patch from detection (for legitimate patches the heuristic cannot distinguish, e.g. when the module under test imports inside a function). The reason is required; a marker with an empty reason, or a marker on a different line, does not suppress |
| `check_conftest_integrity.py` | `tests/conftest.py` | Verifies three things. (1) `tests/conftest.py` exists. (2) No suspicious renamed backup file of the form `conftest.py.*` exists as a sibling (conftest-suspicious-backup-file). (3) Every known required autouse fixture listed in `REQUIRED_AUTOUSE_FIXTURES` (a hardcoded manifest; e.g. `_reset_tool_registry`) is still defined as `@pytest.fixture(autouse=True)`. Motivation: a real incident where `tests/conftest.py` was renamed to `.bak` by an unrelated commit and pytest silently skipped it for about one month, so about 130 order-dependent test-pollution failures accumulated undetected. Read-only. All three categories are definite defects (not heuristics), so the exit code is gated. `--format json\|csv` gives machine-readable output |

## Refactor Validation Runner

Runs the per-file validation gate defined in `rules/toolchain.md` so a multi-file refactor program does not re-type the same command chain (`AGENTS.md` Global Rule 7).

| File | Target | Description |
|---|---|---|
| `run_refactor_validation.py` | `--src scripts/**/*.py` (repeatable), `--tests tests/**/*.py` (repeatable) | Runs in order: `ruff format` and `ruff check` on the given source and test files, `mypy --no-namespace-packages` on the source files, the radon grade gate (fails when any function scores grade C or worse), the targeted tests, then `coverage run` over the same tests plus `coverage xml` and `diff-cover` (default `--fail-under 90`, `--compare-branch master`). `--include` is set from `--src`, so the diff-cover score covers only the files under refactor and previously completed files in the same working tree do not lower it. `--skip mypy\|radon\|tests\|diff-cover` drops a step. Prints one `PASS`/`FAIL` line per step plus a `GATE PASSED`/`GATE FAILED` summary; exit code 1 on any failure. Read-only: it never edits source |

## Lint/Suppression

Detects missing justifications on Python static-analysis suppression comments (`# noqa`, `# type: ignore`, `# nosec`).

| File | Target | Description |
|---|---|---|
| `check_suppression_justification.py` | `scripts/`, `tests/` | Detects `# noqa` / `# type: ignore` / `# nosec` comments that are not accompanied by a rule/error code and a justification separated by an em-dash (` — `). `DEFAULT_ALLOWLIST` tolerates existing non-conforming lines as a baseline |

## Work Items

Scripts that check consistency and manage the lifecycle of work items (issues/plans/implementations).

| File | Target | Description |
|---|---|---|
| `check_plan_target_overlaps.py` | `plans/*.md` (excluding `plans/done/`) | Detects multiple `Frozen` Plans that target the same file path in their `## Implementation Target Files` tables (`cross-plan-target-overlap`). Design contradictions cannot be judged by static analysis, so it presents only the mechanically cheap precondition (multiple Plans targeting one file at the same time) as candidates. Motivation: a real incident where an SSE heartbeat Plan and a delivery-state-transition Plan targeted the DLQ requeue model in contradictory ways (each was self-consistent alone; the conflict surfaced only as a test-suite collision). `Draft` Plans are out of scope (`Implementation Target Files` is not canonical until `Frozen`). Heuristic report-only tool; the exit code is always 0. Read-only. `--format json\|csv` gives machine-readable output |
| `manage_workitem_stage.py` | `issues/`, `plans/`, `implementations/` | See the subcommand reference below |

### manage_workitem_stage.py subcommands

Archive moves:

- `close-issue`, `close-plan`, `close-implementation` run the archive move through `git mv` (via GitPython): `issues/` to `issues/done/`, `plans/` to `plans/done/`, `implementations/` to `implementations/done/`.
- Common preconditions (`move_to_done()`): the source file exists; the destination does not exist; the `done/` directory exists (an explicit error message is returned otherwise).
- Uncommitted changes: if `git status --porcelain` shows uncommitted changes on the source file alone (untracked, staged, or post-commit modifications all count), the tool does not refuse. It auto-commits with `git add` + `git commit` (through the real command, so pre-commit hooks apply) and then moves. Commit message: `chore: auto-commit {kind} before archival move ({filename})`. Uncommitted changes in other files are ignored and not included. There is no bypass flag (the former `--allow-uncommitted` was removed and replaced by the auto-commit).
- `--stage-only` (on every `close-*` subcommand): instead of auto-committing, only runs `git add` (no commit is created). The move is included in the subsequent commit, and pre-commit hooks run at that commit.
- Remote check: if an `origin` remote is configured, the tool fetches. If the destination path already exists on the remote-tracking branch (another session may have already archived it), the move is refused. If the fetch fails, the check is skipped and the tool continues (non-blocking).
- Lock conflicts: if `.git/index.lock` contention is detected during `git status` / `git mv`, retries up to 3 times.
- `close-issue` guard: if a Plan under `plans/` (not `plans/done/`) points to the issue with a `- **Source issue**:` line and that Plan's `Freeze status` is not `Frozen` (it is `Draft`, or the line is missing), the move is blocked. It is forced only when both `--force` and `--reason <reason>` are given. An issue with no such Plan moves as usual.
- `close-implementation` guard: if the `### Execution Status` table of the target file still has a `Pending` row, the move is blocked. It is forced only when both `--force` and `--reason <reason>` are given. If the `Status` column itself cannot be found (for example, the column was renamed), the guard would be disabled, so the tool stops with an error instead.
- Every `close-*` subcommand only moves files; it never edits file content (such as Execution Status rows).

Status updates and queries:

- `set-status`: updates the Status column of every step in the `### Execution Status` table to the same value.
- `set-step-status`: updates only a specific step, selected by `--step N` or `--description "text"`.
- `--notes` (both `set-status` and `set-step-status`): appends to the Notes column (sets it directly if empty; otherwise appends separated by a space).
- `detect-stale`: detects stale In Progress/Pending work items (`--days 7` sets the threshold).
- `list`: lists work items by kind and status.
- `show`: displays the Execution Status table of a work item.

## Stale Detector Rules

`stale_detector.py` verifies the references in an implementation procedure against the current source.

- What it checks: line numbers, symbol names, imports, and `# Before:` blocks cited by the procedure. A single mismatch marks the procedure stale and blocks execution. The CLI returns exit code 1 if stale.
- Import references: only import statements that start at the beginning of a line are checked. Mentions inside prose are out of scope.
- `(new)` marker on symbols and imports: a backticked name or import statement followed by `(new)` is treated as something the procedure will newly create and is excluded from the existence check. A missing name without the marker is stale as before.
- `(new)` marker on the target file: a backticked path in the Target file section followed by `(new)` declares the file as newly created.
  - The existence check on the file is skipped; the parent directory must exist (if absent, `new_target_dir_missing`).
  - If the file already exists, it is reported as `new_target_exists`.
  - symbol / import / `# Before:` checks run against an empty file.
  - Line-number citations that resolve to the target file are not checked.
  - A nonexistent target without `(new)` is `source_missing` as before.
- Names never reported as `symbol_missing` (when the symbol is absent from every `.py` file):
  - builtin names and dunder names;
  - lint rule codes (1-4 uppercase letters followed by 2-4 digits);
  - sibling procedure numbers (`_` followed by digits only);
  - chapter ids that match a filename prefix under `docs/`;
  - names appearing in a key position of config-type files (`config/`, `conf.d/`, `schemas/`, `deploy/`, `init.d/`, `pyproject.toml`, `tox.ini`). A mention inside a comment is not treated as a key.

## Module Docstring Checker

| File | Description |
|---|---|
| `check_docstrings.py` | Validates the docstring format of Python files under `scripts/`. Checks that an em-dash (U+2014) is present and that the form `scripts/<path> — description` is valid. It does **not** add or fix docstrings. Violations that predate the check are listed in `tools/check_docstrings_baseline.txt` (`<relpath>`, tab, issue kind): only new violations fail, and a baseline entry whose violation is gone is reported as stale and also fails. `--update-baseline` regenerates the file; `--no-baseline` reports everything; `--baseline PATH` selects another file. Runs as the pre-commit hook `check-docstrings` when `scripts/**/*.py`, this tool, or its baseline changes, and as a step of the CI `lint` job |

### Limitations of docstring-editing scripts

A script that adds or fixes docstrings by transforming source with regular expressions has these problems:

- **Line-number shift**: inserting a docstring shifts line numbers and breaks existing code.
- **UTF-8 corruption**: the byte sequence of the em-dash (U+2014) can be corrupted.
- **Mixed quoting**: `"""` and `""""""` end up mixed together.

Editing docstrings safely requires an approach based on the syntax tree from the `ast` module. The current implementation never **adds** docstrings; only **format validation** of existing docstrings is recommended.
