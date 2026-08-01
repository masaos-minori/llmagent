# Determine and document where the single-host vs. multi-host deployment premise belongs

## Priority
Medium

## Summary
Neither `docs/02_deployment-part1.md` nor `docs/02_deployment-part2.md` explicitly states whether this deployment guide assumes a single-host-complete setup, or a multi-host configuration (given that embed-llm/agent-llm are confirmed to run on separate hosts per `agent.toml`'s `embed_url`/`llm_url`). This higher-level architectural premise underlies both files but isn't stated in either, and might belong instead in the linked `docs/01_overview.md`.

## Reason for Change
Without this premise being stated anywhere, a reader combining both files could still come away confused about the overall deployment topology — is this "one box you set up completely," or "one box plus externally-managed LLM hosts"? This is foundational context that both files implicitly depend on without declaring.

## Implementation Intent
Confirm with the document author which document should own this premise (part1, part2, or `docs/01_overview.md`, which is already linked as a related document), then add an explicit statement of the deployment topology assumption there, cross-referenced from the other files.

## Target Files or Areas
`docs/02_deployment-part1.md`, `docs/02_deployment-part2.md`, `docs/01_overview.md` (candidate location)

## Required Changes
- Confirm with the document author which file should be the canonical home for this premise.
- Add an explicit statement there, e.g.: "本デプロイガイドは単一ホスト上でAgent本体・MCPサーバ群を完結させる構成を前提とし、embed-llm/agent-llm(LLM推論サーバ)は別ホストで個別に運用される外部サービスとして扱う。"
- Add a cross-reference from the other 2 files to wherever the statement ends up living.

## Acceptance Criteria
Exactly one canonical location states the single-host-vs-multi-host deployment premise explicitly; the other related files reference it rather than restating or omitting it.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
One of `docs/02_deployment-part1.md`, `docs/02_deployment-part2.md`, or `docs/01_overview.md` gains this premise statement; the others gain a cross-reference.

## Out of Scope
Do not restructure `docs/01_overview.md` beyond adding this one statement if it's chosen as the home — broader `01_overview.md` changes are out of scope here (see the separate Overview/Architecture domain's own issue set for unrelated `01_overview.md` work).

## AI Implementation Instruction
This is an editorial/ownership decision requiring the document author's input on which file should own this premise — if unconfirmable, default to adding it to whichever of part1/part2 most directly depends on it (part1, since it covers the setup_services.sh/LLM-host distinction) and note the placement decision as provisional pending author confirmation.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §1 (連結文書としての問題), §複数ファイルにまたがる重複・矛盾
- Generated at: 2026-08-02
