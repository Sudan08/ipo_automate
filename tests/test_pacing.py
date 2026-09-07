"""
Tests for the human-like pacing of a run.

MeroShare sees a session that fills the whole application form in a few hundred
milliseconds, with each value arriving as one input event, as a script. These
cover the pauses and the character-by-character typing that avoid that.
"""

import pytest

from meroshare.client import MeroshareClient


class FakeField:
    def __init__(self):
        self.sent = []
        self.cleared = 0

    def clear(self):
        self.cleared += 1

    def send_keys(self, value):
        self.sent.append(value)


def make_client(**kwargs):
    return MeroshareClient(
        username="u",
        password="p",
        dp_id="1",
        crn="1234567890123456",
        transaction_pin="1234",
        **kwargs,
    )


class TestPause:
    def test_pace_zero_removes_the_pauses(self, monkeypatch):
        slept = []
        monkeypatch.setattr("meroshare.client.time.sleep", slept.append)

        make_client(pace=0)._pause("anything")

        assert slept == []

    def test_pauses_are_randomised_not_a_fixed_delay(self, monkeypatch):
        """A constant delay is as machine-like as none, only slower."""
        slept = []
        monkeypatch.setattr("meroshare.client.time.sleep", slept.append)

        client = make_client()
        for _ in range(20):
            client._pause()

        low, high = MeroshareClient.STEP_PAUSE
        assert all(low <= delay <= high for delay in slept)
        assert len(set(slept)) > 1

    def test_pace_scales_the_delay(self, monkeypatch):
        slept = []
        monkeypatch.setattr("meroshare.client.time.sleep", slept.append)

        make_client(pace=3)._pause()

        low, high = MeroshareClient.STEP_PAUSE
        assert low * 3 <= slept[0] <= high * 3

    def test_a_negative_pace_is_treated_as_no_pause(self):
        assert make_client(pace=-5).pace == 0


class TestTyping:
    def test_values_are_typed_one_character_at_a_time(self, monkeypatch):
        monkeypatch.setattr("meroshare.client.time.sleep", lambda _: None)
        field = FakeField()

        make_client()._type(field, "1234")

        assert field.sent == ["1", "2", "3", "4"]
        assert field.cleared == 1

    def test_non_string_values_are_typed_too(self, monkeypatch):
        monkeypatch.setattr("meroshare.client.time.sleep", lambda _: None)
        field = FakeField()

        make_client()._type(field, 10)

        assert field.sent == ["1", "0"]

    def test_pace_zero_sends_the_whole_value_at_once(self):
        field = FakeField()

        make_client(pace=0)._type(field, "1234")

        assert field.sent == ["1234"]
