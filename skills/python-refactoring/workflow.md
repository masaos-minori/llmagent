# Python Refactoring — Detailed Workflow

## Phase 1: Dependency Mapping

**Gate: blast radius documented; no unknown affected modules**

#### pydeps — import graph

```bash
cd scripts && pydeps <module> --no-output --show-deps
pydeps agent_repl --no-output --show-deps --max-bacon=3
pydeps rag_utils --no-output --show-deps
```

Document every module that imports the target symbol. This is the blast radius.

#### rg — symbol usages

```bash
rg "def <symbol>" scripts/             # definition sites
rg "<symbol>" scripts/                 # all usages (including imports)
rg "from <module> import" scripts/     # all importers of the module
rg "import <module>" scripts/          # direct imports
```

#### deploy.sh impact

```bash
grep "<old_module_name>" deploy/deploy.sh   # does a cp line need to change?
```

Include in the Phase 1 output table:

| File | Change | Blast radius | deploy.sh impact |
|---|---|---|---|
| `scripts/<module>.py` | rename | ... | rename cp line |
| `scripts/<new>.py` | create | ... | add cp line |
| `scripts/<old>.py` | delete | ... | remove cp line |

#### ast-grep — structural usages

```bash
ast-grep --pattern '$OBJ.<method>($$$)' --lang python scripts/
ast-grep --pattern 'class $NAME(<ParentClass>): $$$' --lang python scripts/
ast-grep --pattern 'def <symbol>($$$): $$$' --lang python scripts/
```

#### import-linter — boundary contracts

```bash
lint-imports
cat .importlinter
```

Identify which contracts are affected by the planned refactor.
If the refactor changes a module boundary, plan the contract update as part of Phase 3.

**Phase 1 output**: a table of affected files, symbols, and contract changes required.

---

## Phase 2: Behavior Lock

**Gate: coverage ≥ 80%; 0 surviving mutants on refactored paths; diff-cover baseline recorded**

#### pytest-cov — coverage baseline

```bash
coverage run -m pytest tests/
coverage report --include="scripts/<module>.py"
coverage xml
diff-cover coverage.xml --compare-branch=main   # record baseline
```

If coverage is below 80%: write characterization tests for the uncovered paths before proceeding.

#### hypothesis — property-based invariants

```python
from hypothesis import given, settings
from hypothesis import strategies as st

@given(st.text())
@settings(max_examples=500)
def test_normalize_does_not_change_type(text):
    from rag_utils import normalize_unicode
    result = normalize_unicode(text)
    assert isinstance(result, str)
```

Write property tests for parsers, normalizers, and data transformers that are in the refactor scope.

#### mutmut — test suite strength

```bash
mutmut run --paths-to-mutate scripts/<module>.py
mutmut results
mutmut show <id>
```

If surviving mutants > 0: add tests that kill them before proceeding.
Do not proceed to Phase 3 with surviving mutants on the refactored path.

---

## Phase 3: Semantic Transformation

**Gate: ruff clean; transformed files parse; no old symbol names remain**

#### LibCST — symbol renaming

```python
import libcst as cst
import pathlib

class RenameClass(cst.CSTTransformer):
    def leave_Name(
        self, original_node: cst.Name, updated_node: cst.Name
    ) -> cst.Name:
        if updated_node.value == "OldName":
            return updated_node.with_changes(value="NewName")
        return updated_node

for path in pathlib.Path("scripts").glob("*.py"):
    source = path.read_text()
    tree = cst.parse_module(source)
    new_tree = tree.visit(RenameClass())
    if new_tree.code != source:
        path.write_text(new_tree.code)
```

#### bowler — query-based bulk refactoring

```bash
# dry run first — always
bowler rename_func old_func_name new_func_name --write --dry-run
# apply
bowler rename_func old_func_name new_func_name --write
```

After any transform:

```bash
python3 -m compileall -q scripts/        # syntax check
ruff format scripts/
ruff check scripts/ --fix
```

