# Implementation Procedure: Add Agent Documentation-to-Code Consistency Checks and Triage Current-Behavior Notes

Source plan: `plans/20260717-094227_plan.md`
Source requirement: `requires/20260716_17_require.md`

## Goal

Agent documentation gains the same class of automated, CI-enforced doc-vs-code consistency checks MCP documentation already has (broken internal links, removed-legacy-file references, slash-command drift, DB-schema drift where feasible, obsolete diagnostics references); two pre-existing broken CI/tooling paths discovered during planning are fixed as a prerequisite; and all 31 existing `Current behavior` notes across Agent/MCP docs are triaged into one of five explicit classifications.

## Scope

**In scope**
- New `tools/check_agent_docs_consistency.py`, mirroring `tools/check_mcp_docs_consistency.py`'s architecture (typed `Issue`/`DocFile` dataclasses, one function per check, `--skip` flag registry, ERROR/WARNING severity), implementing: broken internal Markdown link detection, removed-legacy-doc-file reference prohibition, slash-command drift (vs. `command_defs_list.py`'s `_COMMANDS`), best-effort DB-schema drift (vs. `schema_sql.py`), and obsolete diagnostics references (seeded from `docs/05_agent_90_inconsistencies_and_known_issues.md`).
- **Prerequisite fix 1**: `.github/workflows/mcp-docs-consistency.yml` and `.github/workflows/rag-docs-quality.yml` both invoke the non-existent path `scripts/checks/check_*_consistency.py` — correct both to `tools/check_*_consistency.py`.
- **Prerequisite fix 2**: `uv run check-mcp-docs` is currently non-functional (`ModuleNotFoundError`) because `pyproject.toml`'s `[tool.setuptools.packages.find]` scopes `where = ["scripts"]` only, excluding `tools/` — fix the package/entry-point configuration so both `check-mcp-docs` and the new `check-agent-docs` resolve.
- New `.github/workflows/agent-docs-consistency.yml`, modeled on the path-corrected `mcp-docs-consistency.yml`.
- New `pyproject.toml` `[project.scripts]` entry: `check-agent-docs = "check_agent_docs_consistency:main"`.
- Current-behavior triage: extract, classify, and act on all 31 notes across the 20 files containing them.
- Guidance addition (in `rules/coding.md` or a small new doc section) on how future `Current behavior` notes should state their classification.

**Out of scope**
- Rewriting the documentation set.
- Semantic verification of every paragraph.
- Automatically deleting `Current behavior` notes without a verification step.
- Resolving every implementation mismatch found during triage inline — file as tracked issues instead.
- Treating `05_agent_all.md` / `04_mcp_all.md` as real target files — confirmed these never existed in this repo's git history (Assumption 1); this plan targets the actual split doc files.
- A full, column-level DB schema documentation diff — scoped to "feasible-effort" per the source requirement.

## Assumptions

