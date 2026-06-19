"""agent/commands/output_port.py
OutputPort Protocol and CliOutputPort implementation for command handlers.
"""

from __future__ import annotations

from typing import Protocol


class OutputPort(Protocol):
    def write(self, text: str) -> None: ...
    def write_table(self, headers: list[str], rows: list[list[str]]) -> None: ...
    def write_error(self, text: str) -> None: ...
    def write_success(self, text: str) -> None: ...
    def write_no_data(self, text: str) -> None: ...
    def write_validation_error(self, text: str) -> None: ...
    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None: ...
    def write_debug_rag(self, data: dict) -> None: ...


class CliOutputPort:
    """Concrete OutputPort that writes to stdout via print()."""

    def write(self, text: str) -> None:
        print(text)

    def write_success(self, text: str) -> None:
        print(f"  {text}")

    def write_error(self, text: str) -> None:
        print(f"  [error] {text}")

    def write_no_data(self, text: str) -> None:
        print(f"  {text}")

    def write_validation_error(self, text: str) -> None:
        print(f"  [usage] {text}")

    def write_table(self, headers: list[str], rows: list[list[str]]) -> None:
        if not rows:
            return
        widths = [
            max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
        ]
        header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_line)
        print("-" * len(header_line))
        for row in rows:
            print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))

    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None:
        for k, v in pairs:
            print(f"  {k:<{key_width}}: {v}")

    def write_debug_rag(self, data: dict) -> None:
        queries: list = data.get("queries", [])
        all_results: list = data.get("all_results", [])
        merged: list = data.get("merged", [])
        reranked: list = data.get("reranked", [])
        use_rrf = data.get("use_rrf", True)
        rrf_k = data.get("rrf_k", 60)
        print(f"  [debug] MQE queries ({len(queries)}):")
        for i, q in enumerate(queries, 1):
            print(f"    {i}: {q}")
        total = sum(len(r) for r in all_results)
        print(
            f"  [debug] search: {len(all_results)} result lists, {total} total candidates"
        )
        print(f"  [debug] fusion: use_rrf={use_rrf} rrf_k={rrf_k}")
        print(f"  [debug] RRF merge: {len(merged)} unique candidates (top 5):")
        for c in merged[:5]:
            print(
                f"    chunk_id={c.get('chunk_id')}"
                f" rrf={c.get('rrf_score', 0):.4f}"
                f" url={str(c.get('url', ''))[:60]}"
            )
        print(f"  [debug] reranked top-{len(reranked)}:")
        for c in reranked:
            score = c.get("rerank_score", c.get("rrf_score", 0))
            print(
                f"    chunk_id={c.get('chunk_id')}"
                f" score={score:.4f}"
                f" url={str(c.get('url', ''))[:60]}"
            )
