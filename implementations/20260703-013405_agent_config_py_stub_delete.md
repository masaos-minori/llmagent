# Implementation: scripts/agent/config.py — Delete Re-export Stub

**Plan source:** `plans/20260702-202739_plan.md` (Phase 6)
**Target file:** `scripts/agent/config.py`

---

## Goal

Delete `scripts/agent/config.py` after confirming all callers have been updated to import directly from `agent.config_builders` or `agent.config_dataclasses`.

---

## Scope

**In:**
- Final grep to confirm no remaining references: `grep -R "from agent.config import|import agent.config" --include="*.py" /home/masaos/llmagent/ | grep -v ".venv"`
- Delete `scripts/agent/config.py`
- Run full validation suite

**Out:**
- Any logic changes to config builders or dataclasses

---

## Assumptions

1. All callers updated in Phase 2 (agent scripts) and Phase 2 (test files).
2. `uv run pytest` and `PYTHONPATH=scripts uv run lint-imports` are the definitive validation gates.

---

## Implementation

### Target file

`scripts/agent/config.py`

### Procedure

1. Run `grep -R "from agent.config import\|import agent.config" --include="*.py" /home/masaos/llmagent/ | grep -v ".venv"` — expect no output.
2. Delete the file: `rm scripts/agent/config.py`
3. Run full validation suite.

### Method

Bash for grep check and deletion.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Pre-delete check | `grep -R "from agent.config import" --include="*.py" scripts/ tests/ | grep -v .venv` | 0 matches |
| Lint | `uv run ruff check scripts/ tests/` | 0 new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Full suite | `uv run pytest` | All pass |
