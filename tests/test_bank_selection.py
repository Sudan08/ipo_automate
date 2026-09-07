"""
Tests for the bank / bank-account dropdown selection in the apply form.

These cover the regression where the bank was picked by a hardcoded option
value ('37') and the bank account by the CRN - neither of which is stable
across MeroShare accounts.
"""

import pytest

from meroshare import client as client_module
from meroshare.client import MeroshareClient


class FakeOption:
    def __init__(self, value, text):
        self._value = value
        self.text = text

    def get_attribute(self, name):
        assert name == "value"
        return self._value


class FakeSelect:
    """Stands in for selenium's Select over a dropdown that may reload.

    `option_states` is a list of option lists: each read of the dropdown pops the
    next state, and the last one repeats forever - so a test can describe a bank
    account list that arrives late, or one that changes under the code's feet.
    """

    def __init__(self, option_states):
        self.option_states = list(option_states)
        self.selected = None
        self.reads = 0

    @property
    def options(self):
        self.reads += 1
        if len(self.option_states) > 1:
            return self.option_states.pop(0)
        return self.option_states[0]

    def select_by_value(self, value):
        self.selected = value

    @property
    def first_selected_option(self):
        return FakeOption(self.selected, "")


class FakeElement:
    def __init__(self, enabled_after=0):
        self.enabled_after = enabled_after
        self.checks = 0

    def is_enabled(self):
        self.checks += 1
        return self.checks > self.enabled_after


class FakeDriver:
    def __init__(self, element=None):
        self.element = element or FakeElement()

    def find_element(self, by, value):
        return self.element


def make_client(**kwargs):
    kwargs.setdefault("pace", 0)
    client = MeroshareClient(
        username="u",
        password="p",
        dp_id="1",
        crn="1234567890123456",
        transaction_pin="1234",
        **kwargs,
    )
    client.POLL_INTERVAL = 0  # tests should not sit through real poll delays
    return client


def install_select(monkeypatch, options, *, states=None):
    """Make Select(...) return a FakeSelect holding `options`.

    Pass `states` instead to describe a dropdown whose options change between
    reads, e.g. a bank-account list that is still loading.
    """
    select = FakeSelect(states if states is not None else [options])
    monkeypatch.setattr(client_module, "Select", lambda element: select)
    monkeypatch.setattr(
        client_module.EC, "presence_of_element_located", lambda locator: (lambda d: True)
    )
    return select


class TestRealOptions:
    """Placeholder rows must not be mistaken for real choices."""

    @pytest.mark.parametrize(
        "value,text",
        [
            ("", "Select Bank"),
            ("? undefined:undefined ?", ""),
            ("null", "Select Account"),
            ("11", "Select Bank"),
        ],
    )
    def test_placeholders_are_filtered_out(self, value, text):
        select = FakeSelect([[FakeOption(value, text)]])
        assert MeroshareClient._real_options(select) == []

    def test_real_options_are_kept(self):
        options = [
            FakeOption("", "Select Bank"),
            FakeOption("37", "Nabil Bank Limited"),
            FakeOption("42", "Global IME Bank"),
        ]
        select = FakeSelect([options])
        assert MeroshareClient._real_options(select) == options[1:]


class TestSelectDropdownOption:
    def test_single_option_is_used_without_configuration(self, monkeypatch):
        """The old code needed the bank id up front; one linked bank needs none."""
        select = install_select(monkeypatch, [FakeOption("42", "Global IME Bank")])
        c = make_client()
        c.driver = FakeDriver()

        chosen = c._select_dropdown_option("selectBank", "bank")

        assert chosen == "Global IME Bank"
        assert select.selected == "42"

    def test_configured_bank_matches_by_name_not_by_id(self, monkeypatch):
        select = install_select(
            monkeypatch,
            [FakeOption("37", "Nabil Bank Limited"), FakeOption("42", "Global IME Bank")],
        )
        c = make_client(bank="global ime")
        c.driver = FakeDriver()

        chosen = c._select_dropdown_option("selectBank", "bank", c.bank)

        assert chosen == "Global IME Bank"
        assert select.selected == "42"

    def test_configured_bank_may_also_be_the_option_value(self, monkeypatch):
        select = install_select(
            monkeypatch,
            [FakeOption("37", "Nabil Bank Limited"), FakeOption("42", "Global IME Bank")],
        )
        c = make_client(bank="37")
        c.driver = FakeDriver()

        chosen = c._select_dropdown_option("selectBank", "bank", c.bank)
        assert chosen == "Nabil Bank Limited"

    def test_unmatched_bank_reports_what_was_available(self, monkeypatch):
        install_select(monkeypatch, [FakeOption("42", "Global IME Bank")])
        c = make_client(bank="Nabil")
        c.driver = FakeDriver()

        with pytest.raises(RuntimeError, match="Global IME Bank"):
            c._select_dropdown_option("selectBank", "bank", c.bank)

    def test_first_of_several_is_used_when_unconfigured(self, monkeypatch):
        select = install_select(
            monkeypatch,
            [FakeOption("37", "Nabil Bank Limited"), FakeOption("42", "Global IME Bank")],
        )
        c = make_client()
        c.driver = FakeDriver()

        assert c._select_dropdown_option("selectBank", "bank") == "Nabil Bank Limited"
        assert select.selected == "37"


class TestWaitingForOptions:
    """The account list arrives over the network after a bank is picked."""

    def test_waits_until_the_option_list_settles(self, monkeypatch):
        """A list that is still changing must not be read as final.

        This is the regression behind "logs say applied, MeroShare says not":
        the first non-empty read held the previous bank's account, the form was
        submitted with it, and the application was silently dropped.
        """
        stale = [FakeOption("11", "0011000001 - Old Bank")]
        final = [FakeOption("99", "9900000009 - New Bank")]
        select = install_select(monkeypatch, None, states=[stale, final, final])
        c = make_client()
        c.driver = FakeDriver()

        chosen = c._select_dropdown_option("accountNumber", "bank account")

        assert chosen == "9900000009 - New Bank"
        assert select.selected == "99"

    def test_waits_while_the_dropdown_is_still_disabled(self, monkeypatch):
        options = [FakeOption("42", "Global IME Bank")]
        install_select(monkeypatch, options)
        c = make_client()
        c.driver = FakeDriver(FakeElement(enabled_after=3))

        assert c._select_dropdown_option("selectBank", "bank") == "Global IME Bank"

    def test_a_list_that_never_loads_is_an_error(self, monkeypatch):
        install_select(monkeypatch, [])
        c = make_client()
        c.driver = FakeDriver()

        with pytest.raises(RuntimeError, match="never finished loading"):
            c._wait_for_options("accountNumber", "bank account", timeout=0.2)


class TestVerifySelection:
    def test_a_selection_that_does_not_stick_is_an_error(self, monkeypatch):
        install_select(monkeypatch, [FakeOption("42", "Global IME Bank")])
        c = make_client()
        c.driver = FakeDriver()

        with pytest.raises(RuntimeError, match="would not stay selected"):
            c._verify_selection("selectBank", "bank", "42", timeout=0.2)
