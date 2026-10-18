import { Fragment, useEffect, useState, type FormEvent } from "react";
import { HardDrive, Monitor, Radar, Zap } from "lucide-react";

import {
  api,
  type ApplyChoice,
  type BulkKind,
  type BulkResult,
  type Discovered,
  type GameDisk,
  type Machine,
  type MachineMode,
  type MachineTraffic,
} from "../api";
import { AgentState, isOnline } from "../components/AgentState";
import { DiscoveredPanel } from "../components/DiscoveredPanel";
import { ErrorBanner } from "../components/ErrorBanner";
import { ImageStatus } from "../components/ImageStatus";
import { MachineDetails } from "../components/MachineDetails";
import { StatusBadge } from "../components/StatusBadge";
import { formatBytes, formatRate } from "../format";
import { useAsyncAction } from "../useAsyncAction";

interface Props {
  disks: GameDisk[];
  machines: Machine[];
  /** Sent / Received / Speed per machine id, read live from LIO. */
  traffic?: Record<number, MachineTraffic>;
  /** PCs that asked for a disk but are not registered. */
  discovered?: Discovered[];
  reload: () => Promise<void>;
}

const CLIENT_OFF = "The client PC must be powered off or disconnected.";
// Game disk letters; A-C are floppy and system drives.
const LETTERS = "DEFGHIJKLMNOPQRSTUVWXYZ".split("");
const MOVES_NOW = "Running PCs move the game disk within a minute; close games on them first.";

