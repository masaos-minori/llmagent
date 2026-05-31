#!/usr/bin/env python3
"""Minimal JSON-RPC echo server for integration tests. stdlib only."""

import json
import os
import sys


def main() -> None:
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        req_id = req.get("id", 0)
        name = req.get("name", "")
        if name == "__list_tools__":
            resp: dict = {
                "id": req_id,
                "result": ["echo", "cwd_query"],
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
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
