#!/usr/bin/env python3
"""
Automate Meroshare IPO - Main Entry Point

This script provides functionality to automate the process of applying for IPOs
through the Meroshare platform in Nepal, across one or more configured accounts.
"""

import sys
import argparse
import logging

from meroshare.client import MeroshareClient
from models.account import (
    AccountConfigError,
    DEFAULT_ACCOUNTS_PATH,
    get_account_by_name,
    load_accounts,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Automate Meroshare IPO application processes"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check available IPOs without applying",
    )

    parser.add_argument(
        "--apply-all", action="store_true", help="Apply for all available IPOs"
    )

    parser.add_argument("--apply", type=str, help="Apply for a specific IPO by name")

    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode"
    )

    parser.add_argument(
        "--account",
        type=str,
        default=None,
        help="Limit the run to a single named account from accounts.json "
        "(default: run all accounts)",
    )

    parser.add_argument(
        "--accounts-file",
        type=str,
        default=None,
        help="Path to accounts.json (default: src/accounts.json)",
    )

    return parser.parse_args()


def check_available_ipos(client, headless=True):
    """Check for available IPOs.

    Args:
        client: An authenticated MeroshareClient instance
        headless: Whether to run in headless mode

    Returns:
        bool: True if the check succeeded, False otherwise
    """
    logger.info("Checking for available IPOs...")
    try:
        client.login()
        client.navigate("asba")
        ipos = client.getAvailableIPOS()
        if not ipos:
            logger.info("No IPOs are currently available.")
        else:
            logger.info("Successfully checked available IPOs")
        return True

    except Exception as e:
        logger.error(f"Failed to check IPOs: {str(e)}")
        return False
    finally:
        client.close()


def apply_for_ipo(client, ipo_name=None, apply_all=False, headless=True):
    """Apply for IPO(s).

    Args:
        client: An authenticated MeroshareClient instance
        ipo_name: Name of specific IPO to apply for
        apply_all: Whether to apply for all available IPOs
        headless: Whether to run in headless mode

    Returns:
        str: One of "applied", "no_ipos", "failed"
    """
    try:
        client.login()
        client.navigate("asba")
        ipos = client.getAvailableIPOS()
        if not ipos:
            logger.info("No IPOs are currently available. Nothing to apply for.")
            return "no_ipos"
        client.applyAvailableIPOS()
        logger.info("Successfully applied for IPO(s)")
        return "applied"
    except Exception as e:
        logger.error(f"Failed to apply for IPO(s): {str(e)}")
        return "failed"
    finally:
        client.close()


def _print_summary(results):
    """Log a summary table of the outcome for each processed account."""
    logger.info("===== Run Summary =====")
    for name, outcome in results.items():
        logger.info(f"{name:<20}: {outcome}")
    logger.info("========================")


def main():
    """Main entry point for the application."""
    args = parse_arguments()

    accounts_path = args.accounts_file or DEFAULT_ACCOUNTS_PATH
    try:
        accounts = load_accounts(accounts_path)
    except AccountConfigError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.account:
        selected = get_account_by_name(accounts, args.account)
        if selected is None:
            logger.error(f"No account named '{args.account}' found in {accounts_path}")
            sys.exit(1)
        accounts = [selected]

    results = {}

    for account in accounts:
        logger.info(f"=== Processing account: {account.name} ({account.username}) ===")
        client = MeroshareClient(
            username=account.username,
            password=account.password,
            dp_id=account.dp_id,
            crn=account.crn,
            transaction_pin=account.transaction_pin,
            headless=args.headless,
            account_name=account.name,
        )
        try:
            if args.check_only:
                ok = check_available_ipos(client, args.headless)
                results[account.name] = "ok" if ok else "failed"
            elif args.apply_all:
                results[account.name] = apply_for_ipo(
                    client, apply_all=True, headless=args.headless
                )
            elif args.apply:
                results[account.name] = apply_for_ipo(
                    client, ipo_name=args.apply, headless=args.headless
                )
            else:
                ok = check_available_ipos(client, args.headless)
                results[account.name] = "ok" if ok else "failed"
        except Exception as e:
            logger.error(f"Unexpected error processing account '{account.name}': {e}")
            results[account.name] = "failed"

    _print_summary(results)

    if any(v == "failed" for v in results.values()):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(1)
