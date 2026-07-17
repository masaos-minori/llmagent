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
        """Write plain text output."""
        print(text)

    def write_success(self, text: str) -> None:
        """Write a success message prefixed with a space."""
        print(f"  {text}")

    def write_error(self, text: str) -> None:
        """Write an error message prefixed with '[error]'."""
        print(f"  [error] {text}")

    def write_no_data(self, text: str) -> None:
        """Write a no-data message prefixed with a space."""
        print(f"  {text}")

    def write_validation_error(self, text: str) -> None:
        """Write a validation error message prefixed with '[usage]'."""
        print(f"  [usage] {text}")

    def write_table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Write a formatted table with aligned columns."""
        if not rows:
            return
        expected = len(headers)
        for idx, row in enumerate(rows):
            if len(row) != expected:
                raise ValueError(
                    f"write_table: row {idx} has {len(row)} cells, expected {expected}"
                )
        widths = [
            max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
        ]
        header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_line)
        print("-" * len(header_line))
        for row in rows:
            print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))

    def write_kv(self, pairs: list[tuple[str, str]], key_width: int = 22) -> None:
        """Write key-value pairs as aligned lines."""
        for k, v in pairs:
            print(f"  {k:<{key_width}}: {v}")

    def write_debug_rag(self, data: dict) -> None:
        """Write RAG debug information including queries, results, and scores."""
        queries: list = data.get("queries", [])
        all_results: list = data.get("all_results", [])
        merged: list = data.get("merged", [])
        reranked: list = data.get("reranked", [])
        use_rrf = data.get("use_rrf", True)
        rrf_k = data.get("rrf_k", 60)
        http_result_kind = data.get("http_result_kind")
        print(f"  [debug] MQE queries ({len(queries)}):")
        for i, q in enumerate(queries, 1):
            print(f"    {i}: {q}")
        total = sum(len(r) for r in all_results)
        print(
            f"  [debug] search: {len(all_results)} result lists, {total} total candidates"
        )
        rrf_label = (
            f"use_rrf={use_rrf} rrf_k={rrf_k}"
            if use_rrf
            else f"use_rrf={use_rrf} (rank signal disabled)"
        )
        print(f"  [debug] fusion: {rrf_label}")
        if http_result_kind is not None:
            kind_label = (
                "success (empty response — no in-process fallback)"
                if http_result_kind == "empty"
                else http_result_kind
            )
            print(f"  [debug] http_result_kind: {kind_label}")
        print(f"  [debug] RRF merge: {len(merged)} unique candidates (top 5):")
        for c in merged[:5]:
            print(
                f"    chunk_id={c.get('chunk_id')} rrf={c.get('rrf_score', 0):.4f} url={str(c.get('url', ''))[:60]}"
            )
        print(f"  [debug] reranked top-{len(reranked)}:")
        for c in reranked:
            score = c.get("rerank_score", c.get("rrf_score", 0))
            print(
                f"    chunk_id={c.get('chunk_id')} score={score:.4f} url={str(c.get('url', ''))[:60]}"
            )
