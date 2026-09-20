"""Code matching for CDA Alarm."""

from __future__ import annotations

from typing import Any


def match_code(
    codes: list[dict[str, Any]],
    *,
    pin: str | None = None,
    rfid: str | None = None,
    nfc_tag_id: str | None = None,
) -> dict[str, Any] | None:
    """Return the first code entry matching pin, RFID, or NFC tag id."""
    pin_n = (pin or "").strip()
    rfid_n = (rfid or "").strip().lower()
    nfc_n = (nfc_tag_id or "").strip()
    for entry in codes:
        if pin_n and str(entry.get("pin") or "") == pin_n:
            return entry
        if rfid_n and str(entry.get("rfid") or "").strip().lower() == rfid_n:
            return entry
        if nfc_n and str(entry.get("nfc_tag_id") or "") == nfc_n:
            return entry
    return None
