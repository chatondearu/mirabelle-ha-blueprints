from pathlib import Path


PANEL_SOURCE = (
    Path(__file__).parents[1]
    / "custom_components"
    / "cda_alarm"
    / "frontend"
    / "cda-alarm-panel.js"
).read_text()


def test_camera_proxy_requires_access_token() -> None:
    assert "attributes?.access_token" in PANEL_SOURCE
    assert "?token=${encodeURIComponent(" in PANEL_SOURCE
    assert "accessToken" in PANEL_SOURCE
    assert 'src=${`/api/camera_proxy/${camera.entity_id}`}' not in PANEL_SOURCE


def test_access_select_uses_current_home_assistant_items() -> None:
    assert "<ha-list-item" in PANEL_SOURCE
    assert "<mwc-list-item" not in PANEL_SOURCE
    assert "@closed=${(e) => e.stopPropagation()}" in PANEL_SOURCE


def test_form_fields_use_native_inputs() -> None:
    assert "<ha-textarea" not in PANEL_SOURCE
    assert "<ha-textfield" not in PANEL_SOURCE
    assert "_setNumberField" in PANEL_SOURCE
    assert "_eventValue" in PANEL_SOURCE


def test_codes_editor_uses_structured_rows() -> None:
    assert 'aria-label="Code name"' in PANEL_SOURCE
    assert 'aria-label="PIN"' in PANEL_SOURCE
    assert 'aria-label="RFID"' in PANEL_SOURCE
    assert 'aria-label="NFC tag id"' in PANEL_SOURCE
    assert "Add code" in PANEL_SOURCE
    assert "Codes (JSON)" not in PANEL_SOURCE
    assert "_codesJson" not in PANEL_SOURCE


def test_dashboard_pin_dialog_markers() -> None:
    assert "_pinDialogOpen" in PANEL_SOURCE
    assert "_pendingService" in PANEL_SOURCE
    assert "Enter PIN" in PANEL_SOURCE
    assert "code_required" in PANEL_SOURCE
    assert 'service === "alarm_disarm" && this._dashboard?.code_required' in PANEL_SOURCE


def test_failed_dashboard_load_has_retry_backoff() -> None:
    assert "this._nextDashboardRetryAt = Date.now() + 5000" in PANEL_SOURCE
    assert "Date.now() >= this._nextDashboardRetryAt" in PANEL_SOURCE
