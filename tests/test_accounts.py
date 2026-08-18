"""
Tests for account configuration loading.
"""

import json
import pytest

from models.account import (
    AccountConfigError,
    get_account_by_name,
    load_accounts,
)


VALID_ACCOUNTS = [
    {
        "name": "acct1",
        "username": "u1",
        "password": "p1",
        "dp_id": "1",
        "crn": "c1",
        "transaction_pin": "1234",
    },
    {
        "name": "acct2",
        "username": "u2",
        "password": "p2",
        "dp_id": "2",
        "crn": "c2",
        "transaction_pin": "5678",
    },
]


class TestLoadAccounts:
    """Tests for load_accounts()."""

    def test_valid_file_parses(self, tmp_path):
        p = tmp_path / "accounts.json"
        p.write_text(json.dumps(VALID_ACCOUNTS))
        accounts = load_accounts(str(p))
        assert len(accounts) == 2
        assert accounts[0].name == "acct1"
        assert accounts[0].username == "u1"

    def test_missing_file_raises_clear_error(self, tmp_path):
        p = tmp_path / "does_not_exist.json"
        with pytest.raises(AccountConfigError, match="not found"):
            load_accounts(str(p))

    def test_malformed_json_raises_clear_error(self, tmp_path):
        p = tmp_path / "accounts.json"
        p.write_text("{not valid json")
        with pytest.raises(AccountConfigError, match="Invalid JSON"):
            load_accounts(str(p))

    def test_missing_required_field_raises(self, tmp_path):
        p = tmp_path / "accounts.json"
        p.write_text(json.dumps([{"name": "acct1", "username": "u1"}]))
        with pytest.raises(AccountConfigError, match="missing required field"):
            load_accounts(str(p))

    def test_duplicate_names_rejected(self, tmp_path):
        p = tmp_path / "accounts.json"
        dupes = [VALID_ACCOUNTS[0], VALID_ACCOUNTS[0]]
        p.write_text(json.dumps(dupes))
        with pytest.raises(AccountConfigError, match="Duplicate"):
            load_accounts(str(p))

    def test_not_a_list_rejected(self, tmp_path):
        p = tmp_path / "accounts.json"
        p.write_text(json.dumps({"name": "acct1"}))
        with pytest.raises(AccountConfigError, match="non-empty JSON array"):
            load_accounts(str(p))

    def test_empty_list_rejected(self, tmp_path):
        p = tmp_path / "accounts.json"
        p.write_text(json.dumps([]))
        with pytest.raises(AccountConfigError, match="non-empty JSON array"):
            load_accounts(str(p))

    def test_get_account_by_name(self, tmp_path):
        p = tmp_path / "accounts.json"
        p.write_text(json.dumps(VALID_ACCOUNTS))
        accounts = load_accounts(str(p))
        assert get_account_by_name(accounts, "acct2").username == "u2"
        assert get_account_by_name(accounts, "nope") is None
