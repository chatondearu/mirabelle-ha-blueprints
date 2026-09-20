/**
 * CDA Alarm sidebar panel (Lit, CDN).
 * Tabs: Dashboard | Sensors | General | Response | Cameras | Access | Linked
 */
import {
  LitElement,
  html,
  css,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js";

const WS_GET = "cda_alarm/get_config";
const WS_DASHBOARD = "cda_alarm/get_dashboard";
const WS_UPDATE = "cda_alarm/update_config";
const WS_LINKED = "cda_alarm/list_linked";
const MODES = ["away", "home", "night"];

const emptyResponse = () => ({
  sirens: [],
  siren_duration: 0,
  siren_tone: "",
  noise_media_players: [],
  alarm_sound_content_id: "",
  noise_volume: 0.9,
  enable_alarm_tts: false,
  alarm_tts_message: "Warning: the alarm has been triggered.",
  tts_media_players: [],
});

class CdaAlarmPanel extends LitElement {
  static properties = {
    hass: { attribute: false },
    narrow: { type: Boolean },
    _tab: { state: true },
    _dashboard: { state: true },
    _isAdmin: { state: true },
    _denied: { state: true },
    _arming: { state: true },
    _config: { state: true },
    _linked: { state: true },
    _loading: { state: true },
    _saving: { state: true },
    _error: { state: true },
    _message: { state: true },
    _newEntity: { state: true },
    _newMapSensor: { state: true },
    _newMapCamera: { state: true },
    _newUserId: { state: true },
    _users: { state: true },
    _codes: { state: true },
    _pinDialogOpen: { state: true },
    _pendingService: { state: true },
    _dialogPin: { state: true },
  };

  static styles = css`
    cda-alarm-panel {
      display: block;
      padding: 16px;
      max-width: 960px;
      margin: 0 auto;
      font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
      color: var(--primary-text-color);
    }
    cda-alarm-panel h1 {
      margin: 0 0 8px;
      font-size: 1.6rem;
    }
    cda-alarm-panel .subtitle {
      color: var(--secondary-text-color);
      margin-bottom: 16px;
    }
    cda-alarm-panel .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--divider-color);
      padding-bottom: 8px;
    }
    cda-alarm-panel .tabs button {
      background: transparent;
      border: 1px solid var(--divider-color);
      border-radius: 6px;
      padding: 8px 12px;
      cursor: pointer;
      color: var(--primary-text-color);
    }
    cda-alarm-panel .tabs button.active {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border-color: var(--primary-color);
    }
    cda-alarm-panel .card {
      background: var(--card-background-color, var(--ha-card-background, #fff));
      border-radius: 8px;
      padding: 16px;
      box-shadow: var(--ha-card-box-shadow, none);
      border: 1px solid var(--divider-color);
      margin-bottom: 16px;
    }
    cda-alarm-panel .row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }
    cda-alarm-panel .sensor-row {
      display: grid;
      grid-template-columns: minmax(180px, 1fr) repeat(3, auto) auto;
      gap: 8px;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    cda-alarm-panel label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.95rem;
    }
    cda-alarm-panel input[type="text"],
    cda-alarm-panel input[type="number"],
    cda-alarm-panel select,
    cda-alarm-panel textarea {
      width: 100%;
      box-sizing: border-box;
      padding: 8px;
      border-radius: 4px;
      border: 1px solid var(--divider-color);
      background: var(--input-fill-color, transparent);
      color: var(--primary-text-color);
    }
    cda-alarm-panel ha-device-picker,
    cda-alarm-panel ha-entity-picker,
    cda-alarm-panel ha-select,
    cda-alarm-panel ha-user-picker,
    cda-alarm-panel input[type="text"],
    cda-alarm-panel input[type="number"] {
      width: 100%;
      box-sizing: border-box;
    }
    cda-alarm-panel textarea {
      min-height: 140px;
      font-family: ui-monospace, monospace;
    }
    cda-alarm-panel .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 16px;
    }
    cda-alarm-panel button.primary,
    cda-alarm-panel button.secondary,
    cda-alarm-panel button.danger {
      border: none;
      border-radius: 6px;
      padding: 10px 14px;
      cursor: pointer;
    }
    cda-alarm-panel button.primary {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    cda-alarm-panel button.secondary {
      background: var(--secondary-background-color, #eee);
      color: var(--primary-text-color);
    }
    cda-alarm-panel button.danger {
      background: var(--error-color, #db4437);
      color: #fff;
    }
    cda-alarm-panel button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    cda-alarm-panel .banner {
      padding: 10px 12px;
      border-radius: 6px;
      margin-bottom: 12px;
    }
    cda-alarm-panel .banner.error {
      background: rgba(219, 68, 55, 0.15);
      color: var(--error-color, #db4437);
    }
    cda-alarm-panel .banner.ok {
      background: rgba(15, 157, 88, 0.15);
      color: var(--success-color, #0f9d58);
    }
    cda-alarm-panel .muted {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }
    cda-alarm-panel a {
      color: var(--primary-color);
    }
    cda-alarm-panel .keypad-card {
      border: 1px solid var(--divider-color);
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 10px;
    }
    cda-alarm-panel .picker-list {
      width: 100%;
    }
    cda-alarm-panel .picker-list-item,
    cda-alarm-panel .mapping-row,
    cda-alarm-panel .user-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    cda-alarm-panel .mapping-row ha-entity-picker {
      flex: 1 1 240px;
    }
    cda-alarm-panel ul.linked {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    cda-alarm-panel ul.linked li {
      padding: 10px 0;
      border-bottom: 1px solid var(--divider-color);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    cda-alarm-panel .alarm-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    cda-alarm-panel .state-badge {
      display: inline-block;
      padding: 5px 10px;
      border-radius: 999px;
      background: var(--secondary-background-color, #eee);
      font-weight: 600;
      text-transform: capitalize;
    }
    cda-alarm-panel .dashboard-grid,
    cda-alarm-panel .camera-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }
    cda-alarm-panel .area-card {
      margin-bottom: 0;
    }
    cda-alarm-panel .area-card ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    cda-alarm-panel .area-card li {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    cda-alarm-panel .sensor-open {
      color: var(--error-color, #db4437);
      font-weight: 600;
    }
    cda-alarm-panel .camera-tile {
      overflow: hidden;
      padding: 0;
    }
    cda-alarm-panel .camera-tile.highlighted {
      border: 3px solid var(--error-color, #db4437);
      box-shadow: 0 0 0 2px color-mix(in srgb, var(--error-color) 25%, transparent);
    }
    cda-alarm-panel .camera-tile img {
      display: block;
      width: 100%;
      aspect-ratio: 16 / 9;
      object-fit: cover;
      background: var(--secondary-background-color, #eee);
    }
    cda-alarm-panel .camera-caption {
      padding: 12px;
    }
    cda-alarm-panel .code-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 8px;
      align-items: end;
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--divider-color);
    }
    cda-alarm-panel .pin-dialog-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.45);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 16px;
    }
    cda-alarm-panel .pin-dialog {
      width: min(360px, 100%);
      margin: 0;
    }
    cda-alarm-panel .pin-dialog input {
      width: 100%;
      margin: 12px 0;
    }
  `;

  constructor() {
    super();
    this._tab = "dashboard";
    this._dashboard = null;
    this._isAdmin = false;
    this._denied = false;
    this._arming = false;
    this._config = null;
    this._linked = null;
    this._loading = false;
    this._saving = false;
    this._error = "";
    this._message = "";
    this._newEntity = "";
    this._newMapSensor = "";
    this._newMapCamera = "";
    this._newUserId = "";
    this._users = [];
    this._codes = [];
    this._pinDialogOpen = false;
    this._pendingService = null;
    this._dialogPin = "";
    this._dashboardReloadTimer = null;
    this._dashboardLoadPromise = null;
    this._dashboardReloadPending = false;
    this._nextDashboardRetryAt = 0;
  }

  createRenderRoot() {
    return this;
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this._dashboardReloadTimer !== null) {
      clearTimeout(this._dashboardReloadTimer);
      this._dashboardReloadTimer = null;
    }
  }

  updated(changed) {
    if (!changed.has("hass") || !this.hass) return;
    if (
      !this._dashboard &&
      !this._loading &&
      !this._denied &&
      Date.now() >= this._nextDashboardRetryAt
    ) {
      this._load();
      return;
    }
    if (
      this._dashboard &&
      this._dashboardStateChanged(changed.get("hass"))
    ) {
      this._scheduleDashboardReload();
    }
  }

  async _load() {
    if (!this.hass) return;
    this._loading = true;
    this._error = "";
    this._denied = false;
    try {
      await this._reloadDashboard({ loadConfig: true });
      if (!this._denied && this._tab === "linked") {
        await this._loadLinked();
      }
    } catch (err) {
      this._handleDashboardError(err);
    } finally {
      this._loading = false;
    }
  }

  _dashboardEntityIds() {
    if (!this._dashboard) return [];
    return [
      this._dashboard.panel_entity_id,
      ...(this._dashboard.areas || []).flatMap((area) =>
        (area.sensors || []).map((sensor) => sensor.entity_id)
      ),
      ...(this._dashboard.cameras || []).map((camera) => camera.entity_id),
    ].filter(Boolean);
  }

  _dashboardStateChanged(previousHass) {
    return this._dashboardEntityIds().some(
      (entityId) =>
        previousHass?.states?.[entityId] !== this.hass?.states?.[entityId]
    );
  }

  _scheduleDashboardReload() {
    if (this._dashboardReloadTimer !== null) {
      clearTimeout(this._dashboardReloadTimer);
    }
    this._dashboardReloadTimer = setTimeout(() => {
      this._dashboardReloadTimer = null;
      this._reloadDashboard();
    }, 250);
  }

  _handleDashboardError(err) {
    if (err?.code !== "unauthorized" && !/access denied/i.test(err?.message)) {
      this._error = err?.message || String(err);
      this._nextDashboardRetryAt = Date.now() + 5000;
      return false;
    }
    this._denied = true;
    this._dashboard = null;
    this._isAdmin = false;
    this._config = null;
    this._linked = null;
    this._tab = "dashboard";
    this._error = "";
    this._dashboardReloadPending = false;
    if (this._dashboardReloadTimer !== null) {
      clearTimeout(this._dashboardReloadTimer);
      this._dashboardReloadTimer = null;
    }
    return true;
  }

  async _applyDashboard(dashboard, loadConfig) {
    const wasAdmin = this._isAdmin;
    this._dashboard = dashboard;
    this._denied = false;
    this._nextDashboardRetryAt = 0;
    this._isAdmin = Boolean(dashboard.can_configure);
    if (!this._isAdmin) {
      this._config = null;
      this._linked = null;
      this._tab = "dashboard";
      return;
    }
    const configIsMissing =
      !this._config || this._config.entry_id !== dashboard.entry_id;
    if (loadConfig || !wasAdmin || configIsMissing) {
      const config = await this.hass.connection.sendMessagePromise({
        type: WS_GET,
        entry_id: dashboard.entry_id,
      });
      this._config = this._normalizeConfig(config);
      this._codes = this._normalizeCodes(this._config.codes);
    }
  }

  _normalizeCodes(codes) {
    return (Array.isArray(codes) ? codes : []).map((entry) => ({
      name: entry?.name || "",
      pin: entry?.pin || "",
      rfid: entry?.rfid || "",
      nfc_tag_id: entry?.nfc_tag_id || "",
    }));
  }

  _addCodeRow() {
    this._codes = [
      ...this._codes,
      { name: "", pin: "", rfid: "", nfc_tag_id: "" },
    ];
  }

  _updateCodeRow(index, patch) {
    this._codes = this._codes.map((row, i) =>
      i === index ? { ...row, ...patch } : row
    );
  }

  _removeCodeRow(index) {
    this._codes = this._codes.filter((_, i) => i !== index);
  }

  _codesForSave() {
    return this._codes
      .map((row) => {
        const out = {};
        if (row.name) out.name = String(row.name);
        if (row.pin) out.pin = String(row.pin);
        if (row.rfid) out.rfid = String(row.rfid);
        if (row.nfc_tag_id) out.nfc_tag_id = String(row.nfc_tag_id);
        return out;
      })
      .filter((row) => row.pin || row.rfid || row.nfc_tag_id);
  }

  async _reloadDashboard({ loadConfig = false } = {}) {
    if (!this.hass) return;
    if (this._dashboardLoadPromise) {
      this._dashboardReloadPending = true;
      return this._dashboardLoadPromise;
    }
    this._dashboardLoadPromise = (async () => {
      this._error = "";
      try {
        const dashboard = await this.hass.connection.sendMessagePromise({
          type: WS_DASHBOARD,
          entry_id: this._dashboard?.entry_id,
        });
        await this._applyDashboard(dashboard, loadConfig);
      } catch (err) {
        this._handleDashboardError(err);
      } finally {
        this._dashboardLoadPromise = null;
        if (this._dashboardReloadPending && !this._denied) {
          this._dashboardReloadPending = false;
          this._scheduleDashboardReload();
        }
      }
    })();
    return this._dashboardLoadPromise;
  }

  _normalizeConfig(config) {
    return {
      ...config,
      sensor_assignments: Array.isArray(config.sensor_assignments)
        ? config.sensor_assignments.map((item) => ({
            entity_id: item.entity_id,
            modes: [...(item.modes || [])],
          }))
        : [],
      keypads: Array.isArray(config.keypads)
        ? config.keypads.map((item) => ({ ...item }))
        : [],
      response: { ...emptyResponse(), ...(config.response || {}) },
      codes: Array.isArray(config.codes) ? config.codes : [],
      cameras: Array.isArray(config.cameras) ? [...config.cameras] : [],
      sensor_camera_map:
        config.sensor_camera_map &&
        typeof config.sensor_camera_map === "object"
          ? { ...config.sensor_camera_map }
          : {},
      access: {
        mode: config.access?.mode || "admin",
        user_ids: Array.isArray(config.access?.user_ids)
          ? [...config.access.user_ids]
          : [],
        state_notifications: config.access?.state_notifications !== false,
      },
    };
  }

  async _loadLinked() {
    if (!this.hass) return;
    try {
      this._linked = await this.hass.connection.sendMessagePromise({
        type: WS_LINKED,
        entry_id: this._config?.entry_id,
      });
    } catch (err) {
      this._error = err?.message || String(err);
    }
  }

  async _setTab(tab) {
    if (tab !== "dashboard" && !this._isAdmin) return;
    this._tab = tab;
    this._message = "";
    if (tab === "linked") {
      await this._loadLinked();
    } else if (tab === "access") {
      await this._loadUsers();
    }
  }

  async _loadUsers() {
    const users = new Map();
    const addUsers = (items) => {
      for (const user of items || []) {
        if (user?.id) {
          users.set(user.id, { id: user.id, name: user.name || user.id });
        }
      }
    };
    addUsers(Object.values(this.hass?.users || {}));
    addUsers(this.hass?.user ? [this.hass.user] : []);
    try {
      const result = await this.hass.connection.sendMessagePromise({
        type: "config/auth/list",
      });
      addUsers(Array.isArray(result) ? result : result?.users);
    } catch {
      // Some Home Assistant roles do not expose the full user list.
    }
    this._users = [...users.values()].sort((a, b) =>
      a.name.localeCompare(b.name)
    );
  }

  async _requestAlarm(service) {
    if (!this.hass || !this._dashboard?.panel_entity_id) return;
    if (this._dashboard?.code_required) {
      this._pendingService = service;
      this._dialogPin = "";
      this._pinDialogOpen = true;
      this._error = "";
      return;
    }
    await this._controlAlarm(service);
  }

  async _confirmPinDialog() {
    const service = this._pendingService;
    const pin = this._dialogPin;
    this._pinDialogOpen = false;
    this._pendingService = null;
    this._dialogPin = "";
    if (!service) return;
    await this._controlAlarm(service, pin);
  }

  _cancelPinDialog() {
    this._pinDialogOpen = false;
    this._pendingService = null;
    this._dialogPin = "";
  }

  async _controlAlarm(service, pin) {
    if (!this.hass || !this._dashboard?.panel_entity_id) return;
    this._arming = true;
    this._error = "";
    try {
      const data = {
        entity_id: this._dashboard.panel_entity_id,
      };
      if (pin) {
        data.code = pin;
      }
      await this.hass.callService("alarm_control_panel", service, data);
      await this._reloadDashboard();
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._arming = false;
    }
  }

  _entityLabel(entityId) {
    const state = this.hass?.states?.[entityId];
    const name = state?.attributes?.friendly_name;
    return name ? `${name} (${entityId})` : entityId;
  }

  _addSensor() {
    const entityId = (this._newEntity || "").trim();
    if (!entityId || !this._config) return;
    const existing = this._config.sensor_assignments.find(
      (item) => item.entity_id === entityId
    );
    if (existing) {
      this._error = "Sensor already listed.";
      return;
    }
    this._config = {
      ...this._config,
      sensor_assignments: [
        ...this._config.sensor_assignments,
        { entity_id: entityId, modes: [...MODES] },
      ],
    };
    this._newEntity = "";
    this._error = "";
  }

  _removeSensor(entityId) {
    const sensorCameraMap = { ...this._config.sensor_camera_map };
    delete sensorCameraMap[entityId];
    this._config = {
      ...this._config,
      sensor_assignments: this._config.sensor_assignments.filter(
        (item) => item.entity_id !== entityId
      ),
      sensor_camera_map: sensorCameraMap,
    };
  }

  _toggleMode(entityId, mode, checked) {
    this._config = {
      ...this._config,
      sensor_assignments: this._config.sensor_assignments.map((item) => {
        if (item.entity_id !== entityId) return item;
        const modes = new Set(item.modes || []);
        if (checked) modes.add(mode);
        else modes.delete(mode);
        return {
          entity_id: entityId,
          modes: MODES.filter((m) => modes.has(m)),
        };
      }),
    };
  }

  _setField(path, value) {
    const next = { ...this._config };
    if (path.startsWith("response.")) {
      next.response = { ...next.response, [path.slice(9)]: value };
    } else {
      next[path] = value;
    }
    this._config = next;
  }

  /** Read a text/number field value from a native or HA form event. */
  _eventValue(event) {
    const target = event?.target;
    if (target && target.value !== undefined && target.value !== null) {
      return target.value;
    }
    const path = typeof event?.composedPath === "function" ? event.composedPath() : [];
    for (const node of path) {
      if (node && node.value !== undefined && node.value !== null) {
        return node.value;
      }
    }
    return "";
  }

  /** Update a numeric option; keep empty string while the user clears the field. */
  _setNumberField(path, raw) {
    if (raw === "") {
      this._setField(path, "");
      return;
    }
    const number = Number(raw);
    if (Number.isFinite(number)) {
      this._setField(path, number);
    }
  }

  _numberDisplay(value, fallback) {
    if (value === "" || value === null || value === undefined) {
      return value === "" ? "" : String(fallback);
    }
    return String(value);
  }

  _addEntityToField(path, entityId) {
    if (!entityId) return;
    const current = path.startsWith("response.")
      ? this._config.response[path.slice(9)]
      : this._config[path];
    if ((current || []).includes(entityId)) return;
    this._setField(path, [...(current || []), entityId]);
  }

  _removeEntityFromField(path, entityId) {
    const current = path.startsWith("response.")
      ? this._config.response[path.slice(9)]
      : this._config[path];
    this._setField(
      path,
      (current || []).filter((item) => item !== entityId)
    );
    if (path === "cameras") {
      const sensorCameraMap = Object.fromEntries(
        Object.entries(this._config.sensor_camera_map).filter(
          ([, camera]) => camera !== entityId
        )
      );
      this._setField("sensor_camera_map", sensorCameraMap);
    }
  }

  _setSensorCamera(sensorId, cameraId) {
    if (!sensorId || !cameraId) return;
    this._setField("sensor_camera_map", {
      ...this._config.sensor_camera_map,
      [sensorId]: cameraId,
    });
  }

  _removeSensorCamera(sensorId) {
    const sensorCameraMap = { ...this._config.sensor_camera_map };
    delete sensorCameraMap[sensorId];
    this._setField("sensor_camera_map", sensorCameraMap);
  }

  _setAccess(patch) {
    this._setField("access", { ...this._config.access, ...patch });
  }

  _addAccessUser(userId) {
    if (!userId || this._config.access.user_ids.includes(userId)) return;
    this._setAccess({
      user_ids: [...this._config.access.user_ids, userId],
    });
    this._newUserId = "";
  }

  _removeAccessUser(userId) {
    this._setAccess({
      user_ids: this._config.access.user_ids.filter((id) => id !== userId),
    });
  }

  _addKeypad(deviceId) {
    if (!deviceId || !this._config) return;
    if (this._config.keypads.some((item) => item.device_id === deviceId)) {
      return;
    }
    const isFirst = this._config.keypads.length === 0;
    this._config = {
      ...this._config,
      keypads: [
        ...this._config.keypads,
        {
          device_id: deviceId,
          is_default: isFirst,
          feedback: false,
          sync_zha_panel: false,
          endpoint: 44,
        },
      ],
    };
  }

  _updateKeypad(deviceId, patch) {
    let keypads = this._config.keypads.map((item) =>
      item.device_id === deviceId ? { ...item, ...patch } : item
    );
    if (patch.is_default) {
      keypads = keypads.map((item) => ({
        ...item,
        is_default: item.device_id === deviceId,
      }));
    }
    this._config = { ...this._config, keypads };
  }

  _removeKeypad(deviceId) {
    let keypads = this._config.keypads.filter(
      (item) => item.device_id !== deviceId
    );
    if (keypads.length && !keypads.some((item) => item.is_default)) {
      keypads = keypads.map((item, index) => ({
        ...item,
        is_default: index === 0,
      }));
    }
    this._config = { ...this._config, keypads };
  }

  async _save() {
    if (!this.hass || !this._config) return;
    this._saving = true;
    this._error = "";
    this._message = "";
    try {
      const codes = this._codesForSave();
      const payload = {
        sensor_assignments: this._config.sensor_assignments.filter(
          (item) => (item.modes || []).length
        ),
        entry_delay: Number(this._config.entry_delay) || 0,
        exit_delay: Number(this._config.exit_delay) || 0,
        block_arm_if_open: Boolean(this._config.block_arm_if_open),
        codes,
        keypads: this._config.keypads,
        response: this._config.response,
        cameras: this._config.cameras,
        sensor_camera_map: this._config.sensor_camera_map,
        access: this._config.access,
      };
      const updated = await this.hass.connection.sendMessagePromise({
        type: WS_UPDATE,
        entry_id: this._config.entry_id,
        config: payload,
      });
      this._config = this._normalizeConfig(updated);
      this._codes = this._normalizeCodes(this._config.codes);
      this._message = "Saved.";
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._saving = false;
    }
  }

  render() {
    const styles = html`<style>${CdaAlarmPanel.styles.cssText}</style>`;
    if (this._loading && !this._dashboard) {
      return html`${styles}<div class="card">Loading CDA Alarm…</div>`;
    }
    if (this._denied) {
      return html`
        ${styles}
        <div class="card">
          <h1>Access denied</h1>
          <p>You do not have permission to view the CDA Alarm dashboard.</p>
        </div>
      `;
    }
    if (!this._dashboard) {
      return html`
        ${styles}
        <div class="card">
          <p>No CDA Alarm dashboard is available.</p>
          ${this._error
            ? html`<div class="banner error">${this._error}</div>`
            : nothing}
        </div>
      `;
    }

    return html`
      ${styles}
      <h1>CDA Alarm</h1>
      <p class="subtitle">
        Monitor and control your security system.
      </p>
      ${this._error
        ? html`<div class="banner error">${this._error}</div>`
        : nothing}
      ${this._message
        ? html`<div class="banner ok">${this._message}</div>`
        : nothing}
      <div class="tabs">
        ${[
          "dashboard",
          ...(this._isAdmin
            ? [
                "sensors",
                "general",
                "response",
                "cameras",
                "access",
                "linked",
              ]
            : []),
        ].map(
          (tab) => html`
            <button
              class=${this._tab === tab ? "active" : ""}
              @click=${() => this._setTab(tab)}
            >
              ${tab[0].toUpperCase()}${tab.slice(1)}
            </button>
          `
        )}
      </div>
      ${this._tab === "dashboard" ? this._renderDashboard() : nothing}
      ${this._tab === "sensors" ? this._renderSensors() : nothing}
      ${this._tab === "general" ? this._renderGeneral() : nothing}
      ${this._tab === "response" ? this._renderResponse() : nothing}
      ${this._tab === "cameras" ? this._renderCameras() : nothing}
      ${this._tab === "access" ? this._renderAccess() : nothing}
      ${this._tab === "linked" ? this._renderLinked() : nothing}
      ${this._isAdmin &&
      this._config &&
      !["dashboard", "linked"].includes(this._tab)
        ? html`
            <div class="actions">
              <button
                class="primary"
                ?disabled=${this._saving}
                @click=${this._save}
              >
                ${this._saving ? "Saving…" : "Save"}
              </button>
              <button
                class="secondary"
                ?disabled=${this._saving}
                @click=${this._load}
              >
                Reload
              </button>
            </div>
          `
        : nothing}
      ${this._pinDialogOpen ? this._renderPinDialog() : nothing}
    `;
  }

  _renderPinDialog() {
    return html`
      <div class="pin-dialog-backdrop" @click=${this._cancelPinDialog}>
        <div class="pin-dialog card" @click=${(e) => e.stopPropagation()}>
          <h3>Enter PIN</h3>
          <input
            type="password"
            inputmode="numeric"
            autocomplete="off"
            aria-label="PIN"
            .value=${this._dialogPin}
            @input=${(e) => {
              this._dialogPin = this._eventValue(e);
            }}
            @keydown=${(e) => {
              if (e.key === "Enter") this._confirmPinDialog();
            }}
          />
          <div class="actions">
            <button class="primary" @click=${this._confirmPinDialog}>OK</button>
            <button class="secondary" @click=${this._cancelPinDialog}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    `;
  }

  _renderDashboard() {
    const dashboard = this._dashboard;
    const stateLabel = String(dashboard.state || "unavailable").replaceAll(
      "_",
      " "
    );
    return html`
      <div class="card">
        <div class="alarm-header">
          <div>
            <h2>Alarm</h2>
            <span class="state-badge">${stateLabel}</span>
          </div>
        </div>
        <div class="actions">
          <button
            class="primary"
            ?disabled=${this._arming}
            @click=${() => this._requestAlarm("alarm_arm_away")}
          >
            Arm away
          </button>
          <button
            class="secondary"
            ?disabled=${this._arming}
            @click=${() => this._requestAlarm("alarm_arm_home")}
          >
            Arm home
          </button>
          <button
            class="secondary"
            ?disabled=${this._arming}
            @click=${() => this._requestAlarm("alarm_arm_night")}
          >
            Arm night
          </button>
          <button
            class="danger"
            ?disabled=${this._arming}
            @click=${() => this._requestAlarm("alarm_disarm")}
          >
            Disarm
          </button>
          <button
            class="secondary"
            ?disabled=${this._arming}
            @click=${this._reloadDashboard}
          >
            Refresh
          </button>
        </div>
      </div>

      <h2>Areas</h2>
      ${(dashboard.areas || []).length
        ? html`
            <div class="dashboard-grid">
              ${dashboard.areas.map(
                (area) => html`
                  <section class="card area-card">
                    <h3>${area.name}</h3>
                    <ul>
                      ${(area.sensors || []).map(
                        (sensor) => html`
                          <li>
                            <span>${sensor.name}</span>
                            <span class=${sensor.open ? "sensor-open" : ""}>
                              ${sensor.state}
                            </span>
                          </li>
                        `
                      )}
                    </ul>
                  </section>
                `
              )}
            </div>
          `
        : html`<p class="muted">No alarm sensors are configured.</p>`}

      <h2>Cameras</h2>
      ${(dashboard.cameras || []).length
        ? html`
            <div class="camera-grid">
              ${dashboard.cameras.map((camera) => {
                const accessToken =
                  this.hass?.states?.[camera.entity_id]?.attributes?.access_token;
                return html`
                  <article
                    class="card camera-tile ${camera.entity_id ===
                    dashboard.highlighted_camera
                      ? "highlighted"
                      : ""}"
                  >
                    ${accessToken
                      ? html`
                          <img
                            src=${`/api/camera_proxy/${camera.entity_id}?token=${encodeURIComponent(
                              accessToken
                            )}`}
                            alt=${camera.name}
                            loading="lazy"
                          />
                        `
                      : nothing}
                    <div class="camera-caption">
                      <strong>${camera.name}</strong>
                      <div class="muted">${camera.state}</div>
                    </div>
                  </article>
                `;
              })}
            </div>
          `
        : html`<p class="muted">No cameras are configured.</p>`}
    `;
  }

  _renderSensors() {
    return html`
      <div class="card">
        <p class="muted">
          Add entities once, then choose Away / Home / Night for each.
        </p>
        <div class="row">
          <ha-entity-picker
            .hass=${this.hass}
            .value=${this._newEntity}
            label="Sensor entity"
            @value-changed=${(e) => {
              this._newEntity = e.detail?.value ?? e.target.value;
            }}
          ></ha-entity-picker>
          <button class="secondary" @click=${this._addSensor}>Add</button>
        </div>
        ${this._config.sensor_assignments.map(
          (item) => html`
            <div class="sensor-row">
              <div>${this._entityLabel(item.entity_id)}</div>
              ${MODES.map(
                (mode) => html`
                  <label>
                    <input
                      type="checkbox"
                      .checked=${(item.modes || []).includes(mode)}
                      @change=${(e) =>
                        this._toggleMode(
                          item.entity_id,
                          mode,
                          e.target.checked
                        )}
                    />
                    ${mode}
                  </label>
                `
              )}
              <button
                class="danger"
                @click=${() => this._removeSensor(item.entity_id)}
              >
                Remove
              </button>
            </div>
          `
        )}
      </div>
    `;
  }

  _renderGeneral() {
    const devices = this._config.zha_devices || [];
    const unused = devices.filter(
      (device) =>
        !this._config.keypads.some((item) => item.device_id === device.id)
    );
    return html`
      <div class="card">
        <h3>Delays & arming</h3>
        <div class="row">
          <label
            >Entry delay (s)
            <input
              type="number"
              min="0"
              step="1"
              aria-label="Entry delay (s)"
              .value=${this._numberDisplay(this._config.entry_delay, 30)}
              @input=${(e) =>
                this._setNumberField("entry_delay", this._eventValue(e))}
            />
          </label>
          <label
            >Exit delay (s)
            <input
              type="number"
              min="0"
              step="1"
              aria-label="Exit delay (s)"
              .value=${this._numberDisplay(this._config.exit_delay, 60)}
              @input=${(e) =>
                this._setNumberField("exit_delay", this._eventValue(e))}
            />
          </label>
          <label>
            <ha-switch
              .checked=${Boolean(this._config.block_arm_if_open)}
              @change=${(e) =>
                this._setField("block_arm_if_open", e.target.checked)}
            ></ha-switch>
            Block arm if a sensor is open
          </label>
        </div>
      </div>

      <div class="card">
        <h3>Keypads</h3>
        <p class="muted">
          Mark one keypad as default. If none are selected, the integration uses
          the first discovered Frient KEPZB-110
          ${this._config.discovered_default_keypad
            ? html` (currently
              <code>${this._config.discovered_default_keypad}</code>)`
            : nothing}.
        </p>
        <div class="row">
          <select
            id="add-keypad"
            @change=${(e) => {
              this._addKeypad(e.target.value);
              e.target.value = "";
            }}
          >
            <option value="">Add ZHA device…</option>
            ${unused.map(
              (device) => html`
                <option value=${device.id}>
                  ${device.name}${device.model ? ` (${device.model})` : ""}
                </option>
              `
            )}
          </select>
        </div>
        ${this._config.keypads.map(
          (item) => html`
            <div class="keypad-card">
              <strong>${this._deviceName(item.device_id)}</strong>
              <div class="row">
                <label>
                  <ha-switch
                    .checked=${Boolean(item.is_default)}
                    @change=${(e) =>
                      this._updateKeypad(item.device_id, {
                        is_default: e.target.checked,
                      })}
                  ></ha-switch>
                  Default
                </label>
                <label>
                  <ha-switch
                    .checked=${Boolean(item.feedback)}
                    @change=${(e) =>
                      this._updateKeypad(item.device_id, {
                        feedback: e.target.checked,
                      })}
                  ></ha-switch>
                  Feedback
                </label>
                <label>
                  <ha-switch
                    .checked=${Boolean(item.sync_zha_panel)}
                    @change=${(e) =>
                      this._updateKeypad(item.device_id, {
                        sync_zha_panel: e.target.checked,
                      })}
                  ></ha-switch>
                  Sync ZHA panel
                </label>
                <label
                  >Endpoint
                  <input
                    type="number"
                    min="1"
                    max="255"
                    step="1"
                    aria-label="Endpoint"
                    .value=${this._numberDisplay(item.endpoint, 44)}
                    @input=${(e) => {
                      const raw = this._eventValue(e);
                      if (raw === "") return;
                      const endpoint = Number(raw);
                      if (Number.isFinite(endpoint)) {
                        this._updateKeypad(item.device_id, { endpoint });
                      }
                    }}
                  />
                </label>
                <button
                  class="danger"
                  @click=${() => this._removeKeypad(item.device_id)}
                >
                  Remove
                </button>
              </div>
            </div>
          `
        )}
      </div>

      <div class="card">
        <h3>Codes</h3>
        <p class="muted">
          Add PIN, RFID, and NFC tag credentials. Empty rows are ignored on save.
          Optional fields: <code>name</code>, <code>pin</code>, <code>rfid</code>,
          <code>nfc_tag_id</code>.
        </p>
        ${this._codes.map(
          (row, index) => html`
            <div class="code-row">
              <label
                >Name
                <input
                  type="text"
                  aria-label="Code name"
                  .value=${row.name}
                  @input=${(e) =>
                    this._updateCodeRow(index, {
                      name: this._eventValue(e),
                    })}
                />
              </label>
              <label
                >PIN
                <input
                  type="text"
                  inputmode="numeric"
                  autocomplete="off"
                  aria-label="PIN"
                  .value=${row.pin}
                  @input=${(e) =>
                    this._updateCodeRow(index, { pin: this._eventValue(e) })}
                />
              </label>
              <label
                >RFID
                <input
                  type="text"
                  aria-label="RFID"
                  .value=${row.rfid}
                  @input=${(e) =>
                    this._updateCodeRow(index, { rfid: this._eventValue(e) })}
                />
              </label>
              <label
                >NFC tag id
                <input
                  type="text"
                  aria-label="NFC tag id"
                  .value=${row.nfc_tag_id}
                  @input=${(e) =>
                    this._updateCodeRow(index, {
                      nfc_tag_id: this._eventValue(e),
                    })}
                />
              </label>
              <button class="danger" @click=${() => this._removeCodeRow(index)}>
                Remove
              </button>
            </div>
          `
        )}
        <div class="actions">
          <button class="secondary" @click=${this._addCodeRow}>Add code</button>
        </div>
      </div>
    `;
  }

  _deviceName(deviceId) {
    const device = (this._config.zha_devices || []).find(
      (item) => item.id === deviceId
    );
    return device?.name || deviceId;
  }

  _renderResponse() {
    const response = this._config.response || emptyResponse();
    return html`
      <div class="card">
        <h3>Sirens</h3>
        ${this._renderEntityListPicker(
          "Siren entities",
          "response.sirens",
          response.sirens,
          ["siren"]
        )}
        <div class="row">
          <label
            >Duration (s, 0 = default)
            <input
              type="number"
              min="0"
              step="1"
              aria-label="Siren duration (s)"
              .value=${this._numberDisplay(response.siren_duration, 0)}
              @input=${(e) =>
                this._setNumberField(
                  "response.siren_duration",
                  this._eventValue(e)
                )}
            />
          </label>
          <label
            >Tone
            <input
              type="text"
              aria-label="Siren tone"
              .value=${response.siren_tone || ""}
              @input=${(e) =>
                this._setField("response.siren_tone", this._eventValue(e))}
            />
          </label>
        </div>
      </div>

      <div class="card">
        <h3>Noise media</h3>
        ${this._renderEntityListPicker(
          "Media players",
          "response.noise_media_players",
          response.noise_media_players,
          ["media_player"]
        )}
        <label
          >Sound content id
          <input
            type="text"
            aria-label="Sound content ID"
            .value=${response.alarm_sound_content_id || ""}
            @input=${(e) =>
              this._setField(
                "response.alarm_sound_content_id",
                this._eventValue(e)
              )}
          />
        </label>
        <label
          >Volume (0–1)
          <input
            type="number"
            min="0"
            max="1"
            step="0.05"
            aria-label="Noise volume"
            .value=${this._numberDisplay(response.noise_volume, 0.9)}
            @input=${(e) =>
              this._setNumberField(
                "response.noise_volume",
                this._eventValue(e)
              )}
          />
        </label>
      </div>

      <div class="card">
        <h3>TTS</h3>
        <label>
          <ha-switch
            .checked=${Boolean(response.enable_alarm_tts)}
            @change=${(e) =>
              this._setField("response.enable_alarm_tts", e.target.checked)}
          ></ha-switch>
          Enable alarm TTS
        </label>
        <label
          >Message
          <input
            type="text"
            aria-label="TTS message"
            .value=${response.alarm_tts_message || ""}
            @input=${(e) =>
              this._setField(
                "response.alarm_tts_message",
                this._eventValue(e)
              )}
          />
        </label>
        ${this._renderEntityListPicker(
          "TTS media players",
          "response.tts_media_players",
          response.tts_media_players,
          ["media_player"]
        )}
        <p class="muted">
          Response starts when the panel enters <code>triggered</code> and stops
          on disarm / leave-triggered. Clear sirens/noise on
          <strong>[CDA] Alarm Response</strong> to avoid double sound.
        </p>
      </div>
    `;
  }

  _renderEntityListPicker(label, path, values = [], domains = []) {
    return html`
      <div class="picker-list">
        <ha-entity-picker
          .hass=${this.hass}
          .value=${""}
          .includeDomains=${domains}
          .excludeEntities=${values}
          .label=${label}
          @value-changed=${(e) =>
            this._addEntityToField(
              path,
              e.detail?.value ?? e.target.value
            )}
        ></ha-entity-picker>
        ${values.map(
          (entityId) => html`
            <div class="picker-list-item">
              <span>${this._entityLabel(entityId)}</span>
              <button
                class="danger"
                @click=${() => this._removeEntityFromField(path, entityId)}
              >
                Remove
              </button>
            </div>
          `
        )}
      </div>
    `;
  }

  _renderCameras() {
    const sensorIds = this._config.sensor_assignments.map(
      (item) => item.entity_id
    );
    const mappedSensors = Object.keys(this._config.sensor_camera_map);
    return html`
      <div class="card">
        <h3>Cameras</h3>
        <p class="muted">
          Add cameras shown on the dashboard, then optionally map alarm sensors
          to the camera that should be highlighted.
        </p>
        ${this._renderEntityListPicker(
          "Add camera",
          "cameras",
          this._config.cameras,
          ["camera"]
        )}
      </div>
      <div class="card">
        <h3>Sensor camera mapping</h3>
        ${mappedSensors.map(
          (sensorId) => html`
            <div class="mapping-row">
              <ha-entity-picker
                .hass=${this.hass}
                .value=${sensorId}
                .includeEntities=${sensorIds}
                label="Sensor"
                disabled
              ></ha-entity-picker>
              <ha-entity-picker
                .hass=${this.hass}
                .value=${this._config.sensor_camera_map[sensorId]}
                .includeDomains=${["camera"]}
                .includeEntities=${this._config.cameras}
                label="Camera"
                @value-changed=${(e) =>
                  this._setSensorCamera(
                    sensorId,
                    e.detail?.value ?? e.target.value
                  )}
              ></ha-entity-picker>
              <button
                class="danger"
                @click=${() => this._removeSensorCamera(sensorId)}
              >
                Remove
              </button>
            </div>
          `
        )}
        <div class="mapping-row">
          <ha-entity-picker
            .hass=${this.hass}
            .value=${this._newMapSensor}
            .includeEntities=${sensorIds}
            .excludeEntities=${mappedSensors}
            label="Sensor"
            @value-changed=${(e) => {
              this._newMapSensor = e.detail?.value ?? e.target.value;
            }}
          ></ha-entity-picker>
          <ha-entity-picker
            .hass=${this.hass}
            .value=${this._newMapCamera}
            .includeDomains=${["camera"]}
            .includeEntities=${this._config.cameras}
            label="Camera"
            @value-changed=${(e) => {
              this._newMapCamera = e.detail?.value ?? e.target.value;
            }}
          ></ha-entity-picker>
          <button
            class="secondary"
            ?disabled=${!this._newMapSensor || !this._newMapCamera}
            @click=${() => {
              this._setSensorCamera(
                this._newMapSensor,
                this._newMapCamera
              );
              this._newMapSensor = "";
              this._newMapCamera = "";
            }}
          >
            Add
          </button>
        </div>
      </div>
    `;
  }

  _renderAccess() {
    const access = this._config.access;
    const selectedUsers = new Set(access.user_ids);
    const availableUsers = this._users.filter(
      (user) => !selectedUsers.has(user.id)
    );
    return html`
      <div class="card">
        <h3>Dashboard access</h3>
        <ha-select
          label="Access mode"
          .value=${access.mode}
          @closed=${(e) => e.stopPropagation()}
          @selected=${(e) =>
            this._setAccess({
              mode: e.target.value,
            })}
        >
          <ha-list-item value="admin">Administrators only</ha-list-item>
          <ha-list-item value="everyone">Everyone</ha-list-item>
          <ha-list-item value="users">Selected users</ha-list-item>
        </ha-select>
        ${access.mode === "users"
          ? html`
              <div class="row">
                ${customElements.get("ha-user-picker")
                  ? html`
                      <ha-user-picker
                        .hass=${this.hass}
                        .users=${availableUsers}
                        .value=${this._newUserId}
                        label="Add user"
                        @value-changed=${(e) =>
                          this._addAccessUser(
                            e.detail?.value ?? e.target.value
                          )}
                      ></ha-user-picker>
                    `
                  : html`
                      <select
                        .value=${this._newUserId}
                        @change=${(e) =>
                          this._addAccessUser(e.target.value)}
                      >
                        <option value="">Add user…</option>
                        ${availableUsers.map(
                          (user) => html`
                            <option value=${user.id}>${user.name}</option>
                          `
                        )}
                      </select>
                    `}
              </div>
              ${access.user_ids.map((userId) => {
                const user = this._users.find((item) => item.id === userId);
                return html`
                  <div class="user-row">
                    <span>${user?.name || userId}</span>
                    <button
                      class="danger"
                      @click=${() => this._removeAccessUser(userId)}
                    >
                      Remove
                    </button>
                  </div>
                `;
              })}
              ${!this._users.length
                ? html`
                    <p class="muted">
                      The Home Assistant user list is unavailable. Existing
                      assignments can still be removed.
                    </p>
                  `
                : nothing}
            `
          : nothing}
        <label>
          <ha-switch
            .checked=${access.state_notifications !== false}
            @change=${(e) =>
              this._setAccess({
                state_notifications: e.target.checked,
              })}
          ></ha-switch>
          State notifications
        </label>
        <p class="muted">
          Send Companion notifications to phones of users who can open this
          dashboard on arm, disarm, and triggered (not arming/pending).
        </p>
      </div>
    `;
  }

  _renderLinked() {
    const linked = this._linked;
    if (!linked) {
      return html`<div class="card">Loading linked automations…</div>`;
    }
    return html`
      <div class="card">
        <p class="muted">
          Automations that reference
          <code>${linked.panel_entity_id}</code> or known CDA blueprints.
        </p>
        ${(linked.notes || []).map(
          (note) => html`<p class="muted">${note}</p>`
        )}
        ${!(linked.automations || []).length
          ? html`<p>No linked automations found.</p>`
          : html`
              <ul class="linked">
                ${linked.automations.map(
                  (item) => html`
                    <li>
                      <div>
                        <strong>${item.name}</strong>
                        <div class="muted">${item.entity_id} · ${item.state}</div>
                      </div>
                      <a
                        href=${item.automation_id
                          ? `/config/automation/edit/${encodeURIComponent(
                              item.automation_id
                            )}`
                          : "/config/automation/dashboard"}
                        target="_blank"
                        rel="noopener"
                      >
                        Open editor
                      </a>
                    </li>
                  `
                )}
              </ul>
            `}
      </div>
    `;
  }
}

customElements.define("cda-alarm-panel", CdaAlarmPanel);
