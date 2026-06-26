# Implementation: Add source-type dedup and retention policies to memory subsystem

Steps covered: Plan 20260626-100126 — Steps 1-5

---

## Goal

Differentiate dedup thresholds and retention periods by source type (RULE/DECISION/FAILURE/CONVERSATION) in `DedupPolicy` (`enums.py`), `ingestion.py`, and `jsonl_store.py`.

---

## Scope

- **In scope**:
  - `scripts/agent/memory/enums.py`: `DedupPolicy` — add source-type thresholds
  - `scripts/agent/memory/ingestion.py`: dedup logic to use source-type threshold
  - `scripts/agent/memory/jsonl_store.py`: retention filter with source-type days
  - docs: `/memory prune` / `/memory rebuild` policy description
- **Out of scope**: JSONL canonical model replacement

---

## Assumptions

- `DedupPolicy` is in `enums.py`. May be a dataclass or Enum.
- Thresholds: RULE/DECISION → 0.98 (nearly identical to dedup); FAILURE → 0.90; CONVERSATION → 0.85.
- Retention: RULE/DECISION → unlimited; FAILURE → 180 days; CONVERSATION → 90 days.

---

## Implementation

### Target files
`scripts/agent/memory/enums.py`, `scripts/agent/memory/ingestion.py`, `scripts/agent/memory/jsonl_store.py`

### Procedure
1. Read the three files to understand current `DedupPolicy` and retention structures.
2. Step 1 (`enums.py`): Add `similarity_threshold` dict by source type:
   ```python
   DEDUP_THRESHOLDS: dict[str, float] = {
       "RULE": 0.98,
       "DECISION": 0.98,
       "FAILURE": 0.90,
       "CONVERSATION": 0.85,
   }
   RETENTION_DAYS: dict[str, int | None] = {
       "RULE": None,       # unlimited
       "DECISION": None,   # unlimited
       "FAILURE": 180,
       "CONVERSATION": 90,
   }
   ```
3. Step 2 (`ingestion.py`): In dedup check, look up `DEDUP_THRESHOLDS[entry.source_type]`.
4. Step 3 (`jsonl_store.py`): In retention filter, look up `RETENTION_DAYS[entry.source_type]`; skip retention check for `None`.
5. Step 4: Add docs update for `/memory prune` policy.
6. Step 5: Add tests for per-source-type dedup threshold behavior.

### Method
Config-driven dedup/retention. Additive change (new dict fields).

---

## Validation plan

- Run: `uv run pytest tests/agent/memory/ -x` — pass.
- Type: `mypy scripts/agent/memory/` — 0 errors.
- Pre-commit: `pre-commit run --all-files` — pass.
