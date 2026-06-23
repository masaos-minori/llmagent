# Implementation: docs/04_mcp_02_protocol_and_transport.md — stdio Scalability 設計ノート追加

**Plan:** `plans/20260623-111843_plan.md` (Step 1)
**Target:** `docs/04_mcp_02_protocol_and_transport.md`

---

## 変更箇所

"HTTP vs stdio Mode" セクション (line 157-167) の後、line 168 の `---` と line 170 の `## Bearer Authentication` の間に挿入する。

---

## 追加内容

line 168 (`---`) の直後 (line 169 の空行の後) に以下を挿入:

```markdown
### stdio Transport: Scalability Limits (Design Note)

**Current behavior:**
Each `StdioTransport` instance serializes concurrent calls using a single `asyncio.Lock`
(see `shared/tool_executor.py`). This means only one request at a time can be in-flight
per stdio server, regardless of how many concurrent tool calls arrive.

**Why this is acceptable today:**
All production servers use `transport = "http"` (see `config/mcp_servers.toml`).
stdio mode is available but currently unused in production. With one or two stdio servers
handling low-concurrency workloads, the lock contention is negligible.

**When this becomes a bottleneck:**
If stdio-based servers become common, or if a single stdio server receives high
concurrent load (e.g., embedded local tools called across many parallel tool rounds),
the serialized lock will create a queue of waiting coroutines. Threshold TBD — dependent
on round concurrency and per-call latency.

**Future scaling options (planning note — no current commitment):**

1. **Worker pool per stdio server**: Spawn N subprocess workers and distribute calls
   across them using a semaphore-guarded pool. Cost: N × memory overhead per worker.

2. **Multiplexed stdio protocol**: Extend the JSON-RPC framing to support concurrent
   in-flight requests with response matching by `id`. Requires server-side support and
   a response demultiplexer in `StdioTransport`.

3. **Migrate to HTTP transport**: Convert high-traffic stdio servers to persistent HTTP
   servers. Aligns with the existing `HttpTransport` path which has no per-instance
   serialization constraint. This is the lowest-risk migration path.

See `04_mcp_01_system_overview.md` for the transport overview and
`shared/tool_executor.py` (`StdioTransport` class) for the lock implementation.

```

挿入後の構造:

```
## HTTP vs stdio Mode
...テーブル...
---
### stdio Transport: Scalability Limits (Design Note)
...追加内容...

---
## Bearer Authentication
```

---

## 完了条件

```bash
grep -n "Scalability Limits\|Worker pool\|Multiplexed" docs/04_mcp_02_protocol_and_transport.md
# → 各キーワードが存在
```
