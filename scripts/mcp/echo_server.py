#!/usr/bin/env python3
"""Minimal JSON-RPC echo server for integration tests. stdlib only."""

import os
import sys

import orjson

# Counters for observability during integration tests.
_stats: dict[str, int] = {
    "processed": 0,
    "malformed": 0,
    "empty_lines": 0,
}


def main() -> None:
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            _stats["empty_lines"] += 1
            continue
        try:
            req = orjson.loads(line)
        except orjson.JSONDecodeError as exc:
            _stats["malformed"] += 1
            sys.stderr.write(
                f"[echo_server] malformed JSON (#{_stats['malformed']}): "
                f"{exc} — input: {raw[:80]!r}\n"
            )
            sys.stderr.flush()
            continue

        _stats["processed"] += 1
        req_id = req.get("id", 0)
        name = req.get("name", "")
        if name == "__list_tools__":
            resp: dict = {
                "id": req_id,
                "result": ["echo", "cwd_query"],
                "is_error": False,
            }
        elif name == "__stats__":
            resp = {
                "id": req_id,
                "result": orjson.dumps(_stats).decode(),
                "is_error": False,
            }
        elif name == "cwd_query":
            resp = {"id": req_id, "result": os.getcwd(), "is_error": False}
        else:
            resp = {
                "id": req_id,
                "result": f"echo: {req.get('args', {})}",
                "is_error": False,
            }
        sys.stdout.write(orjson.dumps(resp).decode() + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
