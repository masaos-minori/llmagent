# Implementation Procedure: Add Auth Model Design Note and EVENTBUS-008 Known Issue to EventBus Known-Issues Doc

## Goal
Extend `docs/06_eventbus_90_inconsistencies_and_known_issues.md` with:
1. A new Known Issue entry "EVENTBUS-008: No production authentication model" in the "対応が必要な項目" section (High/open severity, matching EVENTBUS-001 rigor)
2. An auth/authz design note selecting static bearer token validated by the EventBus process itself, with documented upgrade path to rotatable service token, 401/403 response shapes, local-dev bypass conditions, and secret rotation expectations — explicitly labeled as a decision record for a future implementation requirement

## Scope
- Target file: `docs/06_eventbus_90_inconsistencies_and_known_issues.md`
- Add EVENTBUS-008 entry in "対応が必要な項目" section
- Add auth model design note (new subsection or alongside Known Issue entry)
- Explicitly label auth note as decision record for future implementation requirement (not authorization to implement)

## Assumptions
- The six auth-model options from `issues/done/20260818_04_issue.md` are the complete candidate set
- Current code has no authentication (loopback-only, no auth)
- Selection is documentation-only; implementation deferred to future requirement per Global Rule 8

## Design decisions
- Select **static bearer token validated by the EventBus process itself** as the recommended model
- Rationale: requires no new infrastructure (no reverse proxy or mTLS cert management), enforceable directly in `scripts/eventbus/config.py`'s existing validation pattern (rejecting `allow_public_bind=true` without a configured token), minimum viable step up from today's "loopback-only, no auth" state
- Document: 401 (missing/absent `Authorization` header) vs. 403 (well-formed but wrong/revoked token) response body shapes
- Local-dev bypass: `EVENTBUS_LOCAL_DEV=1`-style restricted to loopback bind (mirroring existing `allow_public_bind` gate)
- Secret rotation: "operator replaces the configured token value and restarts the process" (no hot-reload) for first iteration; rotation-without-restart flagged as future enhancement
- Explicitly label as decision record for future implementation requirement (not authorization to implement)

## Alternatives considered
- mTLS: Rejected — requires cert management infrastructure
- Reverse-proxy auth: Rejected — adds external dependency
- Per-consumer authz: Rejected — over-engineered for first iteration
- Loopback-only (current): Rejected — not production-ready

## Implementation
### Target file
`docs/06_eventbus_90_inconsistencies_and_known_issues.md`

### Procedure
1. Read the current file content
2. Add EVENTBUS-008 entry in "対応が必要な項目" section (after EVENTBUS-001)
3. Add auth model design note (new subsection "認証/認可モデル設計メモ" or alongside Known Issue)
4. Ensure explicit label: "この設計メモは将来の実装要件へのインプットであり、この計画書/ドキュメント更新フェーズでは実装を許可しない（Global Rule 8）"

### Method
Direct Markdown editing with exact section placement

### Details
**EVENTBUS-008 Entry (add in "対応が必要な項目" section after EVENTBUS-001):**

### EVENTBUS-008: No production authentication model (High/open)

Event Bus の HTTP API（`/publish`、`/subscribe`、`/events/{event_id}/ack`、`/nack`、`/health`、`/dlq`、`/replay`）に本番グレードの認証/認可が存在しない。現在は loopback-only バインドと `allow_public_bind=false` による制御のみで、`allow_public_bind=true` にすると完全にオープンになる。本番環境での運用には認証モデルの実装が必要。

**認証/認可モデル設計メモ（将来の実装要件へのインプット）**

**選択モデル: 静的 Bearer トークン（EventBus プロセス自身で検証）**

根拠:
- 新しいインフラ不要（リバースプロキシや mTLS 証明書管理への依存なし）
- 既存の `scripts/eventbus/config.py` のバリデーションパターン（`allow_public_bind=true` かつトークン未設定を拒否）に直接実装可能
- 現在の "loopback-only, no auth" 状態からの最小限のステップアップ

**レスポンス形状:**
- 401 Unauthorized: `Authorization` ヘッダー欠如 / 不正形式
  ```json
  {"error": "unauthorized", "message": "Authorization header required"}
  ```
- 403 Forbidden: ヘッダーはあるがトークン不一致 / 失効
  ```json
  {"error": "forbidden", "message": "Invalid or revoked token"}
  ```

**ローカル開発バイパス:**
- `EVENTBUS_LOCAL_DEV=1` 環境変数（または同等の設定）でバイパス可能
- ただし loopback バインド（`127.0.0.1`/`::1`）時のみ有効 — 既存の `allow_public_bind` ゲートと整合

**シークレットローテーション:**
- 第1イテレーション: 運用者が設定値を書き換え、プロセス再起動（ホットリロードなし）
- 再起動なしローテーションは将来の拡張としてフラグのみ立てる（本設計メモの最小バーには含めない）

> **重要**: この設計メモは将来の実装要件へのインプットであり、この計画書/ドキュメント更新フェーズでは実装を許可しない（Global Rule 8: Event Bus 関連実装は禁止、デバッグ/調査のみ可）。実装は別途独立した要件として起票すること。

## Compatibility considerations
- Documentation-only change, no code impact
- Explicit deferral of implementation to future requirement
- Known Issue entry matches EVENTBUS-001 format/severity

## Security considerations
- Design note documents security model; no implementation here
- 401/403 distinction prevents information leakage about token validity

## Rollback considerations
- Git revert of this file if issues arise

## Validation plan
- Manual review: new entry matches EVENTBUS-001 severity/format convention
- Auth note has 401/403/local-dev/rotation subsections
- `git diff` confirms no `scripts/` files changed

## Out of scope
- Implementation of bearer token validation in `scripts/eventbus/config.py` or route handlers (deferred to future requirement per Global Rule 8)
- OpenAPI spec creation
- mTLS, reverse proxy, or per-consumer authz implementation

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-220838_require.md
- Source plan: plans/20260819-173619_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-133459
- Related target files: docs/06_eventbus_90_inconsistencies_and_known_issues.md