# Cover Manager - Logic Specification

## Switch Behavior
The cover is controlled by an **impulse switch** (single button):
- Each pulse cycles through states: **idle** → **opening** → **idle** → **closing** → **idle** → **opening** → ...
- The cycle is: `idle → opening → idle → closing → idle → opening → idle → closing → ...`
- **Important**: Each pulse advances to the next state in the cycle
  - From `idle` (last=opening): pulse → `closing` (next in cycle after opening→idle)
  - From `opening`: pulse → `idle` (stops opening)
  - From `idle` (last=closing): pulse → `opening` (next in cycle after closing→idle)
  - From `closing`: pulse → `idle` (stops closing)
- **Key insight**: When at `idle`, the next state depends on `last_direction`:
  - If `last_direction` = `opening`: we came from opening→idle, so next is `closing`
  - If `last_direction` = `closing`: we came from closing→idle, so next is `opening`
- If the cover is stopped mid-travel, the next activation will reverse direction
- If the cover reaches 0% or 100%, it stops automatically (no pulse needed)

## State Variables

### Internal State
- `position`: Current position (0-100%)
- `direction`: Current direction (`idle`, `opening`, `closing`)
- `last_direction`: Last known direction when idle (`opening` or `closing`)
- `travel_time`: Time to travel from 0% to 100% (seconds)
- `pulse_gap`: Delay between automatic pulses (seconds)

### Physical Switch State
- The switch cycles through: `idle` → `opening` → `idle` → `closing` → `idle` → `opening` → ...
- **Each pulse advances to the next state in the cycle**
- **Cycle behavior**:
  - From `idle` (last=opening): pulse → `closing` (next in cycle after opening→idle)
  - From `opening`: pulse → `idle` (stops opening)
  - From `idle` (last=closing): pulse → `opening` (next in cycle after closing→idle)
  - From `closing`: pulse → `idle` (stops closing)
- When cover is `idle`, the switch is in `idle` state, and `last_direction` indicates what the last movement direction was
- When cover is `opening`, the switch is in `opening` state
- When cover is `closing`, the switch is in `closing` state
- **To start movement**: Need to pulse from `idle` to the desired direction
  - If `last_direction` = desired direction: Need 3 pulses (complete cycle: idle→opposite→idle→desired)
  - If `last_direction` ≠ desired direction: Need 1 pulse (go directly to desired, which is next in cycle)

## All Possible Cases

### Case 1: Cover is IDLE at position X, user requests OPEN
**Conditions:**
- `direction` = `idle`
- `position` = X (any value)
- `last_direction` = `opening` or `closing`
- User action: `async_open_cover()` or `async_set_cover_position(target > X)`

**Expected Behavior:**
1. Cover is `idle`, switch is in `idle` state
2. If `last_direction` = `opening`:
   - Switch is at `idle` (after opening→idle)
   - Next in cycle: `idle` → `closing` (not opening!)
   - To get to `opening`: Send 3 pulses
     - Pulse 1: `idle` → `closing` (advance cycle)
     - Pulse 2: `closing` → `idle` (continue cycle)
     - Pulse 3: `idle` → `opening` (arrive at opening and start)
3. If `last_direction` = `closing`:
   - Switch is at `idle` (after closing→idle)
   - Next in cycle: `idle` → `opening` ✓
   - Send 1 pulse: `idle` → `opening` and start
4. Update `direction` = `opening`, `last_direction` = `opening`
5. Start movement loop

---

### Case 2: Cover is IDLE at position X, user requests CLOSE
**Conditions:**
- `direction` = `idle`
- `position` = X (any value)
- `last_direction` = `opening` or `closing`
- User action: `async_close_cover()` or `async_set_cover_position(target < X)`

**Expected Behavior:**
1. Cover is `idle`, switch is in `idle` state
2. If `last_direction` = `closing`:
   - Switch is at `idle` (after closing→idle)
   - Next in cycle: `idle` → `opening` (not closing!)
   - To get to `closing`: Send 3 pulses
     - Pulse 1: `idle` → `opening` (advance cycle)
     - Pulse 2: `opening` → `idle` (continue cycle)
     - Pulse 3: `idle` → `closing` (arrive at closing and start)
3. If `last_direction` = `opening`:
   - Switch is at `idle` (after opening→idle)
   - Next in cycle: `idle` → `closing` ✓
   - Send 1 pulse: `idle` → `closing` and start
4. Update `direction` = `closing`, `last_direction` = `closing`
5. Start movement loop

---

### Case 3: Cover is OPENING, user requests OPEN (same direction)
**Conditions:**
- `direction` = `opening`
- `position` = X
- User action: `async_open_cover()` or `async_set_cover_position(target > X)`

**Expected Behavior:**
1. If target is different: Update target, continue movement (no pulse needed)
2. If target is same: Do nothing
3. Switch is already in opening state, no pulse needed

