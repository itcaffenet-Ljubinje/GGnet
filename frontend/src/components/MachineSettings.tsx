import { useEffect, useState, type FormEvent } from "react";
import { Cpu, HardDrive, Monitor, Network, Save, Settings, X } from "lucide-react";

import { api, type GameDisk, type Machine, type MachineMode } from "../api";
import { formatBytes, formatLink } from "../format";
import { useAsyncAction } from "../useAsyncAction";
import { isOnline } from "./AgentState";
import { ErrorBanner } from "./ErrorBanner";

interface Props {
  machine: Machine;
  disks: GameDisk[];
  onClose: () => void;
  reload: () => Promise<void>;
}

type Tab = "general" | "disks" | "network" | "hardware";

// Game disk letters; A-C are floppy and system drives.
const LETTERS = "DEFGHIJKLMNOPQRSTUVWXYZ".split("");

/**
 * Everything about one PC in one place (ggRock's machine settings). Save
 * sends only what changed: name, mode, MAC and drive letter; the disks (which
 * re-clones the writebacks, so it asks first); Keep Writeback; the pinned version.
 */
export function MachineSettings({ machine: m, disks, onClose, reload }: Props) {
  const { busy, error, setError, run } = useAsyncAction();
  const [tab, setTab] = useState<Tab>("general");
  const [name, setName] = useState(m.name);
  const [mac, setMac] = useState(m.mac ?? "");
  const [mode, setMode] = useState<MachineMode>(m.mode);
  const [osDiskId, setOsDiskId] = useState(m.os_disk_id ? String(m.os_disk_id) : "");
  const [diskId, setDiskId] = useState(m.game_disk_id ? String(m.game_disk_id) : "");
  const [letter, setLetter] = useState(m.drive_letter);
  const [keep, setKeep] = useState(m.keep_writeback);
  const [pin, setPin] = useState(m.pinned_snapshot ?? "");
  const [versions, setVersions] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);

  const osImages = disks.filter((d) => d.published && d.kind === "os");
  const gameDisks = disks.filter((d) => d.published && d.kind !== "os");
  const hasDisk = m.game_disk_id !== null || m.status !== "idle";
  const online = isOnline(m);

  useEffect(() => {
    if (!m.game_disk_id) return;
    api
      .listSnapshots(m.game_disk_id)
      .then((s) => setVersions(s.map((v) => v.name)))
      .catch(() => setVersions([]));
  }, [m.game_disk_id]);

  const disksChanged =
    diskId !== (m.game_disk_id ? String(m.game_disk_id) : "") ||
    (mode === "boot" && osDiskId !== (m.os_disk_id ? String(m.os_disk_id) : ""));

  async function save(e: FormEvent) {
    e.preventDefault();
    setSaved(false);
    const patch: Record<string, string | null> = {};
    if (name.trim() !== m.name) patch.name = name.trim();
    if (mode !== m.mode) patch.mode = mode;
    if ((mac.trim() || null) !== m.mac) patch.mac = mac.trim() || null;
    if (mode === "disk" && letter !== m.drive_letter) patch.drive_letter = letter;
    if (disksChanged && m.game_disk_id !== null) {
      const msg =
        `Change the disks of ${m.name}? Its writebacks are cloned again from the new disks, ` +
        "so everything the PC wrote is lost.\n\nThe PC must be powered off or disconnected.";
      if (!window.confirm(msg)) return;
    }
    const ok = await run("save", async () => {
      if (Object.keys(patch).length > 0) await api.updateMachine(m.id, patch as Parameters<typeof api.updateMachine>[1]);
      if (disksChanged) {
        await api.assignDisk(
          m.id,
          diskId ? Number(diskId) : null,
          mode === "boot" ? (osDiskId ? Number(osDiskId) : null) : undefined,
        );
      }
      if (keep !== m.keep_writeback) await api.setKeepWriteback(m.id, keep);
      if (!disksChanged && (pin || null) !== m.pinned_snapshot) await api.pinSnapshot(m.id, pin || null);
    });
    await reload();
    if (ok) setSaved(true);
  }

  const tabs: { id: Tab; label: string; icon: typeof Settings }[] = [
    { id: "general", label: "General", icon: Settings },
    { id: "disks", label: "Disks", icon: HardDrive },
    { id: "network", label: "Network", icon: Network },
    { id: "hardware", label: "Hardware", icon: Cpu },
  ];
  const hw = m.hardware;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-content machine-settings-modal"
        role="dialog"
        aria-label={`Settings of ${m.name}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div className={`machine-status-avatar ${online ? "online" : "offline"}`}>
              <Monitor size={20} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <h2>{m.name}</h2>
                <span className={`badge ${online ? "badge-provisioned" : "badge-warn"}`}>
                  {online ? "Online" : "Offline"}
                </span>
                <span className={`mode-pill ${m.mode === "boot" ? "mode-pill-boot" : "mode-pill-disk"}`}>
                  {m.mode === "boot" ? "Boot Mode" : "Disk Mode"}
                </span>
              </div>
              <p className="modal-subheading">
                {m.reported_ip ?? "No IP reported"} · MAC {m.mac ?? "not set"}
              </p>
            </div>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="settings-tabs-bar" role="tablist">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={tab === id}
              className={`settings-tab-btn ${tab === id ? "active" : ""}`}
              onClick={() => setTab(id)}
            >
              <Icon size={14} />
              <span>{label}</span>
            </button>
          ))}
        </div>

        <form onSubmit={save}>
          <div className="settings-modal-body">
            <ErrorBanner message={error} onClose={() => setError(null)} />

            {tab === "general" && (
              <div className="form-grid-2">
                <label>
                  Name
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    maxLength={15}
                    required
                    disabled={hasDisk}
                    title={hasDisk ? "Remove its disks first: the name is part of its writebacks" : undefined}
                  />
                </label>
                <label className="check">
                  <input type="checkbox" checked={keep} onChange={(e) => setKeep(e.target.checked)} />
                  Keep writeback (changes survive reboots; for installing and updating)
                </label>
              </div>
            )}

            {tab === "disks" && (
              <div className="form-grid-2">
                <label>
                  Mode
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value as MachineMode)}
                    disabled={hasDisk}
                    title={hasDisk ? "Remove its disks first" : undefined}
                  >
                    <option value="disk">Disk (local Windows)</option>
                    <option value="boot">Boot (diskless)</option>
                  </select>
                </label>
                {mode === "boot" && (
                  <label>
                    OS image
                    <select value={osDiskId} onChange={(e) => setOsDiskId(e.target.value)}>
                      <option value="">None</option>
                      {osImages.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <label>
                  Game disk
                  <select value={diskId} onChange={(e) => setDiskId(e.target.value)}>
                    <option value="">None</option>
                    {gameDisks.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </label>
                {mode === "disk" && (
                  <label>
                    Game disk letter
                    <select value={letter} onChange={(e) => setLetter(e.target.value)}>
                      {LETTERS.map((l) => (
                        <option key={l} value={l}>
                          {l}:
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                {m.game_disk_id !== null && !disksChanged && (
                  <label>
                    Game disk version
                    <select value={pin} onChange={(e) => setPin(e.target.value)}>
                      <option value="">Follow the active version</option>
                      {versions.map((v) => (
                        <option key={v} value={v}>
                          Pin @{v}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
              </div>
            )}

            {tab === "network" && (
              <div className="form-grid-2">
                <label>
                  MAC (identifies the PC)
                  <input value={mac} onChange={(e) => setMac(e.target.value)} placeholder="e.g. 10:ff:e0:66:be:3a" />
                </label>
                <div>
                  <div className="muted small">Reported by the agent</div>
                  <div>IP {m.reported_ip ?? "—"}</div>
                  <div>MAC {m.reported_mac ?? "—"}</div>
                  <div>Link {m.link_speed_mbps ? formatLink(m.link_speed_mbps) : "—"}</div>
                </div>
              </div>
            )}

            {tab === "hardware" && (
              <dl className="details">
                <dt>CPU</dt>
                <dd>{hw?.cpu ?? "—"}</dd>
                <dt>GPU</dt>
                <dd>{hw?.gpus?.length ? hw.gpus.join(", ") : "—"}</dd>
                <dt>Motherboard</dt>
                <dd>{hw?.motherboard ?? "—"}</dd>
                <dt>Memory</dt>
                <dd>{hw?.memory_bytes ? formatBytes(hw.memory_bytes) : "—"}</dd>
                <dt>Network card</dt>
                <dd>{hw?.nic ?? "—"}</dd>
                <dt>Agent</dt>
                <dd>{m.agent_version ?? "not installed"}</dd>
              </dl>
            )}
          </div>

          <div className="modal-footer">
            <div className="footer-left" />
            <div className="footer-right">
              {saved && <span className="save-success-tag">Saved</span>}
              <button type="button" className="secondary" onClick={onClose} disabled={busy !== null}>
                Close
              </button>
              <button type="submit" className="btn-primary" disabled={busy !== null || !name.trim()}>
                <Save size={14} />
                {busy === "save" ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
