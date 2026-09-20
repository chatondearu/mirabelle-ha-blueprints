/**
 * CDA Alarm sidebar panel (Lit, CDN).
 * Tabs: Sensors | General | Response | Linked
 */
import {
  LitElement,
  html,
  css,
  nothing,
} from "https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js";

const WS_GET = "cda_alarm/get_config";
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
    _config: { state: true },
    _linked: { state: true },
    _loading: { state: true },
    _saving: { state: true },
    _error: { state: true },
    _message: { state: true },
    _newEntity: { state: true },
    _codesJson: { state: true },
  };

  static styles = css`
    :host {
      display: block;
      padding: 16px;
      max-width: 960px;
      margin: 0 auto;
      font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
      color: var(--primary-text-color);
    }
    h1 {
      margin: 0 0 8px;
      font-size: 1.6rem;
    }
    .subtitle {
      color: var(--secondary-text-color);
      margin-bottom: 16px;
    }
    .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--divider-color);
      padding-bottom: 8px;
    }
    .tabs button {
      background: transparent;
      border: 1px solid var(--divider-color);
      border-radius: 6px;
      padding: 8px 12px;
      cursor: pointer;
      color: var(--primary-text-color);
    }
    .tabs button.active {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border-color: var(--primary-color);
    }
    .card {
      background: var(--card-background-color, var(--ha-card-background, #fff));
      border-radius: 8px;
      padding: 16px;
      box-shadow: var(--ha-card-box-shadow, none);
      border: 1px solid var(--divider-color);
      margin-bottom: 16px;
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }
    .sensor-row {
      display: grid;
      grid-template-columns: minmax(180px, 1fr) repeat(3, auto) auto;
      gap: 8px;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.95rem;
    }
    input[type="text"],
    input[type="number"],
    select,
    textarea {
      width: 100%;
      box-sizing: border-box;
      padding: 8px;
      border-radius: 4px;
      border: 1px solid var(--divider-color);
      background: var(--input-fill-color, transparent);
      color: var(--primary-text-color);
    }
    textarea {
      min-height: 140px;
      font-family: ui-monospace, monospace;
    }
    .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 16px;
    }
    button.primary,
    button.secondary,
    button.danger {
      border: none;
      border-radius: 6px;
      padding: 10px 14px;
      cursor: pointer;
    }
    button.primary {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    button.secondary {
      background: var(--secondary-background-color, #eee);
      color: var(--primary-text-color);
    }
    button.danger {
      background: var(--error-color, #db4437);
      color: #fff;
    }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .banner {
      padding: 10px 12px;
      border-radius: 6px;
      margin-bottom: 12px;
    }
    .banner.error {
      background: rgba(219, 68, 55, 0.15);
      color: var(--error-color, #db4437);
    }
    .banner.ok {
      background: rgba(15, 157, 88, 0.15);
      color: var(--success-color, #0f9d58);
    }
    .muted {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }
    a {
      color: var(--primary-color);
    }
    .keypad-card {
      border: 1px solid var(--divider-color);
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 10px;
    }
    ul.linked {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    ul.linked li {
      padding: 10px 0;
      border-bottom: 1px solid var(--divider-color);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
  `;

  constructor() {
    super();
    this._tab = "sensors";
    this._config = null;
    this._linked = null;
    this._loading = false;
    this._saving = false;
    this._error = "";
    this._message = "";
    this._newEntity = "";
    this._codesJson = "[]";
  }

  updated(changed) {
    if (changed.has("hass") && this.hass && !this._config && !this._loading) {
      this._load();
    }
  }

  async _load() {
    if (!this.hass) return;
    this._loading = true;
    this._error = "";
    try {
      const config = await this.hass.connection.sendMessagePromise({
        type: WS_GET,
      });
      this._config = this._normalizeConfig(config);
      this._codesJson = JSON.stringify(this._config.codes || [], null, 2);
      if (this._tab === "linked") {
        await this._loadLinked();
      }
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._loading = false;
    }
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
    this._tab = tab;
    this._message = "";
    if (tab === "linked") {
      await this._loadLinked();
    }
  }

  _entityLabel(entityId) {
    const state = this.hass?.states?.[entityId];
    const name = state?.attributes?.friendly_name;
    return name ? `${name} (${entityId})` : entityId;
  }

  _availableEntities() {
    if (!this.hass?.states) return [];
    return Object.keys(this.hass.states).sort();
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
    this._config = {
      ...this._config,
      sensor_assignments: this._config.sensor_assignments.filter(
        (item) => item.entity_id !== entityId
      ),
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

  _parseEntityList(text) {
    return String(text || "")
      .split(/[\n,]+/)
      .map((item) => item.trim())
      .filter(Boolean);
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
      let codes;
      try {
        codes = JSON.parse(this._codesJson || "[]");
      } catch {
        throw new Error("Codes JSON is invalid.");
      }
      if (!Array.isArray(codes)) {
        throw new Error("Codes must be a JSON array.");
      }
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
      };
      const updated = await this.hass.connection.sendMessagePromise({
        type: WS_UPDATE,
        entry_id: this._config.entry_id,
        config: payload,
      });
      this._config = this._normalizeConfig(updated);
      this._codesJson = JSON.stringify(this._config.codes || [], null, 2);
      this._message = "Saved.";
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._saving = false;
    }
  }

  render() {
    if (this._loading && !this._config) {
      return html`<div class="card">Loading CDA Alarm…</div>`;
    }
    if (!this._config) {
      return html`
        <div class="card">
          <p>No CDA Alarm config entry found. Add the integration first.</p>
          ${this._error
            ? html`<div class="banner error">${this._error}</div>`
            : nothing}
        </div>
      `;
    }

    return html`
      <h1>CDA Alarm</h1>
      <p class="subtitle">
        Unified configuration for sensors, keypads, delays, and alarm response.
      </p>
      ${this._error
        ? html`<div class="banner error">${this._error}</div>`
        : nothing}
      ${this._message
        ? html`<div class="banner ok">${this._message}</div>`
        : nothing}
      <div class="tabs">
        ${["sensors", "general", "response", "linked"].map(
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
      ${this._tab === "sensors" ? this._renderSensors() : nothing}
      ${this._tab === "general" ? this._renderGeneral() : nothing}
      ${this._tab === "response" ? this._renderResponse() : nothing}
      ${this._tab === "linked" ? this._renderLinked() : nothing}
      ${this._tab !== "linked"
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
    `;
  }

  _renderSensors() {
    const entities = this._availableEntities();
    return html`
      <div class="card">
        <p class="muted">
          Add entities once, then choose Away / Home / Night for each.
        </p>
        <div class="row">
          <select
            .value=${this._newEntity}
            @change=${(e) => {
              this._newEntity = e.target.value;
            }}
          >
            <option value="">Select entity…</option>
            ${entities.map(
              (id) => html`<option value=${id}>${this._entityLabel(id)}</option>`
            )}
          </select>
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
              .value=${String(this._config.entry_delay ?? 30)}
              @change=${(e) =>
                this._setField("entry_delay", Number(e.target.value))}
            />
          </label>
          <label
            >Exit delay (s)
            <input
              type="number"
              min="0"
              .value=${String(this._config.exit_delay ?? 60)}
              @change=${(e) =>
                this._setField("exit_delay", Number(e.target.value))}
            />
          </label>
          <label>
            <input
              type="checkbox"
              .checked=${Boolean(this._config.block_arm_if_open)}
              @change=${(e) =>
                this._setField("block_arm_if_open", e.target.checked)}
            />
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
                  <input
                    type="checkbox"
                    .checked=${Boolean(item.is_default)}
                    @change=${(e) =>
                      this._updateKeypad(item.device_id, {
                        is_default: e.target.checked,
                      })}
                  />
                  Default
                </label>
                <label>
                  <input
                    type="checkbox"
                    .checked=${Boolean(item.feedback)}
                    @change=${(e) =>
                      this._updateKeypad(item.device_id, {
                        feedback: e.target.checked,
                      })}
                  />
                  Feedback
                </label>
                <label
                  >Endpoint
                  <input
                    type="number"
                    min="1"
                    max="255"
                    .value=${String(item.endpoint ?? 44)}
                    @change=${(e) =>
                      this._updateKeypad(item.device_id, {
                        endpoint: Number(e.target.value),
                      })}
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
        <h3>Codes (JSON)</h3>
        <p class="muted">
          Array of objects with optional string fields:
          <code>name</code>, <code>pin</code>, <code>rfid</code>,
          <code>nfc_tag_id</code>.
        </p>
        <textarea
          .value=${this._codesJson}
          @input=${(e) => {
            this._codesJson = e.target.value;
          }}
        ></textarea>
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
        <label
          >Siren entities (comma or newline separated)
          <textarea
            .value=${(response.sirens || []).join("\n")}
            @change=${(e) =>
              this._setField(
                "response.sirens",
                this._parseEntityList(e.target.value)
              )}
          ></textarea>
        </label>
        <div class="row">
          <label
            >Duration (s, 0 = default)
            <input
              type="number"
              min="0"
              .value=${String(response.siren_duration ?? 0)}
              @change=${(e) =>
                this._setField(
                  "response.siren_duration",
                  Number(e.target.value)
                )}
            />
          </label>
          <label
            >Tone
            <input
              type="text"
              .value=${response.siren_tone || ""}
              @change=${(e) =>
                this._setField("response.siren_tone", e.target.value)}
            />
          </label>
        </div>
      </div>

      <div class="card">
        <h3>Noise media</h3>
        <label
          >Media players
          <textarea
            .value=${(response.noise_media_players || []).join("\n")}
            @change=${(e) =>
              this._setField(
                "response.noise_media_players",
                this._parseEntityList(e.target.value)
              )}
          ></textarea>
        </label>
        <label
          >Sound content id
          <input
            type="text"
            .value=${response.alarm_sound_content_id || ""}
            @change=${(e) =>
              this._setField("response.alarm_sound_content_id", e.target.value)}
          />
        </label>
        <label
          >Volume (0–1)
          <input
            type="number"
            min="0"
            max="1"
            step="0.05"
            .value=${String(response.noise_volume ?? 0.9)}
            @change=${(e) =>
              this._setField("response.noise_volume", Number(e.target.value))}
          />
        </label>
      </div>

      <div class="card">
        <h3>TTS</h3>
        <label>
          <input
            type="checkbox"
            .checked=${Boolean(response.enable_alarm_tts)}
            @change=${(e) =>
              this._setField("response.enable_alarm_tts", e.target.checked)}
          />
          Enable alarm TTS
        </label>
        <label
          >Message
          <input
            type="text"
            .value=${response.alarm_tts_message || ""}
            @change=${(e) =>
              this._setField("response.alarm_tts_message", e.target.value)}
          />
        </label>
        <label
          >TTS media players
          <textarea
            .value=${(response.tts_media_players || []).join("\n")}
            @change=${(e) =>
              this._setField(
                "response.tts_media_players",
                this._parseEntityList(e.target.value)
              )}
          ></textarea>
        </label>
        <p class="muted">
          Response starts when the panel enters <code>triggered</code> and stops
          on disarm / leave-triggered. Clear sirens/noise on
          <strong>[CDA] Alarm Response</strong> to avoid double sound.
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
