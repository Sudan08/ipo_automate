"""
Tests for command-line argument parsing functionality.
"""

import sys
import pytest
from unittest.mock import patch
from src.main import parse_arguments

class TestArgumentParsing:
    """Tests for the argument parsing functionality."""

    def test_check_only_flag(self):
        """Test the --check-only flag is correctly parsed."""
        with patch('sys.argv', ['main.py', '--check-only']):
            args = parse_arguments()
            assert args.check_only is True
            assert args.apply_all is False
            assert args.apply is None
            assert args.headless is False

    def test_apply_all_flag(self):
        """Test the --apply-all flag is correctly parsed."""
        with patch('sys.argv', ['main.py', '--apply-all']):
            args = parse_arguments()
            assert args.apply_all is True
            assert args.check_only is False
            assert args.apply is None
            assert args.headless is False

    def test_apply_specific_ipo(self):
        """Test the --apply flag with a specific IPO name is correctly parsed."""
        test_ipo_name = "ABC Bank Limited"
        with patch('sys.argv', ['main.py', f'--apply={test_ipo_name}']):
            args = parse_arguments()
            assert args.apply == test_ipo_name
            assert args.apply_all is False
            assert args.check_only is False
            assert args.headless is False

    def test_headless_flag(self):
        """Test the --headless flag is correctly parsed."""
        with patch('sys.argv', ['main.py', '--headless']):
            args = parse_arguments()
            assert args.headless is True
            assert args.check_only is False
            assert args.apply_all is False
            assert args.apply is None

    def test_combined_flags(self):
        """Test multiple flags can be combined correctly."""
        test_ipo_name = "XYZ Hydropower"
        with patch('sys.argv', ['main.py', '--apply', test_ipo_name, '--headless']):
            args = parse_arguments()
            assert args.apply == test_ipo_name
            assert args.headless is True
            assert args.check_only is False
            assert args.apply_all is False

    def test_no_args_specified(self):
        """Test default behavior when no arguments are specified."""
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()
            assert args.check_only is False
            assert args.apply_all is False
            assert args.apply is None
            assert args.headless is False

