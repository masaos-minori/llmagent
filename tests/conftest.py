"""
Shared pytest fixtures for the llmagent test suite.
Adds scripts/ to sys.path so all project modules are importable without installation.
"""

import sys
from pathlib import Path

# scripts/ and tools/ are not installed packages; add them to sys.path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
