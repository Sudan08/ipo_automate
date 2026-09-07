"""
Pytest configuration file for the automate-meroshare-ipo application.
"""

import os
import sys
import pytest

# Add the project root directory to Python path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# src/ is the import root at runtime (main.py does `from meroshare.client import ...`),
# so tests need it on the path too.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
