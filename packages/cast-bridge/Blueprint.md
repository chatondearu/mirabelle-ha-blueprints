# Project: HASS-Cast-Bridge (HACS Integration)

**Objective:** Create a HACS integration that acts as a virtual Chromecast Receiver. It must intercept `LOAD` commands from Android devices and forward the media URL to a selected Home Assistant `media_player` (specifically Music Assistant entities).

## Phase 1: Integration Scaffold & Configuration Flow

- **Task 1.1:** Create a standard HACS directory structure: `custom_components/cast_bridge/`.
- **Task 1.2:** Implement `manifest.json` with dependencies: `zeroconf`, `protobuf`, and `pycryptodome`.
- **Task 1.3:** Develop `config_flow.py` to allow users to:
- Name the Virtual Chromecast (e.g., "MA Kitchen Bridge").
- Select a target "Linked Media Player" from existing HA entities.

## Phase 2: mDNS Discovery (The "Beacon")

- **Task 2.1:** Use `zeroconf` to broadcast a `_googlecast._tcp.local` service.
- **Task 2.2:** Must include mandatory TXT records:
- `id`: Random UUID.
- `fn`: Friendly Name (from config).
- `md`: "Chromecast Ultra" (to ensure wide app compatibility).
- `st`: `0` (Idle state).
- `ca`: `4101` (Capabilities flag).

## Phase 3: CastV2 Protocol Server (Socket & TLS)

- **Task 3.1:** Create an `asyncio` TCP server listening on port **8009**.
- **Task 3.2:** Implement the TLS Handshake. *Note: Use a self-signed certificate but handle the case where the client (Android) might drop the connection due to lack of Google Root CA.*
- **Task 3.3:** Implement a Protobuf parser for `CastMessage` packets.
- Reference: `official_messaging.proto` from the Cast protocol.
- **Task 3.4:** Handle core namespaces:
- `urn:x-cast:com.google.cast.tp.heartbeat` (Respond to PING with PONG).
- `urn:x-cast:com.google.cast.tp.connection` (Handle CONNECT/CLOSE).
- `urn:x-cast:com.google.cast.receiver` (Report status: IDLE, BUSY).

## Phase 4: Interception & Media Redirection

- **Task 4.1:** Monitor the `urn:x-cast:com.google.cast.media` namespace.
- **Task 4.2:** On a `LOAD` command, extract:
- `media.contentId` (The stream URL).
- `media.contentType` (MIME type).
- `media.metadata` (Title, Artist, Album Art).
- **Task 4.3:** Trigger the Home Assistant Service:

```python
await self.hass.services.async_call(
    "media_player", "play_media", {
        "entity_id": target_entity,
        "media_content_id": contentId,
        "media_content_type": contentType
    }
)

```

## Phase 5: Feedback Loop (State Sync)

- **Task 5.1:** Listen to state changes of the target `media_player` in HA.
- **Task 5.2:** Translate HA states (Playing, Paused, Buffering) back into Cast `MEDIA_STATUS` messages to update the Android UI (Seek bar, Play/Pause button).

