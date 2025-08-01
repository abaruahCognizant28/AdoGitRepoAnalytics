#!/usr/bin/env python3
"""
Simple runner script for Azure DevOps Git Repository Analytics Tool
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import main

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 