---

### Case 4: Cover is OPENING, user requests CLOSE (opposite direction)
**Conditions:**
- `direction` = `opening`
- `position` = X
- User action: `async_close_cover()` or `async_set_cover_position(target < X)`

**Expected Behavior:**
1. Calculate current position from elapsed time
2. Send 1 pulse to stop (switch goes from `opening` → `idle`)
3. Update `direction` = `idle`, `last_direction` = `opening`
4. Now switch is at `idle` (last=opening), next in cycle is `closing`
5. Send 1 pulse to start closing (switch goes from `idle` → `closing`)
6. Update `direction` = `closing`, `last_direction` = `closing`
7. Start movement loop in closing direction

---

### Case 5: Cover is CLOSING, user requests CLOSE (same direction)
**Conditions:**
- `direction` = `closing`
- `position` = X
- User action: `async_close_cover()` or `async_set_cover_position(target < X)`

**Expected Behavior:**
1. If target is different: Update target, continue movement (no pulse needed)
2. If target is same: Do nothing
3. Switch is already in closing state, no pulse needed

---

### Case 6: Cover is CLOSING, user requests OPEN (opposite direction)
**Conditions:**
- `direction` = `closing`
- `position` = X
- User action: `async_open_cover()` or `async_set_cover_position(target > X)`

**Expected Behavior:**
1. Calculate current position from elapsed time
2. Send 1 pulse to stop (switch goes from `closing` → `idle`)
3. Update `direction` = `idle`, `last_direction` = `closing`
4. Now switch is at `idle` (last=closing), next in cycle is `opening`
5. Send 1 pulse to start opening (switch goes from `idle` → `opening`)
6. Update `direction` = `opening`, `last_direction` = `opening`
7. Start movement loop in opening direction

---

### Case 7: Cover is MOVING, user requests STOP
**Conditions:**
- `direction` = `opening` or `closing`
- `position` = X
- User action: `async_stop_cover()`

**Expected Behavior:**
1. Calculate current position from elapsed time
2. Send 1 pulse to stop (switch goes from current direction → `idle`)
   - If was `opening`: `opening` → `idle`
   - If was `closing`: `closing` → `idle`
3. Update `direction` = `idle`
4. Update `last_direction` = previous `direction` (before stop)
5. Cancel movement loop

---

### Case 8: Cover reaches 0% naturally (during closing)
**Conditions:**
- `direction` = `closing`
- `position` reaches 0%
- Movement loop detects limit

**Expected Behavior:**
1. **DO NOT SEND PULSE** (cover is already stopped at limit)
2. Update `position` = 0%
3. Update `direction` = `idle`
4. Update `last_direction` = `closing` (was closing, now idle)
5. Cancel movement loop
6. Set `_last_limit_stop_time` to ignore subsequent pulses

---

### Case 9: Cover reaches 100% naturally (during opening)
**Conditions:**
- `direction` = `opening`
- `position` reaches 100%
- Movement loop detects limit

**Expected Behavior:**
1. **DO NOT SEND PULSE** (cover is already stopped at limit)
2. Update `position` = 100%
3. Update `direction` = `idle`
4. Update `last_direction` = `opening` (was opening, now idle)
5. Cancel movement loop
6. Set `_last_limit_stop_time` to ignore subsequent pulses

---

### Case 10: Physical switch activated while cover is IDLE
**Conditions:**
- `direction` = `idle`
- Physical switch is activated (state change event)
- `last_direction` = `opening` or `closing`

**Expected Behavior:**
1. Check if pulse should be ignored (within `_ignore_until` or `_last_limit_stop_time` window)
2. If ignored: Do nothing
3. If not ignored:
   - Toggle `last_direction` (opening ↔ closing)
   - Start movement in new direction
   - Update `direction` = new direction
   - Start movement loop

---

### Case 11: Physical switch activated while cover is MOVING
**Conditions:**
- `direction` = `opening` or `closing`
- Physical switch is activated (state change event)

**Expected Behavior:**
1. Check if pulse should be ignored (within `_ignore_until` window - automatic pulse)
2. If ignored: Do nothing (this was our automatic pulse)
3. If not ignored:
   - Calculate current position from elapsed time
   - Stop movement: `direction` = `idle`, `last_direction` = previous direction
   - Cancel movement loop
   - **DO NOT SEND PULSE** (user already activated switch, it already stopped)

---

