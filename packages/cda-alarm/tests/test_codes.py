"""Tests for CDA Alarm code matching."""

from __future__ import annotations

from custom_components.cda_alarm.codes import match_code

CODES = [
    {"name": "alice", "pin": "1234", "rfid": "AABBCC", "nfc_tag_id": "tag-alice"},
    {"name": "bob", "pin": "9999"},
]


def test_match_pin() -> None:
    assert match_code(CODES, pin="1234")["name"] == "alice"


def test_match_rfid_case_insensitive() -> None:
    assert match_code(CODES, rfid="aabbcc")["name"] == "alice"


def test_match_nfc() -> None:
    assert match_code(CODES, nfc_tag_id="tag-alice")["name"] == "alice"


def test_no_match() -> None:
    assert match_code(CODES, pin="0000") is None


def test_empty_codes() -> None:
    assert match_code([], pin="1234") is None
