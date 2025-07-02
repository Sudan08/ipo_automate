#!/usr/bin/env python3
"""
Automate Meroshare IPO - Main Entry Point

This script provides functionality to automate the process of applying for IPOs
through the Meroshare platform in Nepal.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

from meroshare.client import MeroshareClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Automate Meroshare IPO application processes'
    )

    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check available IPOs without applying'
    )

    parser.add_argument(
        '--apply-all',
        action='store_true',
        help='Apply for all available IPOs'
    )

    parser.add_argument(
        '--apply',
        type=str,
        help='Apply for a specific IPO by name'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )

    return parser.parse_args()


def check_available_ipos(client, headless=True):
    """Check for available IPOs.

    Args:
        client: An authenticated MeroshareClient instance
        headless: Whether to run in headless mode

    Returns:
        List of available IPOs
    """
    logger.info("Checking for available IPOs...")
    try:
        client.login()
        client.navigate("asba")
        logger.info("Successfully checked available IPOs")
        client.getAvailableIPOS()

    except Exception as e:
        logger.error(f"Failed to check IPOs: {str(e)}")
        raise
    finally:
        client.close()


def apply_for_ipo(client, ipo_name=None, apply_all=False, headless=False):
    """Apply for IPO(s).

    Args:
        client: An authenticated MeroshareClient instance
        ipo_name: Name of specific IPO to apply for
        apply_all: Whether to apply for all available IPOs
        headless: Whether to run in headless mode
    """
    try:
        client.login()
        client.navigate("asba")
        logger.info("Successfully checked available IPOs")
        client.getAvailableIPOS()
        client.applyAvailableIPOS()

        # TODO: Implement IPO application logic
        logger.info("Successfully applied for IPO(s)")
    except Exception as e:
        logger.error(f"Failed to apply for IPO(s): {str(e)}")
        raise
    finally:
        client.close()


def main():
    """Main entry point for the application."""
    # Load environment variables from .env file
    load_dotenv()

    # Parse command line arguments
    args = parse_arguments()

    # Check for required environment variables
    required_vars = ['MEROSHARE_USERNAME', 'MEROSHARE_PASSWORD',
                     'MEROSHARE_DP_ID', 'MEROSHARE_CRN']

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file")
        sys.exit(1)

    # Initialize Meroshare client
    client = MeroshareClient(
        username=os.getenv('MEROSHARE_USERNAME'),
        password=os.getenv('MEROSHARE_PASSWORD'),
        dp_id=os.getenv('MEROSHARE_DP_ID'),
        crn=os.getenv('MEROSHARE_CRN'),
        transaction_pin=os.getenv("MEROSHARE_TRANSACTIONPIN"),
        headless=False
    )

    try:
        # Process command line arguments
        if args.check_only:
            check_available_ipos(client, args.headless)
        elif args.apply_all:
            apply_for_ipo(client, apply_all=True, headless=args.headless)
        elif args.apply:
            apply_for_ipo(client, ipo_name=args.apply, headless=args.headless)
        else:
            # No specific action requested, just check IPOs as default
            check_available_ipos(client, args.headless)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(1)
