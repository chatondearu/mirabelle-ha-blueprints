"""Tests for Cover Manager cover entity."""

from __future__ import annotations

import asyncio

import pytest
from homeassistant.components.cover import (
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_SET_COVER_POSITION,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cover_manager.const import DOMAIN


async def _setup_cover(hass: HomeAssistant, *, travel_time: int = 2) -> str:
    """Set up a Cover Manager cover and return its entity_id."""
    async def _mock_switch_turn_on(call) -> None:  # noqa: ANN001
        """Allow Cover Manager pulses without a full switch platform."""
        entity_id = call.data.get("entity_id")
        targets = entity_id if isinstance(entity_id, list) else [entity_id]
        for target in targets:
            if target:
                hass.states.async_set(target, "on", {})
                hass.states.async_set(target, "off", {})

    if not hass.services.has_service("switch", "turn_on"):
        hass.services.async_register("switch", "turn_on", _mock_switch_turn_on)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Ctx Cover",
            "switch_entity": "switch.ctx_cover",
            "travel_time": travel_time,
            "initial_position": 50,
            "pulse_gap": 0.05,
            "acceleration_duration": 0,
        },
        title="Ctx Cover",
    )
    entry.add_to_hass(hass)
    hass.states.async_set("switch.ctx_cover", "off", {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entities = [
        e
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == COVER_DOMAIN
    ]
    assert len(entities) == 1
    return entities[0].entity_id


@pytest.mark.asyncio
async def test_cover_initial_position(hass: HomeAssistant) -> None:
    """Cover should expose configured initial position after setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Test Cover",
            "switch_entity": "switch.test_cover",
            "travel_time": 30,
            "initial_position": 25,
            "pulse_gap": 0.8,
            "acceleration_duration": 0,
        },
        title="Test Cover",
    )
    entry.add_to_hass(hass)
    hass.states.async_set("switch.test_cover", "off", {})

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    cover_entities = [e for e in entities if e.domain == COVER_DOMAIN]
    assert len(cover_entities) == 1

    state = hass.states.get(cover_entities[0].entity_id)
    assert state is not None
    assert int(round(state.attributes.get("position", 0))) == 25


@pytest.mark.asyncio
async def test_set_position_preserves_service_parent_context(hass: HomeAssistant) -> None:
    """Position ticks during set_cover_position must keep the service parent_id."""
    entity_id = await _setup_cover(hass, travel_time=2)
    parent = Context()
    child = Context(parent_id=parent.id)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 100},
        blocking=False,
        context=child,
    )
    await asyncio.sleep(0.5)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.context.parent_id == parent.id


@pytest.mark.asyncio
async def test_switch_driven_move_has_no_parent_context(hass: HomeAssistant) -> None:
    """Wall-switch moves must not inherit a fabricated automation parent_id."""
    entity_id = await _setup_cover(hass, travel_time=2)
    hass.states.async_set("switch.ctx_cover", "on", {}, context=Context())
    await asyncio.sleep(0.5)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state in ("opening", "closing", "open", "closed")
    assert state.context.parent_id is None