Verify no old symbol names remain:

```bash
rg "OldName" scripts/
ast-grep --pattern 'OldName' --lang python scripts/
```

---

## Phase 4: Semantic Validation

**Gate: mypy error count unchanged; pyright clean; characterization tests pass**

#### mypy — primary type check

```bash
mypy scripts/ --show-error-codes
```

Record the error count **before** the refactor (Phase 2) and compare after.
The error count must not increase. New errors introduced by the refactor must be fixed.

#### pyright — cross-validation

```bash
pyright scripts/
```

#### ruff — final lint

```bash
ruff check scripts/
ruff format --check scripts/
```

#### characterization tests

```bash
pytest tests/ -v
pytest tests/test_<module>.py -v
```

All tests that existed in Phase 2 must still pass. No new failures are acceptable.

---

## Phase 5: Incremental Migration

**Gate: every commit passes pytest + ruff + mypy; no broken intermediate state**

#### One commit per logical step

Each commit must be independently revertable. Never bundle a rename with a behavior change.

Preferred commit order:

1. add new symbol (new function/class) alongside old one
2. migrate call sites one module at a time
3. remove old symbol after all call sites are migrated
4. update import-linter contracts
5. update deploy.sh if a module was added, removed, or renamed

#### lazygit — hunk-level staging

```bash
lazygit   # stage individual hunks; discard unrelated changes
```

Use lazygit to stage only the lines belonging to the current step.

#### verify each step

```bash
pytest tests/ -x -q
ruff check scripts/
mypy scripts/
```

#### Failure recovery

If a step fails CI:
1. Do NOT use `--no-verify` to bypass
2. `git revert HEAD` to undo the broken commit cleanly
3. Diagnose: `ruff check scripts/` + `mypy scripts/` + `pytest tests/ -x`
4. Fix the root cause and create a new commit

---

## Phase 6: CI Gate

**Gate: pre-commit passes; lint-imports passes; diff-cover ≥ 90%**

```bash
pre-commit run --all-files
lint-imports
diff-cover coverage.xml --compare-branch=main --fail-under=90
```

If `pre-commit` fails: fix the specific hook that failed, do not use `--no-verify`.

Final review:

```bash
git log --oneline -10
git diff main...HEAD -- scripts/
rg "OldName\|old_func\|OldClass" scripts/   # confirm no old symbols remain
```

---

## Special cases

### Refactoring tool_executor.py or agent_repl.py

If the refactor touches `tool_executor.py` or MCP routing logic in `agent_repl.py`:
- check if `_MCP_SERVICE_MAP` keys or server names change: `rg "_MCP_SERVICE_MAP" scripts/agent_repl.py`
- update the map if server keys change
- verify with `/mcp` in the agent REPL after deployment
- add this check to the Phase 1 blast radius table

### Refactoring that creates or removes a module

When a module is added or removed, compose with the `deploy` skill:
- add or remove the `cp` line in `deploy/deploy.sh`
- update `routing.md` if the module maps to a doc reference
- update `CLAUDE.md` Architecture section

---

## Completion checklist

- blast radius table documented
- characterization tests written; coverage ≥ 80%
- 0 surviving mutants on refactored paths
- `ruff check scripts/` — 0 errors
- `mypy scripts/` — error count not increased
- `lint-imports` — passes or contracts updated
- `diff-cover` — ≥ 90% on changed lines
- `pre-commit run --all-files` — passes
- all commits are bisect-safe (each passes tests independently)
- no old symbol names remain in `scripts/`

---

## Prohibited behavior

- do not refactor and add features in the same commit
- do not use regex for symbol renaming — use LibCST or bowler
- do not suppress lint-imports without updating the contract definition
- do not proceed to Phase 3 with surviving mutants on the refactored path
- do not commit with `--no-verify`
- do not bundle multiple rename steps into a single commit