### Case 12: Cover is IDLE at 0%, user requests OPEN
**Conditions:**
- `direction` = `idle`
- `position` = 0%
- `last_direction` = `closing` (MUST be closing, if not it's a bug - cover at 0% means it just finished closing)
- User action: `async_open_cover()` or `async_set_cover_position(target > 0)`

**Expected Behavior:**
1. Cover is `idle` at 0%, switch is in `idle` state
2. `last_direction` MUST be `closing` (cover at 0% means it just finished closing)
3. Switch is at `idle` (after closing→idle)
4. Next in cycle: `idle` → `opening` ✓
5. Send 1 pulse: `idle` → `opening` and start
6. Update `direction` = `opening`, `last_direction` = `opening`
7. Start movement loop
8. Clear `_last_limit_stop_time` (we're starting new movement)

---

### Case 13: Cover is IDLE at 100%, user requests CLOSE
**Conditions:**
- `direction` = `idle`
- `position` = 100%
- `last_direction` = `opening` (MUST be opening, if not it's a bug - cover at 100% means it just finished opening)
- User action: `async_close_cover()` or `async_set_cover_position(target < 100)`

**Expected Behavior:**
1. Cover is `idle` at 100%, switch is in `idle` state
2. `last_direction` MUST be `opening` (cover at 100% means it just finished opening)
3. Switch is at `idle` (after opening→idle)
4. Next in cycle: `idle` → `closing` ✓
5. Send 1 pulse: `idle` → `closing` and start
6. Update `direction` = `closing`, `last_direction` = `closing`
7. Start movement loop
8. Clear `_last_limit_stop_time` (we're starting new movement)

---

### Case 14: Cover is MOVING, reaches target position
**Conditions:**
- `direction` = `opening` or `closing`
- `position` reaches target position (not at limit 0% or 100%)

**Expected Behavior:**
1. Calculate final position from elapsed time
2. Send 1 pulse to stop (switch goes from current direction → `idle`)
   - If was `opening`: `opening` → `idle`
   - If was `closing`: `closing` → `idle`
3. Update `position` = target
4. Update `direction` = `idle`
5. Update `last_direction` = previous `direction` (before stop)
6. Cancel movement loop

**Note**: If target is at limit (0% or 100%), the cover will naturally stop (see Case 8 and Case 9), no pulse needed.

---

## Pulse Ignoring Logic

### When to Ignore Pulses

1. **Automatic Pulse Ignore (`_ignore_until`)**:
   - After sending an automatic pulse via `_trigger_pulse()`
   - Ignore window: `pulse_gap + 0.5` seconds
   - Purpose: Ignore our own automatic pulses, not user actions

2. **Limit Stop Ignore (`_last_limit_stop_time`)**:
   - After cover naturally reaches 0% or 100%
   - Ignore window: `LIMIT_STOP_IGNORE_DURATION` (2.0 seconds)
   - Purpose: Ignore any switch activation immediately after natural limit stop
   - **Note**: This should only apply when cover stops at limit naturally, not when user stops manually

---

## State Update Rules

### Cover Entity Updates
- **MUST** update `async_write_ha_state()` at every tick during movement (for real-time position display)
- **MUST** update when direction changes
- **MUST** update when movement stops

### Sub-Entities Updates
- **Position Override**: Update only when cover becomes `idle` (not during movement)
- **Direction**: Update when direction changes (idle ↔ opening ↔ closing)
- **Last Direction**: Update when `last_direction` changes
- **Travel Time**: Update only when user modifies it
- **Pulse Gap**: Update only when user modifies it

---

## Edge Cases to Handle

1. **Rapid successive commands**: Handle gracefully, cancel previous task if needed
2. **Position override during movement**: Stop movement, update position, notify
3. **Travel time change during movement**: Continue with new travel time (recalculate)
4. **Switch state desynchronization**: Always verify and correct using pulses if needed
5. **Multiple rapid switch activations**: Ignore within ignore windows, handle after

---

## Summary Table

| Current State | User Action | Pulses Needed | New Direction | Notes |
|--------------|-------------|---------------|---------------|-------|
| IDLE (last=open) | OPEN | 3 | opening | Switch at idle (after opening), next is closing. Need: idle→closing→idle→opening |
| IDLE (last=close) | OPEN | 1 | opening | Switch at idle (after closing), next is opening. Need: idle→opening |
| IDLE (last=open) | CLOSE | 1 | closing | Switch at idle (after opening), next is closing. Need: idle→closing |
| IDLE (last=close) | CLOSE | 3 | closing | Switch at idle (after closing), next is opening. Need: idle→opening→idle→closing |
| OPENING | OPEN (same) | 0 | opening | Continue, no pulse |
| OPENING | CLOSE | 1+1 | closing | Stop (1: opening→idle), then start closing (1: idle→closing) |
| CLOSING | CLOSE (same) | 0 | closing | Continue, no pulse |
| CLOSING | OPEN | 1+1 | opening | Stop (1: closing→idle), then start opening (1: idle→opening) |
| MOVING | STOP | 1 | idle | Stop pulse: current→idle |
| MOVING | Reaches 0% | 0 | idle | Natural stop, no pulse |
| MOVING | Reaches 100% | 0 | idle | Natural stop, no pulse |
| MOVING | Reaches target | 1 | idle | Stop pulse: current→idle |
