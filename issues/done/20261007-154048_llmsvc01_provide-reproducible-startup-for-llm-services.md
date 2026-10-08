# Provide reproducible startup for LLM services

## Priority
Medium

## Summary
Add repository-managed service definitions and documented startup steps for the embedding LLM and agent LLM services, like the other services.

## Background
Source: local investigation notes (memo1.md, ISSUE-12), from DEPLOY-001.

## Problem
- No script, service definition, or configuration for starting embed-llm and agent-llm exists in the repository (per investigation notes).
- The header comment of `setup_services.sh` wrongly says the Agent starts the LLM.

## Reason for Change
- Operators cannot learn from the documentation how to start the LLM services, so recovery and rebuild are not reproducible.
- The embedding model dimension must match the RAG schema, but that prerequisite is not recorded in any procedure.

## Implementation Intent
- LLM services are started reproducibly from definitions inside the repository, like the other services.

## Target Files or Areas
- `deploy/`, `deploy/setup_services.sh`, deployment_01

## Required Changes
- Add a service definition for llama-server under `deploy/` for the target OS's service manager (OpenRC init script and conf.d if the target is Gentoo).
- Document startup steps and the relationship between model dimension and the RAG schema in deployment_01.
- Fix the header comment of `setup_services.sh`.

## Constraints
- No secrets or host-specific paths committed; follow the documentation content policy for literals.

## Acceptance Criteria
- An operator can start the LLM services following only the documented steps.

## Testing Expectations
Not required: deployment definition and documentation; verify manually on a target host.

## Documentation Impact
Update deployment_01 (startup procedure, dimension prerequisite); remove Known Issue DEPLOY-001 from the ledger when done.

## Out of Scope
- Model selection and performance tuning.

## Dependencies
N/A: none

## Unresolved Questions
- How llama-server is currently started on the operations server (configuration outside the repository).
- The target OS (documents may mix Ubuntu and Gentoo descriptions).

## AI Implementation Instruction
Do not invent host-specific values; ask or mark them as configuration. Verify the target OS before choosing the service manager.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154048
- **Related target files**: `deploy/`, `deploy/setup_services.sh`, `docs/90_deployment/deployment_01_deployment.md`