1. `05_agent_all.md` and `04_mcp_all.md` (the source requirement's stated target files) do not exist and have never existed in this repo's git history — confirmed via `find` and `git log --all --oneline`. The only references to these filenames anywhere are inside requirement documents themselves. This plan targets the real split files (`docs/05_agent_*.md`, `docs/04_mcp_*.md`).
2. `tools/check_docs_consistency.py` (441 lines, 10 checks, gates its RAG-specific checks on `filename.startswith("03_rag_")`) and `tools/check_mcp_docs_consistency.py` (809 lines, 12 checks) are the correct existing assets — neither currently does broken-link detection, command-drift, or DB-schema-drift checking; Agent docs today receive only 8 generic checks and nothing agent-specific.
3. `.github/workflows/mcp-docs-consistency.yml` and `rag-docs-quality.yml` reference `scripts/checks/check_*.py` — **confirmed broken** by direct local reproduction (`FileNotFoundError`); real files live at `tools/check_*.py`.
4. `uv run check-mcp-docs` **confirmed broken** (`ModuleNotFoundError: No module named 'check_mcp_docs_consistency'`) — `pyproject.toml`'s `[tool.setuptools.packages.find]` sets `where = ["scripts"]` only; `tools/` is outside the package path.
5. `scripts/agent/commands/command_defs_list.py`'s `_COMMANDS: list[CommandDef]` (20 entries) is the single source of truth for slash commands, per its own docstring.
6. `scripts/db/schema_sql.py` stores schema as raw SQL DDL template strings (no named table/column constants) — a doc-comparison script must regex-extract `CREATE TABLE`/`CREATE VIRTUAL TABLE` names, with no cleaner extraction path available.
7. The 31 `Current behavior` notes have no existing ID/severity metadata — triage requires manually reading each one; no prior tracked classification exists to reuse (confirmed: no "triage"/"トリアージ" references in any `*_90_inconsistencies_and_known_issues*.md` file).
8. `check_mcp_docs_consistency.py`'s design (typed dataclasses, `--skip` registry, single `discover_md_files()` pass, ERROR/WARNING severity split) is the better pattern to mirror, vs. `check_docs_consistency.py`'s plain-string-list design.

## Implementation

### Target file

Primary (new): `tools/check_agent_docs_consistency.py`. Secondary: `.github/workflows/mcp-docs-consistency.yml`, `.github/workflows/rag-docs-quality.yml`, `.github/workflows/agent-docs-consistency.yml` (new), `pyproject.toml`, `docs/05_agent_*.md` / `docs/04_mcp_*.md` (triage edits), `rules/coding.md` (guidance addition).

### Procedure

1. **Prerequisite verification**: re-confirm the `scripts/checks/` vs `tools/` path break and the `check-mcp-docs` package-resolution break (both already confirmed during planning — see Assumptions 3-4). Prototype the `schema_sql.py` regex `CREATE TABLE` extractor against the actual file content and manually verify its output against a hand-read table list.
2. **Fix the broken CI paths**: update `.github/workflows/mcp-docs-consistency.yml` and `.github/workflows/rag-docs-quality.yml` to invoke `tools/check_*_consistency.py`.
3. **Fix the broken `check-mcp-docs` package resolution**: add `tools` to `pyproject.toml`'s `[tool.setuptools.packages.find]` `where` list (or relocate both checkers under `scripts/checks/` and update all three references — CI workflows, pre-commit hook, entry point — consistently in one direction); re-run `uv run check-mcp-docs` locally to confirm it resolves and executes.
4. **Build `tools/check_agent_docs_consistency.py`**:
   - Broken-link detection: resolve `[text](path)` / `[text](#anchor)` references against actual files/headings under `docs/05_agent_*.md`.
   - Removed-legacy-file-reference prohibition: flag references to any removed/renamed doc file.
   - Slash-command drift: extract command names from `CommandDef(...)` calls in `command_defs_list.py`; flag doc-referenced `/command` not in `_COMMANDS`, or `_COMMANDS` entries with no doc mention.
   - DB-schema drift (best-effort): regex-extract `CREATE TABLE`/`CREATE VIRTUAL TABLE` names from `schema_sql.py`'s template strings per Step 1's verified extractor; cross-check against table names in `docs/90_shared_04_*` and `docs/05_agent_09_*`.
   - Obsolete diagnostics references: seed from `docs/05_agent_90_inconsistencies_and_known_issues.md`.
   - Wire each check behind a `--skip <name>` flag; severity: broken links and removed-file references are ERROR; command/DB-schema drift and diagnostics references are WARNING initially (staged rollout, promotable to ERROR later); ensure error output includes file path, section/line, and offending reference.
5. **Add `check-agent-docs` to `pyproject.toml`** (using Step 3's corrected package-resolution mechanism) and wire `.github/workflows/agent-docs-consistency.yml`, triggered on `docs/05_agent_*.md` + the new checker file.
6. **Run the new checker against the current doc set** and fix any real findings (broken links, stale command references, etc.) before wiring it as a required CI check.
7. **Current-behavior triage**: read all 31 notes across the 20 files containing them (heading variants: `### Current behavior (...)`, `**Current behavior:**`, `> **Current behavior**:`, `### 実装上の補足（Current behavior）`, `**現在の動作:**`); produce a triage table (file, section, summary, classification); act per classification:
   - *Accepted current specification* → reword to remove "Current behavior" framing, merge into normal prose.
   - *Implementation fix required* → file a GitHub-issue-template Markdown under `issues/`, cross-reference from the note.
   - *Documentation fix required* → fix directly in this pass, remove the note.
   - *Issue already tracked* → cross-reference the existing entry, remove the redundant note.
   - *Obsolete and removable* → verify against current code, then delete.
8. **Add future-note guidance** to `rules/coding.md` (or a small new doc section) describing the five-category classification scheme.
9. **Deployment/verification**: no service restart needed; run the full validation sequence and confirm both fixed CI workflows, the fixed `check-mcp-docs` entry point, and the new workflow all pass.

### Method

- New checker built as a direct architectural mirror of `tools/check_mcp_docs_consistency.py` — same dataclass shapes, same `--skip` registry pattern, same severity model — not a from-scratch design.
- CI/packaging fixes are small, targeted path/config corrections, not refactors.
- Triage is manual per-note reading and classification; no automation attempted for the classification step itself (only extraction of note locations is mechanical).

### Details

- Do not implement a full schema-diff for the DB-schema-drift check — best-effort regex extraction only, with a documented fallback to a hand-maintained table-name allowlist if extraction precision is too low (per UNK-04's resolution path).
- Do not wire the new checker as an ERROR-blocking CI gate for command-drift/DB-schema-drift on first rollout — start these two checks at WARNING severity to avoid an immediate false-positive-driven CI failure storm.
- Do not delete a `Current behavior` note without first verifying against current code that the discrepancy it describes no longer exists.
- Ambiguous triage classifications should default to "implementation fix required" (file an issue) rather than "accepted," since an unnecessary issue is cheaper to undo than silently accepting a real discrepancy.
- Confirm whether `tools/` is in `deploy/deploy.sh`'s scope at all (likely not, since it's dev/CI tooling) before assuming zero deploy impact.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| New checker runs clean | `python tools/check_agent_docs_consistency.py` (or `uv run check-agent-docs` once wired) | 0 ERROR-severity issues against current docs after Step 6's fixes |
| Existing MCP checker entry point now resolves | `uv run check-mcp-docs` | executes successfully (currently fails with `ModuleNotFoundError`) |
| Fixed CI paths actually resolve | `python tools/check_docs_consistency.py`, `python tools/check_mcp_docs_consistency.py` | both execute without `FileNotFoundError` |
| No broken internal links | new checker's link-check function | 0 broken links across `docs/05_agent_*.md` |
| Command-list drift | new checker's command-drift function | every `/command` mentioned in docs exists in `_COMMANDS`, and vice versa (or each mismatch is a documented exception) |
| Triage completeness | manual review of the triage table | all 31 notes have an assigned classification; none left "TBD" |
| Pre-commit | `uv run pre-commit run --all-files` | pass (existing `docs-consistency` hook unaffected) |
| CI | push a branch and observe `agent-docs-consistency.yml`, `mcp-docs-consistency.yml`, `rag-docs-quality.yml` runs | all three pass |
