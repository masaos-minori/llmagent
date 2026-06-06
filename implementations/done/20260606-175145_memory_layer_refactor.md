# Implementation and Test Procedure: Memory Layer Refactoring

## Goal
Refactor the memory layer to remove backward-compatibility features, standardize public APIs, centralize SQLite persistence, and unify retrieval scoring configuration.

## Scope
This implementation will:
- Remove all backward-compatibility features from memory layer components
- Standardize public API boundaries across memory layer components
- Centralize SQLite persistence responsibilities in the store layer
- Unify all retrieval scoring configuration under `ScoringPolicy`
- Refactor specific files: `layer.py`, `types.py`, `retriever.py`, `scoring.py`, `ingestion.py`, `store.py`, `embedding_client.py`, `injection.py`, `extract.py`

## Assumptions
- The system has Python 3.13 installed with required dependencies
- The memory layer components are currently functional
- All existing tests and integrations are aware of the upcoming changes
- The refactoring can be done in a specific priority order

## Implementation
The implementation will:
1. Refactor `agent/memory/layer.py` to remove backward-compatibility features and standardize APIs
2. Refactor `agent/memory/types.py` to standardize type definitions
3. Refactor `agent/memory/retriever.py` to centralize SQLite operations and unify scoring
4. Refactor `agent/memory/scoring.py` to unify scoring configuration under `ScoringPolicy`
5. Refactor `agent/memory/ingestion.py` to standardize ingestion processes
6. Refactor `agent/memory/store.py` to centralize SQLite persistence
7. Refactor `agent/memory/embedding_client.py` to standardize embedding operations
8. Refactor `agent/memory/injection.py` to standardize injection processes
9. Refactor `agent/memory/extract.py` to standardize extraction processes

## Validation plan
1. Verify that all backward-compatibility features are removed from each component
2. Confirm that public APIs are properly standardized across all components
3. Ensure SQLite operations are centralized in the store layer
4. Validate that scoring configuration is unified under `ScoringPolicy`
5. Test that existing functionality is preserved in each component
6. Run relevant tests to ensure no regressions in memory layer functionality
7. Verify that all refactored components integrate properly with each other