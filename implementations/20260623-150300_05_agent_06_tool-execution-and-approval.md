# Implementation: docs/05_agent_06_tool-execution-and-approval.md — cache key 関数名修正

**Plan:** `plans/20260623-111653_plan.md` (Step 4 のみ未実装)
**Target:** `docs/05_agent_06_tool-execution-and-approval.md`

---

## 変更箇所: line 165

**変更前:**
```
- Cache key: `"{tool_name}:{orjson_dumps(args)}"` (plain string, no MD5)
```

**変更後:**
```
- Cache key: `f"{tool_name}:{_json_dumps(args)}"` (plain string, no MD5; `_json_dumps` = orjson with OPT_SORT_KEYS)
```

**変更理由:** `orjson_dumps` は旧名称。実装は `from shared.json_utils import dumps as _json_dumps` であり、`tool_executor.py:608` で `cache_key = f"{tool_name}:{_json_dumps(args)}"` と使用されている。

---

## 完了条件

```bash
grep -n "orjson_dumps" docs/05_agent_06_tool-execution-and-approval.md
# → 0件

grep -n "_json_dumps\|cache key" docs/05_agent_06_tool-execution-and-approval.md
# → _json_dumps が存在
```
