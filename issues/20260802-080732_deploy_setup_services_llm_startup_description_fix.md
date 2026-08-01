# Fix confirmed-inaccurate setup_services.sh LLM-startup description in docs/02_deployment-part1.md

## Priority
High

## Summary
`docs/02_deployment-part1.md` §2.3 opens with "`deploy/setup_services.sh` initializes the LLM services," but the actual corresponding code (~lines 74-83) only executes an `echo` statement per service (`embed-llm`, `agent-llm`) with no actual process-start logic. Furthermore, `config/agent.toml` shows `embed_url`/`llm_url` pointing to separate host IP addresses — meaning embed-llm/agent-llm are external services running on different hosts entirely, outside this deployment pipeline's scope. This fact is not explained anywhere in `part1`.

## Reason for Change
This is a confirmed implementation mismatch — a reader would reasonably conclude that running `setup_services.sh` starts the LLM services, when in fact it does not, and those services must be started/managed separately on different hosts. In production, this misunderstanding could result in going live with the LLM servers never actually started.

## Implementation Intent
Correct the opening description to accurately state what `setup_services.sh` actually does (validates workflow artifacts, checks DB/schema, starts agent-managed MCP servers on ports 8004-8014), and explicitly state that embed-llm/agent-llm run on separate hosts and are outside this pipeline's scope.

## Target Files or Areas
`docs/02_deployment-part1.md` (§2.3)

## Required Changes
- Replace "`deploy/setup_services.sh` initializes the LLM services." with: "`deploy/setup_services.sh` はワークフロー成果物の検証・DB/スキーマの事前確認を行った後、agent-managedなMCPサーバ(port 8004-8014)を起動する。embed-llm/agent-llmは `agent.toml` の `embed_url`/`llm_url` が指す別ホスト上で個別に起動・運用されるプロセスであり、このスクリプトはローカルでLLMプロセスを起動しない。"
- Re-verify the exact current line range and behavior of `setup_services.sh`'s embed-llm/agent-llm handling before finalizing, in case it has changed since this review.

## Acceptance Criteria
The description accurately reflects `setup_services.sh`'s actual behavior (echo-only, no process start) and explicitly states embed-llm/agent-llm are separate-host external services outside this pipeline's scope.

## Testing Expectations
Not required (documentation-only). Manually re-verify `setup_services.sh`'s current behavior and `config/agent.toml`'s `embed_url`/`llm_url` values before finalizing.

## Documentation Impact
`docs/02_deployment-part1.md` corrected — resolves a confirmed implementation mismatch.

## Out of Scope
Do not implement actual LLM-process-starting logic in `setup_services.sh` in this issue — documentation only, reflecting current (echo-only) reality. Do not resolve where the broader single-host-vs-multi-host deployment premise should be documented — tracked in a separate issue.

## AI Implementation Instruction
This is a confirmed implementation mismatch — apply the fix directly, re-verifying `setup_services.sh`'s current behavior and `agent.toml`'s current URL values first.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §4 強化候補 (§2.3 setup_services.sh), §5 例2, §6 (LLMサーバ起動責務の欠落)
- Generated at: 2026-08-02
