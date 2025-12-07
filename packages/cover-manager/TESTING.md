# Cover Manager - Testing Checklist

## Quick Test Script

Use this checklist to verify the integration works correctly:

### Pre-Installation Checks

- [ ] Home Assistant version is 2025.5.3 or later
- [ ] HACS is installed (if using HACS method)
- [ ] A switch entity exists to control the cover
- [ ] Switch entity is accessible and working

### Installation Verification

- [ ] Integration appears in HACS or custom_components directory
- [ ] Integration shows in **Settings** > **Devices & Services**
- [ ] Integration status is "Loaded" (green)
- [ ] No errors in Home Assistant logs

### Entity Creation Verification

- [ ] Cover entity created: `cover.<cover_name>`
- [ ] Position helper created: `input_text.<cover_name>_position`
- [ ] Direction helper created: `input_text.<cover_name>_direction`
- [ ] All entities appear in **Settings** > **Devices & Services** > **Entities**

### Functional Tests

#### Test 1: Open Cover
- [ ] Call service: `cover.open_cover` on cover entity
- [ ] Switch turns ON
- [ ] After travel time, switch turns OFF
- [ ] Position helper = 100
- [ ] Cover entity state = "open"

#### Test 2: Close Cover
- [ ] Call service: `cover.close_cover` on cover entity
- [ ] Switch turns ON
- [ ] After travel time, switch turns OFF
- [ ] Position helper = 0
- [ ] Cover entity state = "closed"

#### Test 3: Set Position (50%)
- [ ] Call service: `cover.set_cover_position` with `position: 50`
- [ ] Switch turns ON
- [ ] After half travel time, switch turns OFF
- [ ] Position helper = 50
- [ ] Cover entity position = 50%

#### Test 4: Stop Cover
- [ ] While cover is moving, call service: `cover.stop_cover`
- [ ] Switch turns OFF immediately
- [ ] Direction helper = "stopped"
- [ ] Cover entity state = "stopped"

#### Test 5: UI Controls
- [ ] Cover card appears in Lovelace
- [ ] Slider works to set position
- [ ] Open button works
- [ ] Close button works
- [ ] Stop button works
- [ ] Icon updates based on state

### Edge Cases

#### Test 6: Rapid Commands
- [ ] Send open command, then immediately send close command
- [ ] Verify no conflicts or errors

#### Test 7: Invalid Position
- [ ] Try to set position > 100 (should be clamped to 100)
- [ ] Try to set position < 0 (should be clamped to 0)

#### Test 8: Switch State
- [ ] Manually turn switch ON
- [ ] Verify direction helper updates
- [ ] Manually turn switch OFF
- [ ] Verify direction helper = "stopped"

### Configuration Files Verification

- [ ] Helper file created: `configuration/packages/cover_manager_<cover_id>_helpers.yaml`
- [ ] Cover config added: `configuration/covers.yaml`
- [ ] Script exists: `scripts/set_cover_position.yaml`

### Log Verification

- [ ] No errors in Home Assistant logs
- [ ] Info log: "Cover Manager setup completed for <name>"
- [ ] No warnings about missing entities or services

## Automated Test Script

You can use this YAML automation to test the cover:

```yaml
automation:
  - alias: "Test Cover Manager"
    description: "Automated test for Cover Manager integration"
    trigger:
      - platform: event
        event_type: test_cover_manager
    action:
      - service: cover.set_cover_position
        target:
          entity_id: cover.living_room_blind  # Replace with your cover entity
        data:
          position: 25
      - delay:
          seconds: 35  # Wait for movement + buffer
      - service: cover.set_cover_position
        target:
          entity_id: cover.living_room_blind
        data:
          position: 75
      - delay:
          seconds: 35
      - service: cover.close_cover
        target:
          entity_id: cover.living_room_blind
      - delay:
          seconds: 35
      - service: cover.open_cover
        target:
          entity_id: cover.living_room_blind
```

To trigger the test:
1. Go to **Developer Tools** > **Events**
2. Event: `test_cover_manager`
3. Click **Fire Event**

## Performance Tests

- [ ] Response time: Cover responds within 1 second of command
- [ ] Position accuracy: Position is within ±5% of target
- [ ] Multiple covers: Can create and control multiple covers simultaneously
- [ ] Memory: No memory leaks after extended use

## Integration with Other Components

- [ ] Works with automations
- [ ] Works with scenes
- [ ] Works with scripts
- [ ] Works with blueprints
- [ ] Appears in energy dashboard (if applicable)

## Troubleshooting Test

If any test fails:

1. **Check Logs**
   ```bash
   # In Home Assistant logs, filter for:
   cover_manager
   ```

2. **Verify Configuration**
   - Check `configuration.yaml` includes `covers.yaml`
   - Verify helpers are in `configuration/packages/`

3. **Manual Verification**
   - Test switch entity directly
   - Check helper values manually
   - Verify script exists and is valid

4. **Reset and Retry**
   - Remove integration
   - Delete created files
   - Reinstall and reconfigure

## Success Criteria

All tests should pass for a successful installation:
- ✅ All entities created
- ✅ All services work correctly
- ✅ UI controls functional
- ✅ No errors in logs
- ✅ Position tracking accurate
- ✅ Integration stable over time