export function MachinesPage({ disks, machines, traffic = {}, discovered = [], reload }: Props) {
  const { busy, error, setError, run } = useAsyncAction();
  const [name, setName] = useState("");
  const [mac, setMac] = useState("");
  const [mode, setMode] = useState<MachineMode>("disk");
  const [diskId, setDiskId] = useState("");
  const [osDiskId, setOsDiskId] = useState("");
  // Boot Mode: which kept writebacks Apply Writebacks turns into versions, per machine.
  const [applyWhat, setApplyWhat] = useState<Record<number, ApplyKey>>({});
  const [allLetter, setAllLetter] = useState("D");
  // The machine whose hardware and network are shown.
  const [open, setOpen] = useState<number | null>(null);
  // Bulk operations: the selected machines and the last result.
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [bulkReport, setBulkReport] = useState<{ label: string; results: BulkResult[] } | null>(null);
  const picked = machines.filter((m) => selected.has(m.id));

  function toggle(id: number) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  }

  async function runBulk(
    label: string,
    action: BulkKind,
    extra: Parameters<typeof api.bulk>[2] = {},
    confirmText?: string,
  ) {
    if (confirmText && !window.confirm(`${confirmText}\n\n${picked.map((m) => m.name).join(", ")}`)) return;
    await run("bulk", async () => {
      setBulkReport({ label, results: await api.bulk([...selected], action, extra) });
    });
    await reload();
  }
  // Versions of each game disk in use, for the pin drop-down.
  const [versions, setVersions] = useState<Record<number, string[]>>({});

  const published = disks.filter((d) => d.published && d.kind !== "os");
  const osImages = disks.filter((d) => d.published && d.kind === "os");
  const inUse = published.filter((d) => machines.some((m) => m.game_disk_id === d.id));
  // Re-read when a disk gets a new version (Apply Writebacks, Make active).
  const versionKey = inUse.map((d) => `${d.id}@${d.snapshot}`).join(",");

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      inUse.map((d) =>
        api
          .listSnapshots(d.id)
          .then((s) => [d.id, s.map((v) => v.name)] as const)
          .catch(() => [d.id, []] as const),
      ),
    ).then((pairs) => {
      if (!cancelled) setVersions(Object.fromEntries(pairs));
    });
    return () => {
      cancelled = true;
    };
  }, [versionKey]); // inUse is derived from versionKey
  const diskName = (id: number | null) => disks.find((d) => d.id === id)?.name ?? "—";

  async function create(e: FormEvent) {
    e.preventDefault();
    const ok = await run("create", () =>
      api.createMachine({
        name: name.trim(),
        mode,
        mac: mac.trim(),
        game_disk_id: diskId ? Number(diskId) : null,
        os_disk_id: mode === "boot" && osDiskId ? Number(osDiskId) : null,
      }),
    );
    if (ok) {
      setName("");
      setMac("");
    }
    await reload();
  }

  async function assign(m: Machine, value: string) {
    const target = value ? Number(value) : null;
    if (target === m.game_disk_id && m.status === "provisioned") return;
    if (m.game_disk_id !== null || m.status !== "idle") {
      const msg =
        target === null
          ? `Remove the game disk from ${m.name}? Everything the client wrote is lost.`
          : `Switch ${m.name} to "${diskName(target)}"? Everything the client wrote is lost.`;
      if (!window.confirm(`${msg}\n\n${CLIENT_OFF}`)) return;
    }
    await run(`assign-${m.id}`, () => api.assignDisk(m.id, target));
    await reload();
  }

  async function setLetter(m: Machine, letter: string) {
    if (m.iscsi_connected && !window.confirm(`Move the game disk of ${m.name} to ${letter}:?\n\n${MOVES_NOW}`)) {
      return;
    }
    await run(`letter-${m.id}`, () => api.updateMachine(m.id, { drive_letter: letter }));
    await reload();
  }

  async function setLetterAll() {
    if (!window.confirm(`Set the game disk letter of every Disk Mode PC to ${allLetter}:?\n\n${MOVES_NOW}`)) {
      return;
    }
    await run("letter-all", () => api.setDriveLetterAll(allLetter));
    await reload();
  }

  async function power(m: Machine, action: "on" | "shutdown" | "reboot") {
    if (action !== "on") {
      const what = action === "shutdown" ? "Shut down" : "Restart";
      const msg =
        `${what} ${m.name}?\n\n` +
        "The agent gets it with its next heartbeat (within 30 s) and warns whoever sits at the PC 10 s before.";
      if (!window.confirm(msg)) return;
    }
    await run(`power-${m.id}`, () => api.power(m.id, action));
    await reload();
  }

    async function pin(m: Machine, value: string) {
    await run(`pin-${m.id}`, () => api.pinSnapshot(m.id, value || null));
    await reload();
  }

    async function keep(m: Machine, enabled: boolean) {
    if (!enabled) {
      const msg =
        `Stop keeping the writeback of ${m.name}?\n\n` +
        "Changes not applied yet are discarded the next time it disconnects.";
      if (!window.confirm(msg)) return;
    }
    await run(`keep-${m.id}`, () => api.setKeepWriteback(m.id, enabled));
    await reload();
  }

  async function apply(m: Machine) {
    const what: ApplyKey = m.mode === "boot" ? (applyWhat[m.id] ?? "both") : "game";
    const targets = [
      ...(what !== "game" ? [`the OS image "${diskName(m.os_disk_id ?? null)}"`] : []),
      ...(what !== "os" ? [`the game disk "${diskName(m.game_disk_id)}"`] : []),
    ];
    const kept =
      m.mode === "boot" && what !== "both"
        ? `\n\nThe ${what === "os" ? "game" : "OS"} writeback is not applied and stays kept as it is.`
        : "";
    const msg =
      `Apply the writebacks of ${m.name} to ${targets.join(" and ")}?\n\n` +
      "They become new versions. Every other PC gets them at its next reboot." +
      kept +
      `\n\n${m.name} must be powered off.`;
    if (!window.confirm(msg)) return;
    const comment = window.prompt("Comment for the new version (who, what changed). Optional.", "") ?? null;
    if (comment === null) return;
    const choice: ApplyChoice = {
      ...(m.mode === "boot" ? APPLY[what] : {}),
      ...(comment.trim() ? { comment: comment.trim() } : {}),
    };
    await run(`apply-${m.id}`, () =>
      api.applyWritebacks(m.id, Object.keys(choice).length > 0 ? choice : undefined),
    );
    await reload();
  }

  async function remove(m: Machine) {
    if (!window.confirm(`Delete ${m.name} and its disk on the host?\n\n${CLIENT_OFF}`)) return;
    await run(`delete-${m.id}`, () => api.deleteMachine(m.id));
    await reload();
  }

  return (
    <section>
      <ErrorBanner message={error} onClose={() => setError(null)} />

      <MachineKpis machines={machines} discovered={discovered.length} />

      <DiscoveredPanel discovered={discovered} disks={disks} busy={busy !== null} run={run} reload={reload} />

      <form className="card form-row" onSubmit={create}>
        <label>
          Name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. pc-01"
            required
            maxLength={15}
          />
        </label>
        <label>
          MAC
          <input
            value={mac}
            onChange={(e) => setMac(e.target.value)}
            placeholder="e.g. 10:ff:e0:66:be:3a"
            required
          />
        </label>
        <label>
          Mode
          <select value={mode} onChange={(e) => setMode(e.target.value as MachineMode)}>
            <option value="disk">Disk (local Windows)</option>
            <option value="boot">Boot (diskless)</option>
          </select>
        </label>
        {mode === "boot" && (
          <label>
            OS image
            <select value={osDiskId} onChange={(e) => setOsDiskId(e.target.value)} required>
              <option value="">Choose…</option>
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
          <select value={diskId} onChange={(e) => setDiskId(e.target.value)} required={mode === "boot"}>
            <option value="">None</option>
            {published.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={busy !== null}>
          {busy === "create" ? "Adding…" : "Add machine"}
        </button>
      </form>

      {machines.some((m) => m.mode === "disk") && (
        <div className="card form-row">
          <label>
            Game disk letter for all Disk Mode PCs
            <select value={allLetter} onChange={(e) => setAllLetter(e.target.value)}>
              {LETTERS.map((l) => (
                <option key={l} value={l}>
                  {l}:
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={setLetterAll} disabled={busy !== null}>
            {busy === "letter-all" ? "Applying…" : "Apply to all"}
          </button>
        </div>
      )}

      {picked.length > 0 && (
        <BulkBar
          machines={picked}
          disks={published}
          versions={versions}
          busy={busy !== null}
          run={runBulk}
          clear={() => setSelected(new Set())}
        />
      )}
      {bulkReport && <BulkReport {...bulkReport} onClose={() => setBulkReport(null)} />}

      {machines.length === 0 ? (
        <p className="empty">No machines yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  aria-label="Select all machines"
                  checked={machines.length > 0 && selected.size === machines.length}
                  onChange={(e) => setSelected(new Set(e.target.checked ? machines.map((m) => m.id) : []))}
                />
              </th>
              <th>Name</th>
              <th>Mode</th>
              <th>MAC</th>
              <th>Game disk</th>
              <th>Drive</th>
              <th>Status</th>
              <th>Agent</th>
              <th title="Since the PC's writeback was last cloned">Traffic</th>
              <th>Keep writeback</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {machines.map((m) => (
              <Fragment key={m.id}>
                <tr className={selected.has(m.id) ? "selected" : undefined}>
                  <td>
                    <input
                      type="checkbox"
                      aria-label={`Select ${m.name}`}
                      checked={selected.has(m.id)}
                      onChange={() => toggle(m.id)}
                    />
                  </td>
                  <td>
                    <div className="strong">{m.name}</div>
                    {m.reported_ip && <div className="mono muted small">{m.reported_ip}</div>}
                  </td>
                  <td>{m.mode === "disk" ? "Disk" : "Boot"}</td>
                  <td className="mono">{m.mac ?? "—"}</td>
                  <td>
                    {m.status === "editing" ? (
                      <span className="muted">Editing {diskName(m.editing_disk_id)}</span>
                    ) : m.mode === "disk" ? (
                      <select
                        aria-label={`Game disk for ${m.name}`}
                        value={m.game_disk_id ?? ""}
                        onChange={(e) => assign(m, e.target.value)}
                        disabled={busy !== null}
                      >
                        <option value="">None</option>
                        {published.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <BootDisks machine={m} diskName={diskName} />
                    )}
                    {m.mode === "disk" && m.game_disk_id !== null && m.status !== "editing" && (
                      <div className="image-version">
                        <select
                          aria-label={`Version for ${m.name}`}
                          value={m.pinned_snapshot ?? ""}
                          onChange={(e) => pin(m, e.target.value)}
                          disabled={busy !== null}
                        >
                          <option value="">
                            Follow active (@{disks.find((d) => d.id === m.game_disk_id)?.snapshot})
                          </option>
                          {(versions[m.game_disk_id] ?? (m.pinned_snapshot ? [m.pinned_snapshot] : [])).map(
                            (v) => (
                              <option key={v} value={v}>
                                Pin @{v}
                              </option>
                            ),
                          )}
                        </select>
                        <ImageStatus machine={m} disk={disks.find((d) => d.id === m.game_disk_id)} />
                      </div>
                    )}
                  </td>
                  <td>
                    {m.mode === "disk" ? (
                      <select
                        aria-label={`Drive letter for ${m.name}`}
                        value={m.drive_letter}
                        onChange={(e) => setLetter(m, e.target.value)}
                        disabled={busy !== null}
                      >
                        {LETTERS.map((l) => (
                          <option key={l} value={l}>
                            {l}:
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="muted">D:</span>
                    )}
                    {m.reported_drive_letter && m.reported_drive_letter !== m.drive_letter && (
                      <div>
                        <span
                          className="badge badge-warn"
                          title={`${m.drive_letter}: is taken on this PC, so the game disk got ${m.reported_drive_letter}:`}
                        >
                          Got {m.reported_drive_letter}:
                        </span>
                      </div>
                    )}
                  </td>
                  <td>
                    <StatusBadge status={m.status} />
                    {m.last_error && <div className="error-text small">{m.last_error}</div>}
                  </td>
                  <td>
                    <AgentState machine={m} />
                  </td>
                  <td className="small">
                    <TrafficCell traffic={traffic[m.id]} />
                  </td>
                  <td>
                    <input
                      type="checkbox"
                      aria-label={`Keep writeback of ${m.name}`}
                      checked={m.keep_writeback}
                      onChange={(e) => keep(m, e.target.checked)}
                      disabled={busy !== null}
                    />
                  </td>
                  <td className="actions">
                    <button
                      type="button"
                      className="secondary"
                      aria-expanded={open === m.id}
                      onClick={() => setOpen(open === m.id ? null : m.id)}
                    >
                      {open === m.id ? "Hide details" : "Details"}
                    </button>
                    {isOnline(m) ? (
                      <>
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => power(m, "shutdown")}
                          disabled={busy !== null || m.pending_command !== null}
                        >
                          Shutdown
                        </button>
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => power(m, "reboot")}
                          disabled={busy !== null || m.pending_command !== null}
                        >
                          Reboot
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => power(m, "on")}
                        disabled={busy !== null || (!m.mac && !m.reported_mac)}
                        title={!m.mac && !m.reported_mac ? "No MAC address yet" : "Wake-on-LAN"}
                      >
                        {busy === `power-${m.id}` ? "Waking…" : "Turn on"}
                      </button>
                    )}
                    {m.keep_writeback && m.status === "provisioned" && m.mode === "boot" && (
                      <select
                        aria-label={`What to apply from ${m.name}`}
                        value={applyWhat[m.id] ?? "both"}
                        onChange={(e) => setApplyWhat({ ...applyWhat, [m.id]: e.target.value as ApplyKey })}
                        disabled={busy !== null}
                      >
                        <option value="both">OS + game</option>
                        <option value="os">OS only</option>
                        <option value="game">Game only</option>
                      </select>
                    )}
                    {m.keep_writeback && m.status === "provisioned" && (
                      <button
                        type="button"
                        onClick={() => apply(m)}
                        disabled={busy !== null || m.session_active === true}
                        title={m.session_active ? `Shut down ${m.name} first` : undefined}
                      >
                        {busy === `apply-${m.id}` ? "Applying…" : "Apply writebacks"}
                      </button>
                    )}
                    <button
                      type="button"
                      className="danger"
                      onClick={() => remove(m)}
                      disabled={busy !== null || m.status === "editing"}
                      title={m.status === "editing" ? "Finish editing the game disk first" : undefined}
                    >
                      {busy === `delete-${m.id}` ? "Deleting…" : "Delete"}
                    </button>
                  </td>
                </tr>
                {open === m.id && (
                  <tr>
                    <td colSpan={9}>
                      <MachineDetails machine={m} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

/** ggRock's Sent / Received / Speed for one machine. */
function TrafficCell({ traffic: t }: { traffic: MachineTraffic | undefined }) {
  if (!t) return <span className="muted">—</span>;
  return (
    <div aria-label="Traffic">
      <div>
        Sent {formatBytes(t.sent_bytes)} · Received {formatBytes(t.received_bytes)}
      </div>
      {t.sent_bps !== null && t.received_bps !== null && (
        <div className="muted">
          ↓ {formatRate(t.sent_bps)} · ↑ {formatRate(t.received_bps)}
        </div>
      )}
    </div>
  );
}

interface BulkBarProps {
  machines: Machine[];
  disks: GameDisk[];
  versions: Record<number, string[]>;
  busy: boolean;
  run: (label: string, action: BulkKind, extra?: Parameters<typeof api.bulk>[2], confirmText?: string) => void;
  clear: () => void;
}

/** ggRock's bulk operations on the selected machines. */
function BulkBar({ machines, disks, versions, busy, run, clear }: BulkBarProps) {
  const [disk, setDisk] = useState("");
  const [version, setVersion] = useState("");
  const [letter, setLetter] = useState("D");
  const n = machines.length;
  // A version can be pinned on several PCs only when they share a game disk.
  const diskIds = new Set(machines.map((m) => m.game_disk_id));
  const shared = diskIds.size === 1 ? [...diskIds][0] : null;
  const sharedVersions = shared !== null ? (versions[shared] ?? []) : [];

  return (
    <div className="card bulk-bar" aria-label="Bulk actions">
      <span className="strong">{n} selected</span>
      <button type="button" className="secondary" disabled={busy} onClick={() => run("Turn on", "on")}>
        Turn on
      </button>
      <button
        type="button"
        className="secondary"
        disabled={busy}
        onClick={() => run("Shutdown", "shutdown", {}, `Shut down ${n} PC(s)?`)}
      >
        Shutdown
      </button>
      <button
        type="button"
        className="secondary"
        disabled={busy}
        onClick={() => run("Reboot", "reboot", {}, `Restart ${n} PC(s)?`)}
      >
        Reboot
      </button>

      <span className="bulk-group">
        <select aria-label="Game disk for selected" value={disk} onChange={(e) => setDisk(e.target.value)}>
          <option value="">Game disk…</option>
          <option value="none">None (remove)</option>
          {disks.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <button
          type="button"
          disabled={busy || !disk}
          onClick={() =>
            run(
              "Game disk",
              "assign",
              { game_disk_id: disk === "none" ? null : Number(disk) },
              `Set the game disk of ${n} PC(s)? Everything they wrote is lost. ${CLIENT_OFF}`,
            )
          }
        >
          Apply
        </button>
      </span>

      {shared !== null && (
        <span className="bulk-group">
          <select aria-label="Version for selected" value={version} onChange={(e) => setVersion(e.target.value)}>
            <option value="">Version…</option>
            <option value="follow">Follow active</option>
            {sharedVersions.map((v) => (
              <option key={v} value={v}>
                Pin @{v}
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={busy || !version}
            onClick={() => run("Version", "pin", { snapshot: version === "follow" ? null : version })}
          >
            Apply
          </button>
        </span>
      )}

      <span className="bulk-group">
        <select aria-label="Drive letter for selected" value={letter} onChange={(e) => setLetter(e.target.value)}>
          {LETTERS.map((l) => (
            <option key={l} value={l}>
              {l}:
            </option>
          ))}
        </select>
        <button
          type="button"
          disabled={busy}
          onClick={() => run("Drive letter", "drive_letter", { drive_letter: letter }, `${MOVES_NOW}`)}
        >
          Apply
        </button>
      </span>

      <button
        type="button"
        className="secondary"
        disabled={busy || !machines.some((m) => m.keep_writeback)}
        onClick={() => run("Stop keeping writeback", "stop_keep_writeback")}
      >
        Stop keeping writeback
      </button>
      <button type="button" className="link" aria-label="Clear selection" onClick={clear}>
        ×
      </button>
    </div>
  );
}

/** "Turn on: done on 3, failed on 1" with the reason per failed PC. */
function BulkReport({ label, results, onClose }: { label: string; results: BulkResult[]; onClose: () => void }) {
  const failed = results.filter((r) => !r.ok);
  const done = results.length - failed.length;
  return (
    <div className={failed.length ? "banner banner-warn" : "banner"} role="status">
      <div>
        <span className="strong">{label}</span>: done on {done}
        {failed.length > 0 && `, failed on ${failed.length}`}
        {failed.map((r) => (
          <div key={r.machine_id} className="small">
            {r.name ?? `#${r.machine_id}`}: {r.error}
          </div>
        ))}
      </div>
      <button type="button" className="link" aria-label="Close" onClick={onClose}>
        ×
      </button>
    </div>
  );
}

type ApplyKey = "both" | "os" | "game";
const APPLY: Record<ApplyKey, ApplyChoice> = {
  both: { os: true, game: true },
  os: { os: true, game: false },
  game: { os: false, game: true },
};

/** Boot Mode: the OS image and game disk a PC runs, with their versions. */
function BootDisks({ machine: m, diskName }: { machine: Machine; diskName: (id: number | null) => string }) {
  const version = (snap: string | null | undefined) => (snap ? `@${snap.split("@")[1]}` : "");
  return (
    <div className="small">
      <div>
        <span className="muted">OS </span>
        {diskName(m.os_disk_id ?? null)} <span className="muted">{version(m.os_clone_snapshot)}</span>
      </div>
      <div>
        <span className="muted">Game </span>
        {diskName(m.game_disk_id)} <span className="muted">{version(m.clone_snapshot)}</span>
      </div>
    </div>
  );
}

/** Summary cards above the machine list. */
function MachineKpis({ machines, discovered }: { machines: Machine[]; discovered: number }) {
  const online = machines.filter((m) => isOnline(m)).length;
  const writebacks = machines.filter((m) => m.keep_writeback || m.writeback_dirty).length;
  const boot = machines.filter((m) => m.mode === "boot").length;
  const cards = [
    { title: "Machines", value: machines.length, sub: `${boot} Boot Mode · ${machines.length - boot} Disk Mode`, icon: Monitor, tone: "blue" },
    { title: "Online", value: online, sub: `${machines.length - online} off or not reporting`, icon: Zap, tone: "green" },
    { title: "Writebacks", value: writebacks, sub: "written since the last reset, or kept", icon: HardDrive, tone: "amber" },
    { title: "New PCs", value: discovered, sub: "knocked but not registered", icon: Radar, tone: "purple" },
  ];
  return (
    <div className="kpi-grid">
      {cards.map(({ title, value, sub, icon: Icon, tone }) => (
        <div key={title} className="kpi-card">
          <div className="kpi-info">
            <span className="kpi-title">{title}</span>
            <span className="kpi-value">{value}</span>
            <span className="kpi-subtitle">{sub}</span>
          </div>
          <div className={`kpi-icon-box ${tone}`}>
            <Icon size={22} />
          </div>
        </div>
      ))}
    </div>
  );
}
