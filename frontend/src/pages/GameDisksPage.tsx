import { Fragment, useState, type FormEvent } from "react";
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Gamepad2,
  HardDrive,
  Layers,
  Monitor,
  Pencil,
  Plus,
  Trash2,
  Type,
  Wand2,
  type LucideIcon,
} from "lucide-react";

import { api, type DiskKind, type GameDisk, type Machine } from "../api";
import { DiskDetails } from "../components/DiskDetails";
import { ErrorBanner } from "../components/ErrorBanner";
import { useAsyncAction } from "../useAsyncAction";

interface Props {
  disks: GameDisk[];
  machines: Machine[];
  reload: () => Promise<void>;
}

export function GameDisksPage({ disks, machines, reload }: Props) {
  const { busy, error, setError, run } = useAsyncAction();
  const [name, setName] = useState("");
  const [sizeGb, setSizeGb] = useState("100");
  const [kind, setKind] = useState<DiskKind>("game");
  // Per draft disk: the machine picked to fill it on.
  const [editOn, setEditOn] = useState<Record<number, string>>({});
  // The disk whose versions and writebacks are shown.
  const [open, setOpen] = useState<number | null>(null);

  const assigned = (id: number) =>
    machines.filter((m) => m.game_disk_id === id || m.os_disk_id === id).length;
  const machine = (id: number | null) => machines.find((m) => m.id === id);
  // A draft can be filled only on a disk-mode PC that has no game disk.
  const free = machines.filter(
    (m) => m.mode === "disk" && m.status === "idle" && m.game_disk_id === null,
  );

  async function create(e: FormEvent) {
    e.preventDefault();
    const ok = await run("create", () => api.createDisk(name.trim(), Number(sizeGb), kind));
    if (ok) setName("");
    await reload();
  }

  async function publish(disk: GameDisk) {
    const msg =
      `Publish "${disk.name}"?\n\n` +
      "This takes the @base snapshot and makes the master read-only. " +
      "Fill it with data first; after publishing it cannot be changed.";
    if (!window.confirm(msg)) return;
    await run(`publish-${disk.id}`, () => api.publishDisk(disk.id));
    await reload();
  }

  async function startEdit(disk: GameDisk) {
    const m = machine(Number(editOn[disk.id]));
    if (!m) return;
    const msg =
      `Edit "${disk.name}" on ${m.name}?\n\n` +
      "The master becomes that PC's game disk (through ggnet-agent). Initialize and format it " +
      "in Disk Management, install the games, then shut the PC down and click Finish editing.";
    if (!window.confirm(msg)) return;
    await run(`edit-${disk.id}`, () => api.startEdit(disk.id, m.id));
    await reload();
  }

  async function finishEdit(disk: GameDisk) {
    const name = machine(disk.editor_id)?.name ?? "the PC";
    if (!window.confirm(`Finish editing "${disk.name}"?\n\nThe master is removed from ${name}.`)) return;
    await run(`finish-${disk.id}`, () => api.finishEdit(disk.id));
    await reload();
  }

  async function prepare(disk: GameDisk) {
    const msg =
      `Prepare "${disk.name}" for all PCs?\n\n` +
      "A new version is made from the newest one, with the server's agent (Settings → Client app) and " +
      "its service, Fast Startup off, fixed IP addresses switched to DHCP and old drive letters forgotten.\n\n" +
      "Windows is also set up for diskless PCs: High performance, no sleep or hibernation (the display " +
      "stays on), PCIe, USB and network card power saving off, a fixed 4 GB page file, no crash dumps, " +
      "no automatic Windows Update, Store updates, maintenance (defragmentation), search index or SysMain, " +
      "and the iSCSI driver loaded after the network, which saves about 25 s of every start.\n\n" +
      "PCs move to it at their next reboot. Apply Writebacks of an OS image does this already.";
    if (!window.confirm(msg)) return;
    await run(`prepare-${disk.id}`, () => api.prepareImage(disk.id));
    await reload();
  }

  async function rename(disk: GameDisk) {
    const what = disk.kind === "os" ? "OS image" : "game disk";
    const next = window.prompt(
      `New name for ${what} "${disk.name}" (a-z, 0-9 and -, up to 32 characters).\n\n` +
        "Only the name in ggNet changes; the zvol, its versions and the PCs' writebacks stay as they are.",
      disk.name,
    );
    const name = next?.trim().toLowerCase();
    if (!name || name === disk.name) return;
    await run(`rename-${disk.id}`, () => api.renameDisk(disk.id, name));
    await reload();
  }

  async function remove(disk: GameDisk) {
    const what = disk.kind === "os" ? "OS image" : "game disk";
    if (!window.confirm(`Delete ${what} "${disk.name}" and its zvol on the host?`)) return;
    await run(`delete-${disk.id}`, () => api.deleteDisk(disk.id));
    await reload();
  }

  function section(title: string, Icon: LucideIcon, list: GameDisk[], empty: string) {
    return (
      <>
        <h2 className="section-title title-with-icon">
          <Icon size={16} aria-hidden />
          {title}
          <span className="tab-badge" aria-label={`${list.length} in all`}>
            {list.length}
          </span>
        </h2>
        {list.length === 0 ? (
          <p className="empty">{empty}</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Size</th>
                  <th>State</th>
                  <th>Machines</th>
                  <th>ZFS path</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {list.map((d) => (
                  <Fragment key={d.id}>
                    <tr>
                      <td className="strong">
                        <span className="name-with-icon">
                          {d.kind === "os" ? (
                            <Monitor size={15} className="kind-icon kind-os" aria-hidden />
                          ) : (
                            <Gamepad2 size={15} className="kind-icon kind-game" aria-hidden />
                          )}
                          {d.name}
                        </span>
                      </td>
                      <td>{d.size_gb} GB</td>
                      <td>
                        {d.published ? (
                          <span className="badge badge-provisioned">Published @{d.snapshot}</span>
                        ) : d.editor_id !== null ? (
                          <span className="badge badge-editing">
                            Editing on {machine(d.editor_id)?.name ?? `#${d.editor_id}`}
                          </span>
                        ) : (
                          <span className="badge badge-idle">Draft</span>
                        )}
                      </td>
                      <td>{assigned(d.id)}</td>
                      <td className="mono muted">{d.zvol_path}</td>
                      <td className="actions">
                        {d.published && (
                          <button
                            type="button"
                            className="secondary"
                            aria-expanded={open === d.id}
                            onClick={() => setOpen(open === d.id ? null : d.id)}
                          >
                            {open === d.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            {open === d.id ? "Hide details" : "Details"}
                          </button>
                        )}
                        {d.published && d.kind === "os" && (
                          <button
                            type="button"
                            onClick={() => prepare(d)}
                            disabled={busy !== null}
                            title="New version with the server's agent and the settings every PC needs"
                          >
                            <Wand2 size={14} />
                            {busy === `prepare-${d.id}` ? "Preparing…" : "Prepare image"}
                          </button>
                        )}
                        {!d.published && d.editor_id === null && (
                          <>
                            <select
                              aria-label={`PC to edit ${d.name} on`}
                              value={editOn[d.id] ?? ""}
                              onChange={(e) => setEditOn({ ...editOn, [d.id]: e.target.value })}
                              disabled={busy !== null}
                            >
                              <option value="">PC…</option>
                              {free.map((m) => (
                                <option key={m.id} value={m.id}>
                                  {m.name}
                                </option>
                              ))}
                            </select>
                            <button
                              type="button"
                              onClick={() => startEdit(d)}
                              disabled={busy !== null || !editOn[d.id]}
                            >
                              <Pencil size={14} />
                              {busy === `edit-${d.id}` ? "Starting…" : "Edit on PC"}
                            </button>
                            <button type="button" onClick={() => publish(d)} disabled={busy !== null}>
                              <CheckCircle2 size={14} />
                              {busy === `publish-${d.id}` ? "Publishing…" : "Publish"}
                            </button>
                          </>
                        )}
                        {d.editor_id !== null && (
                          <button
                            type="button"
                            onClick={() => finishEdit(d)}
                            disabled={busy !== null || machine(d.editor_id)?.session_active === true}
                            title={
                              machine(d.editor_id)?.session_active
                                ? `Shut down ${machine(d.editor_id)?.name} first`
                                : undefined
                            }
                          >
                            <CheckCircle2 size={14} />
                            {busy === `finish-${d.id}` ? "Finishing…" : "Finish editing"}
                          </button>
                        )}
                        <button
                          type="button"
                          className="icon-btn"
                          onClick={() => rename(d)}
                          disabled={busy !== null}
                          aria-label={`Rename ${d.name}`}
                          title="Rename"
                        >
                          <Type size={14} />
                        </button>
                        <button
                          type="button"
                          className="icon-btn icon-btn-danger"
                          onClick={() => remove(d)}
                          disabled={busy !== null}
                          aria-label={`Delete ${d.name}`}
                          title={busy === `delete-${d.id}` ? "Deleting…" : "Delete"}
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                    {open === d.id && (
                      <tr>
                        <td colSpan={6}>
                          <DiskDetails disk={d} onChanged={reload} refreshKey={machines} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </>
    );
  }

  return (
    <section>
      <ErrorBanner message={error} onClose={() => setError(null)} />

      <ImageKpis disks={disks} machines={machines} />

      <form className="card form-row" onSubmit={create} aria-label="New image">
        <label>
          Name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. steam-main"
            required
            maxLength={32}
          />
        </label>
        <label>
          Kind
          <select value={kind} onChange={(e) => setKind(e.target.value as DiskKind)}>
            <option value="game">Game disk</option>
            <option value="os">OS image (Boot Mode)</option>
          </select>
        </label>
        <label>
          Size (GB)
          <input
            type="number"
            min={1}
            max={16384}
            value={sizeGb}
            onChange={(e) => setSizeGb(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={busy !== null}>
          <Plus size={14} />
          {busy === "create" ? "Creating…" : "Create"}
        </button>
      </form>

      {section("OS images", Monitor, disks.filter((d) => d.kind === "os"), "No OS images yet.")}
      {section("Game disks", Gamepad2, disks.filter((d) => d.kind !== "os"), "No game disks yet.")}
    </section>
  );
}

function ImageKpis({ disks, machines }: { disks: GameDisk[]; machines: Machine[] }) {
  const os = disks.filter((d) => d.kind === "os");
  const games = disks.filter((d) => d.kind !== "os");
  const drafts = disks.filter((d) => !d.published).length;
  const using = machines.filter((m) => m.game_disk_id !== null || m.os_disk_id !== null).length;
  const totalGb = disks.reduce((sum, d) => sum + d.size_gb, 0);
  const cards = [
    { title: "Images", value: disks.length, sub: `${totalGb} GB in all${drafts ? ` · ${drafts} draft` : ""}`, icon: Layers, tone: "blue" },
    { title: "OS images", value: os.length, sub: "Windows for Boot Mode PCs", icon: Monitor, tone: "purple" },
    { title: "Game disks", value: games.length, sub: "shared D: for every PC", icon: Gamepad2, tone: "green" },
    { title: "In use", value: using, sub: `of ${machines.length} PCs have an image`, icon: HardDrive, tone: "amber" },
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
