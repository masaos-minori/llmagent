#!/usr/bin/env python3
"""Legacy entry point for backward compatibility.

This file is kept for backward compatibility only.
Use `python -m agent` (from the scripts/ directory) instead.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for backward compatibility
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the new entry point
from agent.__main__ import main

if __name__ == "__main__":
    main()
