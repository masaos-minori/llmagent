from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_offset(offsets_dir: str, consumer_id: str) -> int:
    safe_id = consumer_id.replace("/", "_").replace("..", "_")
    path = Path(offsets_dir) / safe_id
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_offset(offsets_dir: str, consumer_id: str, seq: int) -> None:
    safe_id = consumer_id.replace("/", "_").replace("..", "_")
    Path(offsets_dir).mkdir(parents=True, exist_ok=True)
    path = Path(offsets_dir) / safe_id
    path.write_text(str(seq))
    logger.debug("offset written consumer=%s seq=%d", consumer_id, seq)
