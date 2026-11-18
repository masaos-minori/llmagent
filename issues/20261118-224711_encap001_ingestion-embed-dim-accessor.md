# Expose a public accessor for MemoryStore embed_dim instead of reaching into _embed_dim

## Priority
Low

## Summary
`MemoryIngestionService._persist_entry_with_embedding` reads the private attribute
`self._store._embed_dim` to forward the embedding dimension to `write_upsert`.
Replace that private access with a public accessor on `MemoryStore` so ingestion
does not depend on store internals.

## Background
`MemoryStore.__init__` stores the optional embedding dimension in a private field
`self._embed_dim` (`store.py`). `ingestion.py` forwards it on every persisted
entry via `write_upsert(entry, embedding=embedding, embed_dim=self._store._embed_dim)`.
The two classes live in different modules of the memory package, so this crosses a
module boundary through a private name.

## Problem
`ingestion.py` reaches into `MemoryStore._embed_dim`, a private implementation
detail. If `MemoryStore` renames the field, computes the dimension differently, or
moves it, ingestion breaks with an `AttributeError` at runtime. The dependency is
invisible in the public type contract of `MemoryStore`.

## Reason for Change
The private access is a latent coupling that the refactor made visible by placing
both classes in the same package with clear module boundaries. It has no runtime
effect today, but it invites future breakage and hides a real dependency.

## Implementation Intent
Add a small public property (for example `embed_dim`) on `MemoryStore` that
returns the stored dimension, and have `ingestion.py` read that public property
instead of `self._store._embed_dim`. Alternatively inject the dimension through
the service constructor. Preserve the current `None`-means-unvalidated behavior.

## Target Files or Areas
- `scripts/agent/memory/store.py`
- `scripts/agent/memory/ingestion.py`

## Required Changes
- Add a public accessor on `MemoryStore` for the embedding dimension.
- Update `ingestion.py` to read the public accessor instead of `_embed_dim`.
- Keep passing `None` when the dimension is unset so validation stays disabled.

## Constraints
- Behavior must be unchanged: `None` disables dimension validation, an int enables it.
- Do not change the `write_upsert` signature or the `add`/`upsert` write paths.
- Do not affect the manual-write path (`_persist_entry`).

## Acceptance Criteria
- No code in `ingestion.py` references `MemoryStore._embed_dim`.
- The public accessor returns the same value previously read from `_embed_dim`.
- Type checks pass with the accessor in place.

## Testing Expectations
- Run `tests/agent/memory/test_memory_store.py` and `tests/agent/memory/test_memory_layer.py`;
  confirm they still pass.
- Add a test asserting the public accessor mirrors the constructor dimension.
- `uv run mypy` and `uv run ruff check` on the touched files.

## Documentation Impact
None required.

## Out of Scope
- Changing how `embed_dim` is validated against embeddings.
- Refactoring the write transaction logic in `write_ops.py`.
- Any change to dedup or link behavior.

## Dependencies
- `N/A: none`

## Unresolved Questions
- Whether the dimension should instead be injected via the service constructor
  rather than read back from the store. `Needs confirmation`: decide the cleaner
  ownership between `MemoryStore` and `MemoryIngestionService`.

## AI Implementation Instruction
- Only touch `store.py` and `ingestion.py`.
- Preserve the `None`-disables-validation semantics exactly.
- Do not rename or change `write_upsert`/`add`.
- Run ruff, mypy, and the memory store/layer tests before finishing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-224711
- **Related target files**: scripts/agent/memory/store.py, scripts/agent/memory/ingestion.py
