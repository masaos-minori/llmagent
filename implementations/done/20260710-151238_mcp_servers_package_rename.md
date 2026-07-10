# Implementation: Rename `scripts/mcp` to `scripts/mcp_servers` (Phase 1)

## Goal

Eliminate the package-name collision between this project's own `mcp` package (`scripts/mcp/`) and the PyPI Model Context Protocol SDK (`mcp`, transitively installed via the dev dependency `semgrep`), which causes `ModuleNotFoundError: No module named 'mcp.audit'` when any `scripts/mcp/<name>/server.py` is launched standalone in the dev venv.

## Scope

**In:**
- `git mv scripts/mcp scripts/mcp_servers` (directory rename, preserves history)
- Rewrite `from mcp.` / `import mcp` in all affected `.py` files to `from mcp_servers.` / `import mcp_servers`
- Update the 10 `app_module = "mcp.<name>.server:app"` class attributes to `"mcp_servers.<name>.server:app"`
- Update the 10 `[mcp_servers.*].cmd` entries in `config/agent.toml` that reference `scripts/mcp/...` paths, to `scripts/mcp_servers/...`
- Update `.importlinter`: `root_packages` and all 5 contracts (`shared-is-leaf`, `db-only-uses-shared`, `rag-no-agent-or-mcp`, `mcp-no-agent`, `eventbus-is-isolated`) that reference `mcp`
- Update `AGENTS.md`'s layer-contract note (`mcp → db, shared`) and any other `mcp/` references in its module list
- Update code references inside `docs/04_mcp_*.md` (module paths, `app_module` examples) — file names themselves stay `04_mcp_*.md` (the doc-set naming convention is independent of the package name)

**Out:**
- No behavior change to any server's runtime logic — this is a pure rename plus mechanical import rewrite
- `pyproject.toml`'s `[tool.setuptools.packages.find] where = ["scripts"]` — no change needed; directory auto-discovery already covers the renamed path
- Removing/isolating `semgrep` as an alternative fix — explicitly out of scope per the plan (rename is the chosen permanent fix)

## Assumptions

1. `shared/config_loader.py::ConfigLoader.restrict_to`'s config directory resolution is an absolute physical path (`Path(__file__).resolve().parent.parent.parent / "config"`), not cwd-relative — confirmed in the plan's own investigation; the rename requires no config-loader changes.
2. The production venv (`/opt/llm/venv`, `uv sync --system-certs`, no dev group) does not install `semgrep` or the official `mcp` SDK, so the name collision is currently dev-venv-only — this rename does not change production runtime behavior, only fixes local dev standalone-launch capability.
3. Exact count of files requiring `from mcp.`/`import mcp` rewrites: 97 (measured via `grep -rl "^from mcp\.\|^import mcp\b\|^from mcp import\| from mcp\.\| import mcp\b" scripts/ tests/ --include="*.py"` at planning time); the plan's own count (94) was a slightly earlier measurement — re-run the grep at implementation time as the authoritative count, since file counts can drift.
4. `.importlinter` contains exactly 5 contracts, all referencing `mcp` in `root_packages` and/or `source_modules`/`forbidden_modules` (confirmed: `shared-is-leaf`, `db-only-uses-shared`, `rag-no-agent-or-mcp`, `mcp-no-agent`, `eventbus-is-isolated`).

## Implementation

### Target file

1. `scripts/mcp/` → `scripts/mcp_servers/` (directory, ~97 files)
2. `config/agent.toml`
3. `.importlinter`
4. `AGENTS.md`
5. `docs/04_mcp_*.md` (code-reference sections only)

### Procedure

1. `git mv scripts/mcp scripts/mcp_servers` — preserves file history for every moved file in a single rename commit.
2. Use `libcst` (per `skills/python-refactoring`) to mechanically rewrite import statements across the moved tree and all external callers (`tests/`, any `scripts/agent/` or `scripts/shared/` file importing `mcp.*`):
   ```python
   import libcst as cst
   import libcst.matchers as m

   class RenameMcpImport(cst.CSTTransformer):
       def leave_ImportFrom(self, original_node, updated_node):
           if updated_node.module and m.matches(updated_node.module, m.Attribute(value=m.Name("mcp")) | m.Name("mcp")):
               # rewrite `mcp` / `mcp.xxx` module path to `mcp_servers` / `mcp_servers.xxx`
               ...
           return updated_node
       def leave_Import(self, original_node, updated_node):
           # rewrite `import mcp` / `import mcp.xxx as yyy`
           ...
           return updated_node
   ```
   Run against every file returned by `grep -rl "^from mcp\.\|^import mcp\b" scripts/ tests/ --include="*.py"`, then `uv run ruff format` + `uv run ruff check --fix` on the touched set.
3. `grep -rln 'app_module = "mcp\.' scripts/` → for each of the 10 matches, replace `"mcp.<name>.server:app"` with `"mcp_servers.<name>.server:app"`.
4. `grep -n 'scripts/mcp/' config/agent.toml` → for each of the 10 `cmd` entries, replace `scripts/mcp/` with `scripts/mcp_servers/`.
5. In `.importlinter`, replace `mcp` with `mcp_servers` in `root_packages` and in every contract's `source_modules`/`forbidden_modules` list (5 contracts).
6. In `AGENTS.md`, update the layer-contract line `mcp    → db, shared` to `mcp_servers → db, shared` and any other `mcp/` path references in the module list.
7. In each `docs/04_mcp_*.md` file, update code-reference snippets (`app_module = "mcp...."`, `from mcp.xxx import ...` examples) to the new package name — the files themselves keep their `04_mcp_*.md` names since that numbering reflects the documentation-set convention, not the Python package name.
8. Run `PYTHONPATH=scripts uv run lint-imports` — expect 0 violations under the renamed contracts.
9. Run `grep -rn "\bmcp\." scripts/ tests/ config/agent.toml .importlinter AGENTS.md --include="*.py" --include="*.toml" --include="*.md" | grep -v "mcp_servers\|mcp_pipeline\|rag_pipeline"` and manually triage remaining hits — confirm no stray unrewritten reference survives.

### Method

Mechanical rename + CST-based bulk import rewrite, following the `python-refactoring` skill's toolchain (format → lint → type → architecture → security → tests). No new abstractions; pure identifier substitution across the codebase.

### Details

- `libcst` is preferred over plain regex/sed because it parses the AST and can distinguish `import mcp` (the local package) from unrelated identifiers containing the substring `mcp` (e.g., `rag_pipeline`, `mcp_launcher` itself once introduced in Phase 2) — a blind text substitution would risk corrupting unrelated strings.
- The rename commit should be kept as "pure rename + mechanical replace" only (per the plan's own risk mitigation) — no functional changes (like the Phase 2 launcher) should land in the same commit, to keep `git blame`/review tractable.
- `docs/04_mcp_*.md` filenames intentionally do not change — only their code-reference content does. This avoids an unnecessary large-scale doc-file rename cascading from a Python package rename.

## Validation plan

```bash
git mv scripts/mcp scripts/mcp_servers
uv run ruff format scripts/mcp_servers tests/
uv run ruff check scripts/mcp_servers tests/ --fix
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
grep -rn 'app_module = "mcp\.' scripts/                 # expect no output
grep -n 'scripts/mcp/' config/agent.toml                 # expect no output
grep -c "mcp_servers" .importlinter                      # expect >= 6 (root_packages + 5 contracts)
uv run pytest tests/ -x -q
```

Expected outcome: `lint-imports` passes under the renamed contracts, no stray `scripts/mcp/` or `"mcp.<name>.server:app"` references remain, and the full test suite has no new failures caused by the rename.
