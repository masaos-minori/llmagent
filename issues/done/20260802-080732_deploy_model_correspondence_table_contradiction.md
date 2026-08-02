# Fix internal contradiction in docs/02_deployment-part1.md model-correspondence table

## Priority
Medium

## Summary
`docs/02_deployment-part1.md` §1.4 (~lines 77-81)'s LLM-model-retrieval table has an internal contradiction: it labels an entry "Qwen2.5-Coder-7B (LLM)" by purpose/version, but the corresponding filename listed is `Qwen3.6-Instruct-Q4_K_M.gguf` — a different model family, version, and variant (Coder vs. Instruct) than the label implies.

## Reason for Change
This is a confirmed internal document inconsistency (found without needing to cross-check the actual deployed environment) — an implementer following this table could retrieve/deploy the wrong model file, degrading embedding/generation quality or causing a startup-time model mismatch error.

## Implementation Intent
Determine which is actually correct — the purpose/version label or the filename — by checking what is actually deployed at `/opt/llm/models/` (or consulting the document author/design owner), then correct the table to be internally consistent. Also compress the table per the related summarization intent (see 要約候補), keeping only the placement-and-key-matching principle in the main text.

## Target Files or Areas
`docs/02_deployment-part1.md` (§1.4, ~lines 77-81)

## Required Changes
- Confirm the actual, currently-deployed model file(s) at `/opt/llm/models/` (via direct inspection if accessible, or via the document author).
- Correct the table so the model label (purpose/version) and filename are consistent.
- Compress the surrounding text to the principle: "モデルファイルは `/opt/llm/models/` 配下に配置し、ファイル名は `agent.toml` の対応するモデルパスキーと一致させること." with the corrected file-name detail kept in a compact table or reference.

## Acceptance Criteria
The model-correspondence table no longer contains a contradictory label/filename pair for any entry; the surrounding text is compressed to the placement-and-key-matching principle.

## Testing Expectations
Not required (documentation-only). Verify the actual deployed model filename before finalizing — do not guess between the two conflicting values presented in the current table.

## Documentation Impact
`docs/02_deployment-part1.md` §1.4 corrected and compressed.

## Out of Scope
Do not change the actual deployed model files in this issue — documentation only, reflecting whichever is confirmed correct.

## AI Implementation Instruction
Do not assume either the label or the filename is correct without confirmation — this is an internal document contradiction, not a documentation-vs-code mismatch, so neither side is automatically authoritative. If the actual deployed model can't be confirmed, register this as an explicit Needs Confirmation item rather than picking one arbitrarily.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §3 要約候補 item 1, §6 (モデル対応表の内部矛盾)
- Generated at: 2026-08-02
