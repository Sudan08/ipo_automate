"""
Account model and loader for multi-account Meroshare configuration.
"""

import json
import logging
import os
import stat
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_ACCOUNTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "accounts.json"
)

_REQUIRED_FIELDS = ("name", "username", "password", "dp_id", "crn", "transaction_pin")

# Optional per-account settings, with the default used when they are absent.
# `bank` / `bank_account` are only needed when more than one is linked to the
# account - MeroShare assigns their internal ids per user, so they are matched
# by name at runtime rather than configured as ids.
_OPTIONAL_FIELDS = {"bank": "", "bank_account": "", "applied_kitta": "10"}


class AccountConfigError(Exception):
    """Raised when accounts.json is missing, malformed, or invalid."""


@dataclass
class Account:
    name: str
    username: str
    password: str
    dp_id: str
    crn: str
    transaction_pin: str
    bank: str = ""
    bank_account: str = ""
    applied_kitta: str = "10"


def load_accounts(path: str = DEFAULT_ACCOUNTS_PATH) -> List[Account]:
    """Load and validate the accounts list from a JSON file.

    Raises:
        AccountConfigError: if the file is missing, is not valid JSON,
            is not a non-empty list, or any entry is missing a required
            field or has a duplicate name.
    """
    if not os.path.isfile(path):
        raise AccountConfigError(
            f"Accounts file not found at {path}. "
            f"Copy src/accounts.example.json to src/accounts.json and fill in your credentials."
        )

    _warn_if_permissions_too_open(path)

    with open(path, "r", encoding="utf-8") as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError as e:
            raise AccountConfigError(f"Invalid JSON in {path}: {e}") from e

    if not isinstance(raw, list) or not raw:
        raise AccountConfigError(
            f"{path} must contain a non-empty JSON array of account objects."
        )

    accounts = []
    seen_names = set()
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise AccountConfigError(f"Account entry #{i} in {path} is not an object.")
        missing = [f for f in _REQUIRED_FIELDS if not entry.get(f)]
        if missing:
            raise AccountConfigError(
                f"Account entry #{i} in {path} is missing required field(s): {', '.join(missing)}"
            )
        if entry["name"] in seen_names:
            raise AccountConfigError(
                f"Duplicate account name '{entry['name']}' in {path}. Names must be unique."
            )
        seen_names.add(entry["name"])
        fields = {f: str(entry[f]) for f in _REQUIRED_FIELDS}
        for field, default in _OPTIONAL_FIELDS.items():
            value = entry.get(field)
            fields[field] = str(value) if value not in (None, "") else default
        accounts.append(Account(**fields))

    return accounts


def get_account_by_name(accounts: List[Account], name: str) -> Optional[Account]:
    return next((a for a in accounts if a.name == name), None)


def _warn_if_permissions_too_open(path: str) -> None:
    """POSIX-only best-effort warning if accounts.json is group/world readable."""
    if os.name != "posix":
        return
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode)
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            logger.warning(
                f"{path} is readable by group/other users (mode {oct(mode)}). "
                f"Run 'chmod 600 {path}' to restrict access to your credentials."
            )
    except OSError:
        pass
