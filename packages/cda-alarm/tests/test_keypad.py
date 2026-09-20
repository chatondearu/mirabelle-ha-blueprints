"""Tests for the Frient keypad event listener."""

from __future__ import annotations

import pytest
from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    SERVICE_ALARM_TRIGGER,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm.const import (
    CONF_ENABLE_KEYPAD_FEEDBACK,
    CONF_FRIENT_DEVICE_ID,
    CONF_KEYPAD_ENDPOINT,
    DOMAIN,
)

KEYPAD_IEEE = "00:0d:6f:00:0a:90:69:e7"
ZHA_DOMAIN = "zha"
ZHA_FEEDBACK_SERVICE = "issue_zigbee_cluster_command"


async def _setup_panel(hass: HomeAssistant, **overrides) -> str:
    data = {
        "name": "CDA Alarm",
        "codes": [{"name": "alice", "pin": "1234"}],
        "sensors_away": [],
        "sensors_home": [],
        "sensors_night": [],
        "entry_delay": 0,
        "exit_delay": 0,
        "block_arm_if_open": True,
        "frient_device_id": "device-frient-1",
        **overrides,
    }
    if data.get(CONF_ENABLE_KEYPAD_FEEDBACK):
        zha_entry = MockConfigEntry(domain=ZHA_DOMAIN)
        zha_entry.add_to_hass(hass)
        keypad_device = dr.async_get(hass).async_get_or_create(
            config_entry_id=zha_entry.entry_id,
            identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)},
        )
        data[CONF_FRIENT_DEVICE_ID] = keypad_device.id

    entry = MockConfigEntry(domain=DOMAIN, data=data, title="CDA Alarm")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entities = [
        entity
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
        if entity.domain == ALARM_DOMAIN
    ]
    assert len(entities) == 1
    return entities[0].entity_id


