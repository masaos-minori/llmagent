"""tests/rag/ingestion/test_crawler_config_validation.py

Missing-required-key validation for WebCrawler.__init__ (ragrev019):
single-key removal, several keys named in declared order, complete config,
and a drift guard keeping the required-key tuple and config/crawler.toml in sync.
"""

import tomllib
from pathlib import Path

import pytest
from rag.ingestion.crawler import _REQUIRED_KEYS, WebCrawler


def _complete_config(tmp_path: Path) -> dict:
    """Return a config containing every required key, rooted at tmp_path."""
    return {
        "rag_src_dir": str(tmp_path / "rag-src"),
        "crawl_delay": 0,
        "max_depth": 1,
        "min_chunk": 0,
        "fetch_retry": 1,
        "target_urls": [],
    }


@pytest.mark.parametrize("key", _REQUIRED_KEYS)
def test_each_required_key_missing(tmp_path: Path, key: str) -> None:
    """Removing one required key raises one ValueError naming that key."""
    cfg = _complete_config(tmp_path)
    del cfg[key]
    with pytest.raises(ValueError, match=key):
        WebCrawler(config=cfg)


def test_several_missing_keys_named_in_declared_order(tmp_path: Path) -> None:
    """Removing several required keys raises one ValueError naming all of them in declared order."""
    cfg = _complete_config(tmp_path)
    del cfg["rag_src_dir"]
    del cfg["min_chunk"]
    with pytest.raises(ValueError) as excinfo:
        WebCrawler(config=cfg)
    msg = str(excinfo.value)
    assert "rag_src_dir" in msg and "min_chunk" in msg
    assert msg.index("rag_src_dir") < msg.index("min_chunk")


def test_complete_config_constructs(tmp_path: Path) -> None:
    """A complete config constructs normally and parses target_urls as before."""
    crawler = WebCrawler(config=_complete_config(tmp_path))
    assert crawler._target_urls == []


def test_shipped_crawler_toml_covers_required_keys() -> None:
    """The shipped config/crawler.toml defines every key in the required tuple."""
    toml_path = Path(__file__).resolve().parents[3] / "config" / "crawler.toml"
    with toml_path.open("rb") as f:
        data = tomllib.load(f)
    assert set(_REQUIRED_KEYS) <= set(data.keys())
