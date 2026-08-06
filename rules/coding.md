# rules/coding.md — Shared Coding Conventions

## Mandatory conventions

Enforced by ruff, mypy, and ast-grep. Do not violate.

| Rule | Detail |
|---|---|
| Line length | max 120 chars — enforced by `ruff format` |
| Comments and log output | English only |
| String formatting | f-strings preferred; plain literals when no variables |
| Import order | enforced by ruff `I` rules (isort-compatible) |
| Module addition | update copy list in `deploy/deploy.sh` |
| MCP server addition | create `config/<key>_mcp_server.toml` with app config and `[mcp_servers.<key>]` transport section |

## Tool configuration (pyproject.toml)

**ruff:** `line-length = 120`, `select = ["E", "W", "F", "I", "UP"]`, `target-version = "py313"`
- `ignore = ["E501"]` — E501 not auto-fixable in string literals; `ruff format` enforces length in code
- `RUF100` (unused-noqa) intentionally deferred — 224 findings measured (see
  `plans/done/20260806-134805_plan.md`); spans rule codes beyond `BLE001`/`PLC0415`,
  out of scope for this increment.

**mypy:** `python_version = "3.13"`, `files = ["scripts/"]`, `ignore_missing_imports = true`
- Pre-existing errors exist. Fix incrementally; do not suppress with `type: ignore` without justification.

**bandit:** `[tool.bandit]` — `skips = []`; do not add skips without justification

**tox:** defines four environments: `lint`, `typecheck`, `security`, `tests`

## Suppression governance

Every `# noqa`, `# type: ignore`, and `# nosec` requires an inline justification.
Suppressions without explanation are prohibited. The primary enforcement mechanism is
the automated `tools/check_suppression_justification.py` check, wired into
`.pre-commit-config.yaml`'s `check-suppression-justification` hook. The `rg` one-liners
below are a secondary, human-readable illustration for manually spot-checking a specific
file — not the sole enforcement mechanism.

```bash
rg '# noqa' scripts/ | grep -v '# noqa:.*—'      # noqa without rule code or justification
rg '# type: ignore' scripts/ | grep -v '\[.*—'    # ignore without error code or justification
rg '# nosec' scripts/ | grep -v ' — '             # nosec without comment
```

`pyproject.toml`'s `[tool.ruff.lint] select` currently includes `BLE001` (active).
`PLC0415` (import-outside-top-level) is an intentionally-excluded exception — see the
inline comment above `ignore = ["E501"]` in `pyproject.toml` and
`plans/done/20260806-133908_plan.md` for the measured evidence (~1193 net-new findings).

## Constraint checks (run before every commit)

```bash
# no bare except
ast-grep --pattern 'except: $$$' --lang python scripts/

# no print() in library modules
ast-grep --pattern 'print($$$)' --lang python scripts/

# no json.load() outside config_loader.py (see Key library choices — use orjson)
ast-grep --pattern 'json.load($$$)' --lang python scripts/ | grep -v config_loader.py
```

## Bandit priority findings

Must resolve before merge:

| Code | Issue | Fix |
|---|---|---|
| B105/B106 | Hardcoded password/token | Move to env/conf.d |
| B301/B302 | Pickle deserialization | Replace with JSON or Pydantic |
| B501/B502 | TLS verification disabled | Never in production |
| B608 | SQL injection in f-string query | Parameterized queries |
| B404 | subprocess import | Acceptable; document why |
| B603 | subprocess without shell=True | Preferred; document if shell=True needed |

If a finding is a false positive, suppress with an inline justification (see Suppression
governance above):

```python
result = subprocess.run(cmd)  # nosec B603 — cmd is a validated static list, no user input
```

## Key library choices

- Use `orjson` (not stdlib `json`) for all JSON serialization — `orjson.dumps()` returns `bytes`; call `.decode()` when a `str` is required; use `option=orjson.OPT_SORT_KEYS` / `OPT_INDENT_2` instead of `sort_keys=True` / `indent=2`
- Use `httpx` (not `requests`) for HTTP — `httpx.Client` for sync, `httpx.AsyncClient` for async

## mypy note

`warn_unused_ignores = true` is set in `pyproject.toml` — any `# type: ignore` on a line where mypy finds no error is itself an error. `tests/` is also covered by pre-commit's mypy run.

## Documentation notes — "Current behavior" classification

When a `docs/*.md` note describes a gap between what a reader might expect
and what the code actually does, classify it into exactly one of these five
categories before writing it (do not use unlabeled "Current behavior" /
"現在の動作" framing as a catch-all):

| Classification | Action |
|---|---|
| Accepted current specification | The described behavior is correct and intentional. Write it as plain prose in the normal section — no special heading/framing, no "Current behavior" label. |
| Implementation fix required | The code has a real bug. File a Markdown issue under `issues/` (see existing files for the format), cross-reference it from the doc, and do not silently patch the doc to match the bug. |
| Documentation fix required | The doc itself is wrong (stale example, wrong command name, wrong file reference). Fix the doc directly; remove the note once the surrounding text is accurate. |
| Issue already tracked | The discrepancy is already filed. Cross-reference the existing entry; remove the redundant inline note. |
| Obsolete and removable | The discrepancy no longer exists (verify against current code first). Delete the note. |

Ambiguous cases default to "Implementation fix required" (file an issue) —
an unnecessary issue is cheaper to undo than silently accepting a real
discrepancy. Never delete a note without first verifying against current
code that the discrepancy it describes no longer applies.

## Prohibited behavior (all tasks)

- do not write comments or log messages in Japanese
- do not use `git add -A` or `git add .` — stage files individually
- do not commit with `--no-verify`
- do not add `# noqa` / `# type: ignore` / `# nosec` without an inline explanation
- do not add global ignores to `pyproject.toml` without justification
- do not suppress `lint-imports` violations without updating the contract definition
- do not commit `import ipdb`, temporary `structlog` debug calls, viztracer/tracemalloc instrumentation, or Sentry DSN
