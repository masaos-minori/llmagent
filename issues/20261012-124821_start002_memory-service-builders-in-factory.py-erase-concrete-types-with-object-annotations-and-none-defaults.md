# Memory-service builders in factory.py erase concrete types with object annotations and None defaults

## Priority
Low

## Summary
The memory-service builder helpers in `factory.py` (`_build_retriever`, `_build_embedding_client`,
`_build_jsonl_store`, `_build_injection_service`, `_build_ingestion_service`) annotate their
object arguments as `object` and give some of them a `= None` default. `mypy` passes, but the
annotations erase the concrete types (`EmbeddingClient`, `JsonlMemoryStore`, `Retriever`, etc.)
and invite passing `None` where a real instance is required. Restore the concrete parameter types.

## Background
`_build_memory_services` constructs `MemoryServices` by calling a chain of builder helpers.
Each helper receives a previously-built service instance. The builders were typed as `object`
with `None` defaults rather than the concrete class.

## Problem
`object` accepts any value including `None` (the `= None` defaults type-check under the current
mypy settings), so a caller can pass `None` and the error surfaces later as an
`AttributeError` deep in a builder or service. The concrete types are recoverable from the
callers but are not enforced at the boundary, which is exactly where a wrong argument would
first be rejected.

## Reason for Change
Builder boundaries are the cheapest place to catch a wrong argument. Erasing the types moves
that failure deeper and makes the signatures unreadable (`object` says nothing about what the
argument is).

## Implementation Intent
Replace the `object` annotations with the concrete types imported from the memory package
(`EmbeddingClient`, `HybridRetriever`/`Retriever`, `JsonlMemoryStore`, the policy/service
classes). Remove the `= None` defaults where a real instance is always supplied; keep a `None`
default only where a builder genuinely supports an optional dependency, and type it
`X | None`. Do not change call order or behavior.

## Target Files or Areas
- `scripts/agent/factory.py` (memory builder helpers)
- `scripts/agent/memory/*` — read only, to name the concrete types

## Required Changes
- Annotate each object-typed parameter with its concrete memory type.
- Drop the `= None` defaults that are never used as `None` by callers; type as `X | None`
  only where optional is a real contract.
- Keep the generic `type[T]` constructor parameters as-is.

## Constraints
- `mypy` must remain clean (it currently passes).
- Do not change `_build_memory_services` call sites or runtime behavior.
- Preserve the lazy imports already used inside `_build_memory_services`.

## Acceptance Criteria
- No `object` annotation remains on a memory-service argument that has a concrete type.
- `mypy scripts/agent/factory.py` passes.
- No behavioral change; existing memory tests pass.

## Testing Expectations
- `mypy` on `factory.py`.
- `tests/agent/` memory tests (existing) pass unchanged.
- `ruff check` clean.

## Documentation Impact
No doc change required.

## Out of Scope
- Refactoring any non-memory builder in `factory.py`.
- Changing how `MemoryServices` is assembled.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Only change parameter annotations and remove unused `None` defaults in the memory builder
helpers. Name concrete types from the memory package. Do not touch call sites. Confirm mypy
stays clean.

## Traceability
- **Workflow phase**: `python-code-review` + `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `N/A: not filed from a Plan`
- **Source implementation procedure**: `N/A: not filed from an implementation procedure`
- **Generated at**: 20261012-124821
- **Related target files**: `scripts/agent/factory.py`
