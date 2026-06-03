# rules/coding.md — Shared Coding Conventions

## Mandatory conventions

Enforced by ruff, mypy, and ast-grep. Do not violate.

| Rule | Detail |
|---|---|
| Line length | max 88 chars — enforced by `ruff format` |
| Comments and log output | English only |
| String formatting | f-strings preferred; plain literals when no variables |
| Import order | enforced by ruff `I` rules (isort-compatible) |
| Module addition | update copy list in `deploy/deploy.sh` |
| MCP server addition | add entry to `config/mcp_servers.toml [mcp_servers]` |

## Tool configuration (pyproject.toml)

**ruff:** `line-length = 88`, `select = ["E", "W", "F", "I", "UP"]`, `target-version = "py313"`
- `ignore = ["E501"]` — E501 not auto-fixable in string literals; `ruff format` enforces length in code

**mypy:** `python_version = "3.13"`, `files = ["scripts/"]`, `ignore_missing_imports = true`
- Pre-existing errors exist. Fix incrementally; do not suppress with `type: ignore` without justification.

**bandit:** `[tool.bandit]` — `skips = []`; do not add skips without justification

**tox:** defines four environments: `lint`, `typecheck`, `security`, `tests`

## Suppression governance

Every `# noqa`, `# type: ignore`, and `# nosec` requires an inline justification.
Suppressions without explanation are prohibited.

```bash
rg '# noqa' scripts/ | grep -v '# noqa:'        # noqa without rule code
rg '# type: ignore' scripts/ | grep -v '\['      # ignore without error code
rg '# nosec' scripts/ | grep -v ' — '           # nosec without comment
```

## Constraint checks (run before every commit)

```bash
# no bare except
ast-grep --pattern 'except: $$$' --lang python scripts/

# no print() in library modules
ast-grep --pattern 'print($$$)' --lang python scripts/
```

## Key library choices

- Use `orjson` (not stdlib `json`) for all JSON serialization — `orjson.dumps()` returns `bytes`; call `.decode()` when a `str` is required; use `option=orjson.OPT_SORT_KEYS` / `OPT_INDENT_2` instead of `sort_keys=True` / `indent=2`
- Use `httpx` (not `requests`) for HTTP — `httpx.Client` for sync, `httpx.AsyncClient` for async

## mypy note

`warn_unused_ignores = true` is set in `pyproject.toml` — any `# type: ignore` on a line where mypy finds no error is itself an error. `tests/` is also covered by pre-commit's mypy run.

## Prohibited behavior (all tasks)

- do not write comments or log messages in Japanese
- do not use `git add -A` or `git add .` — stage files individually
- do not commit with `--no-verify`
- do not add `# noqa` / `# type: ignore` / `# nosec` without an inline explanation
- do not add global ignores to `pyproject.toml` without justification
- do not suppress `lint-imports` violations without updating the contract definition
- do not commit `import ipdb`, temporary `structlog` debug calls, viztracer/tracemalloc instrumentation, or Sentry DSN