def _fire_keypad_event(
    hass: HomeAssistant,
    *,
    arm_mode: int,
    code: str | None = "1234",
    code_field: str = "code",
    device_id: str = "device-frient-1",
) -> None:
    params: dict[str, object] = {"arm_mode": arm_mode}
    if code is not None:
        params[code_field] = code
    hass.bus.async_fire(
        "zha_event",
        {
            "device_id": device_id,
            "command": "arm",
            "args": [],
            "params": params,
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("arm_mode", "expected_state"),
    [
        (1, STATE_ALARM_ARMED_HOME),
        (2, STATE_ALARM_ARMED_NIGHT),
        (3, STATE_ALARM_ARMED_AWAY),
    ],
)
async def test_frient_event_arms_configured_mode(
    hass: HomeAssistant,
    arm_mode: int,
    expected_state: str,
) -> None:
    entity_id = await _setup_panel(hass)

    _fire_keypad_event(hass, arm_mode=arm_mode)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == expected_state


@pytest.mark.asyncio
async def test_frient_event_ignores_wrong_device(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)

    _fire_keypad_event(hass, arm_mode=3, device_id="another-device")
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_frient_event_rejects_bad_disarm_code_and_restores_feedback(
    hass: HomeAssistant,
) -> None:
    calls: list[ServiceCall] = []

    async def capture_feedback(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(ZHA_DOMAIN, ZHA_FEEDBACK_SERVICE, capture_feedback)
    entity_id = await _setup_panel(
        hass,
        **{
            CONF_ENABLE_KEYPAD_FEEDBACK: True,
            CONF_KEYPAD_ENDPOINT: 44,
        },
    )
    device_id = dr.async_get(hass).async_get_device(
        identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)}
    ).id

    _fire_keypad_event(hass, arm_mode=3, code=None, device_id=device_id)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY
    assert len(calls) >= 1

    _fire_keypad_event(hass, arm_mode=0, code="0000", device_id=device_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ALARM_ARMED_AWAY


@pytest.mark.asyncio
async def test_frient_event_disarms_cda_panel(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_TRIGGER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_TRIGGERED

    _fire_keypad_event(hass, arm_mode=0)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_frient_event_pushes_enabled_keypad_feedback(
    hass: HomeAssistant,
) -> None:
    calls: list[ServiceCall] = []

    async def capture_feedback(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(
        ZHA_DOMAIN,
        ZHA_FEEDBACK_SERVICE,
        capture_feedback,
    )
    entity_id = await _setup_panel(
        hass,
        **{
            CONF_ENABLE_KEYPAD_FEEDBACK: True,
            CONF_KEYPAD_ENDPOINT: 44,
        },
    )

    _fire_keypad_event(
        hass,
        arm_mode=3,
        device_id=dr.async_get(hass).async_get_device(
            identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)}
        ).id,
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY
    assert len(calls) == 1
    assert calls[0].data == {
        "ieee": KEYPAD_IEEE,
        "endpoint_id": 44,
        "cluster_id": 1281,
        "cluster_type": "out",
        "command": 4,
        "command_type": "client",
        "args": [3, 0, 0, 0],
    }


@pytest.mark.asyncio
async def test_frient_feedback_failure_does_not_block_arming(
    hass: HomeAssistant,
) -> None:
    attempts = 0

    async def reject_feedback(call: ServiceCall) -> None:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("ZHA rejected keypad feedback")

    hass.services.async_register(
        ZHA_DOMAIN,
        ZHA_FEEDBACK_SERVICE,
        reject_feedback,
    )
    entity_id = await _setup_panel(
        hass,
        **{
            CONF_ENABLE_KEYPAD_FEEDBACK: True,
            CONF_KEYPAD_ENDPOINT: 44,
        },
    )

    _fire_keypad_event(
        hass,
        arm_mode=1,
        device_id=dr.async_get(hass).async_get_device(
            identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)}
        ).id,
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_HOME
    assert attempts == 1


@pytest.mark.asyncio
async def test_frient_event_arms_with_rfid_badge(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(
        hass,
        codes=[{"name": "bob", "rfid": "AA:BB:CC:DD"}],
    )

    _fire_keypad_event(hass, arm_mode=3, code="AA:BB:CC:DD")
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY


@pytest.mark.asyncio
async def test_frient_event_accepts_arm_disarm_code_field(
    hass: HomeAssistant,
) -> None:
    entity_id = await _setup_panel(hass)

    _fire_keypad_event(hass, arm_mode=3, code_field="arm_disarm_code")
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY


@pytest.mark.asyncio
async def test_frient_event_without_code_arms_when_no_codes_configured(
    hass: HomeAssistant,
) -> None:
    entity_id = await _setup_panel(hass, codes=[])

    _fire_keypad_event(hass, arm_mode=3, code=None)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY


@pytest.mark.asyncio
async def test_frient_feedback_reports_rejected_arm_as_disarmed(
    hass: HomeAssistant,
) -> None:
    calls: list[ServiceCall] = []

    async def capture_feedback(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(ZHA_DOMAIN, ZHA_FEEDBACK_SERVICE, capture_feedback)
    hass.states.async_set("binary_sensor.front_door", "on", {})
    entity_id = await _setup_panel(
        hass,
        **{
            "sensors_away": ["binary_sensor.front_door"],
            CONF_ENABLE_KEYPAD_FEEDBACK: True,
            CONF_KEYPAD_ENDPOINT: 44,
        },
    )

    _fire_keypad_event(
        hass,
        arm_mode=3,
        device_id=dr.async_get(hass).async_get_device(
            identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)}
        ).id,
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED
    assert len(calls) == 1
    assert calls[0].data["args"] == [0, 0, 0, 0]


@pytest.mark.asyncio
async def test_sync_zha_panel_mirrors_disarm(hass: HomeAssistant) -> None:
    from unittest.mock import AsyncMock, patch
    from homeassistant.components.alarm_control_panel import SERVICE_ALARM_DISARM
    from custom_components.cda_alarm.const import CONF_KEYPADS

    zha_entry = MockConfigEntry(domain=ZHA_DOMAIN)
    zha_entry.add_to_hass(hass)
    keypad_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)},
        manufacturer="frient A/S",
        model="KEPZB-110",
    )
    entity_id = await _setup_panel(
        hass,
        **{
            CONF_FRIENT_DEVICE_ID: keypad_device.id,
            CONF_KEYPADS: [{
                "device_id": keypad_device.id,
                "is_default": True,
                "feedback": False,
                "sync_zha_panel": True,
                "endpoint": 44,
            }],
        },
    )
    await hass.services.async_call(
        ALARM_DOMAIN, "alarm_arm_away", {ATTR_ENTITY_ID: entity_id, "code": "1234"}, blocking=True
    )
    await hass.async_block_till_done()
    with patch(
        "custom_components.cda_alarm.keypad._async_mirror_zha_panel",
        new_callable=AsyncMock,
    ) as mirror:
        await hass.services.async_call(
            ALARM_DOMAIN, SERVICE_ALARM_DISARM, {ATTR_ENTITY_ID: entity_id, "code": "1234"}, blocking=True
        )
        await hass.async_block_till_done()
        mirror.assert_awaited()
        assert any(
            call.args[1] == keypad_device.id and call.args[2] == STATE_ALARM_DISARMED
            for call in mirror.await_args_list
        )
    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_sync_zha_panel_disabled_skips_mirror(hass: HomeAssistant) -> None:
    from unittest.mock import AsyncMock, patch
    from homeassistant.components.alarm_control_panel import SERVICE_ALARM_DISARM
    from custom_components.cda_alarm.const import CONF_KEYPADS

    zha_entry = MockConfigEntry(domain=ZHA_DOMAIN)
    zha_entry.add_to_hass(hass)
    keypad_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)},
    )
    entity_id = await _setup_panel(
        hass,
        **{
            CONF_KEYPADS: [{
                "device_id": keypad_device.id,
                "is_default": True,
                "feedback": False,
                "sync_zha_panel": False,
                "endpoint": 44,
            }],
        },
    )
    with patch("custom_components.cda_alarm.keypad._async_mirror_zha_panel", new_callable=AsyncMock) as mirror:
        await hass.services.async_call(
            ALARM_DOMAIN, SERVICE_ALARM_DISARM, {ATTR_ENTITY_ID: entity_id, "code": "1234"}, blocking=True
        )
        await hass.async_block_till_done()
        mirror.assert_not_called()


@pytest.mark.asyncio
async def test_sync_zha_mirror_suppresses_echo_arm_events(hass: HomeAssistant) -> None:
    """ZHA mirror service calls must not re-enter CDA via echoed keypad events."""
    from unittest.mock import AsyncMock, patch
    from custom_components.cda_alarm.const import CONF_KEYPADS

    zha_entry = MockConfigEntry(domain=ZHA_DOMAIN)
    zha_entry.add_to_hass(hass)
    keypad_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)},
        manufacturer="frient A/S",
        model="KEPZB-110",
    )
    entity_id = await _setup_panel(
        hass,
        **{
            CONF_KEYPADS: [{
                "device_id": keypad_device.id,
                "is_default": True,
                "feedback": False,
                "sync_zha_panel": True,
                "endpoint": 44,
            }],
        },
    )
    with patch(
        "custom_components.cda_alarm.keypad._async_mirror_zha_panel",
        new_callable=AsyncMock,
    ):
        await hass.services.async_call(
            ALARM_DOMAIN,
            "alarm_arm_away",
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY

        # Echoed disarm from the physical keypad right after mirror.
        _fire_keypad_event(hass, arm_mode=0, code="1234", device_id=keypad_device.id)
        await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY
