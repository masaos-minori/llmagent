## Goal

Make `scripts/rag/models_result.py` the single home of `SearchDiagnostics`: derive `degraded` from the counters, add `to_dict()`, drop the never-set `fallback_reason`, remove the `PipelineDiagnostics` re-export, and type `RagSearchResult.hits` as `list[RankedHit]` (REQ-001, REQ-004 / AC-1, AC-4).

## Scope
**Release unit**: single-diagnostics-model

## Assumptions
- `corpus_generation` (models_result.py:90-91) is removed by `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md`; this procedure leaves that field and its `RAGCORPUS001` comment untouched and runs after that Plan lands.
- No importer takes `PipelineDiagnostics` from `models_result` — `pipeline.py` and `test_diagnostics.py` import it from `rag.diagnostics` — so the re-export block is dead.
- `RankedHit` lives in `scripts/shared/types.py` and is importable under the layer contract; annotations are strings under `from __future__ import annotations`, so the import is `TYPE_CHECKING`.
- `degraded` derives as `embed_failed > 0 or fts_errors > 0`, identical to the former `diagnostics.py` computation, so behavior is unchanged for every current writer.
- `rmcompat007` sweeps the `RAGCORPUS001` comment after this Plan; do not touch it here.

## Design decisions
- `degraded` becomes an `@property` over the two counters instead of a stored field, removing the stored-versus-derived mismatch; the dataclass keeps `embed_ok`, `embed_failed`, `fts_errors` as fields.
- Keep `SearchDiagnostics` in `models_result.py`; moving it to `diagnostics.py` would cycle (`rag.stage` -> `rag.models_result` and `rag.diagnostics` -> `rag.stage`).

## Alternatives considered
- Adding `to_dict()` to the model versus building the dict in `pipeline.py`: the model owns its shape, matching the surviving class's intended contract.
- Typing `hits` as `list[RankedHit]` now versus later: `RankedHit` is importable and the field has no live constructor in scope, so the narrowing is safe now.

## Implementation
### Target file
`scripts/rag/models_result.py`

### Procedure
1. Convert `SearchDiagnostics.degraded` to a derived property and add `to_dict()`.
2. Drop the `fallback_reason` field.
3. Remove the `PipelineDiagnostics` re-export block.
4. Type `RagSearchResult.hits` as `list[RankedHit]`.

### Method
Edit `scripts/rag/models_result.py` in place; no new module symbols except the property and method on the existing class.

### Details
- Under `@dataclass(frozen=True) class SearchDiagnostics`: delete the `degraded: bool = False` field and the `fallback_reason: str | None = None` field; add after the fields:
  ```python
  @property
  def degraded(self) -> bool:
      """True when any embedding or FTS error occurred during the run."""
      return self.embed_failed > 0 or self.fts_errors > 0

  def to_dict(self) -> dict[str, object]:
      return {
          "embed_ok": self.embed_ok,
          "embed_failed": self.embed_failed,
          "fts_errors": self.fts_errors,
          "degraded": self.degraded,
      }
  ```
  Keep the `corpus_generation` field and its `RAGCORPUS001` comment unchanged (removed by rmcompat003).
- Remove the `TYPE_CHECKING` block that imports `PipelineDiagnostics` (the `# noqa: F401` re-export); if `TYPE_CHECKING` then has no use, drop the guard and remove `Any` from the `typing` import only if `Any` is otherwise unused (verify before removing).
- In `RagSearchResult`, change `hits: list[Any]  # list[RankedHit] — typed after Phase 3-1` to `hits: list[RankedHit]`.
- Add `RankedHit` to the `TYPE_CHECKING` import block: `from shared.types import RankedHit`.

## Compatibility considerations
- `stage.py`, `stage_lifecycle.py`, `types.py`, `augment.py`, `stages/search.py`, `pipeline.py`, and tests keep importing `SearchDiagnostics` from `models_result`; `degraded` stays readable as an attribute (now a property).
- `stages/search.py` currently passes `degraded=` when constructing `SearchDiagnostics`; once `degraded` is a property it must not be passed to the constructor. That removal belongs to the `stages/search.py` procedure of this Plan; verify `search.py` still constructs the class with only the three counters.

## Security considerations
N/A: no input handling or trust boundary change.

## Rollback considerations
Revert the commit; the property and `to_dict()` are additive and the field removal is inside the release unit.

## Validation plan
- `uv run pytest tests/rag/test_diagnostics.py tests/rag/test_rag_stages.py` passes with `degraded` derived.
- `rg -n "class SearchDiagnostics" scripts/rag` returns exactly one match in `models_result.py`; `rg -n "fallback_reason" scripts/rag/models_result.py` returns nothing (AC-1).
- `rg -n "re-exported|Phase 3-1|noqa: F401" scripts/rag/models_result.py` returns nothing; `RagSearchResult.hits` reads `list[RankedHit]` (AC-4).
- Full sequence: `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria
`degraded` is a derived property, `to_dict()` exists, `fallback_reason` is gone, the re-export block and `Phase 3-1` comment are removed, and `RagSearchResult.hits` is `list[RankedHit]`; the AC-1/AC-4 searches match and the sequence passes.

## Out of Scope
`corpus_generation` (rmcompat003), the second `SearchDiagnostics` in `diagnostics.py` (this document's sibling), the `get_diagnostics()` rewrite (sibling), and comment sweeping (rmcompat007).

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
- **Requirement ID**: REQ-001 (one `SearchDiagnostics` with derived `degraded`, no never-set field) and REQ-004 (re-export removed, `RagSearchResult.hits` typed)
- **Source issue**: issues/20261110-170709_rmcompat002_rag-diagnostics-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120425_rmcompat002_rag-diagnostics-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-070042
- **Related target files**: scripts/rag/models_result.py
