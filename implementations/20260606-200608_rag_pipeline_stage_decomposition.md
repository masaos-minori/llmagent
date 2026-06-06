# Implementation and Test Procedure: RAG Pipeline Stage Decomposition

## Goal
Decompose the RAG pipeline into independent PipelineStage components with unit tests and latency measurements.

## Scope
This implementation will:
- Create `PipelineStage` Protocol and `PipelineContext` classes
- Implement MQE/Search/Fusion/Rerank/Augment Stage classes
- Update `rag/pipeline.py` to use Stage-based execution
- Maintain the same return value signature (4-tuple)
- Add OTel span measurements

## Assumptions
- Current `rag/pipeline.py` sequentially executes MQE → Search → RRF → Rerank → Augment
- OTel tracer is implemented in `shared/otel_tracer.py`
- Behavior-lock tests exist in `test_rag_pipeline.py`

## Implementation
The implementation will create the following files:
1. `scripts/rag/stage.py` - `PipelineStage` Protocol and `PipelineContext` classes
2. `scripts/rag/stages/mqe.py` - MQE Stage implementation
3. `scripts/rag/stages/search.py` - Search Stage implementation
4. `scripts/rag/stages/fusion.py` - Fusion Stage implementation
5. `scripts/rag/stages/rerank.py` - Rerank Stage implementation
6. `scripts/rag/stages/augment.py` - Augment Stage implementation
7. Update `scripts/rag/pipeline.py` to use Stage-based execution

## Validation plan
1. Verify that linting passes (`ruff check scripts/rag/`)
2. Verify that type checking passes (`mypy scripts/`)
3. Verify that architecture checks pass (`lint-imports`)
4. Verify that existing tests still pass (`uv run pytest tests/test_rag_pipeline.py`)
5. Confirm that the return value signature is maintained
6. Validate that OTel span measurements are correctly implemented