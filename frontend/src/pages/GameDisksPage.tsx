import { Fragment, useState, type FormEvent } from "react";

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
      "stays on), PCIe, USB and network card power saving off, a fixed 4 GB page file, and no automatic " +
      "Windows Update, Store updates, maintenance (defragmentation), search index or SysMain.\n\n" +
      "PCs move to it at their next reboot. Apply Writebacks of an OS image does this already.";
    if (!window.confirm(msg)) return;
    await run(`prepare-${disk.id}`, () => api.prepareImage(disk.id));
    await reload();
  }

  async function remove(disk: GameDisk) {
    const what = disk.kind === "os" ? "OS image" : "game disk";
    if (!window.confirm(`Delete ${what} "${disk.name}" and its zvol on the host?`)) return;
    await run(`delete-${disk.id}`, () => api.deleteDisk(disk.id));
    await reload();
  }

  function section(title: string, list: GameDisk[], empty: string) {
    return (
      <>
        <h2 className="section-title">{title}</h2>
        {list.length === 0 ? (
          <p className="empty">{empty}</p>
        ) : (
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
                    <td className="strong">{d.name}</td>
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
                            {busy === `edit-${d.id}` ? "Starting…" : "Edit on PC"}
                          </button>
                          <button type="button" onClick={() => publish(d)} disabled={busy !== null}>
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
                          {busy === `finish-${d.id}` ? "Finishing…" : "Finish editing"}
                        </button>
                      )}
                      <button
                        type="button"
                        className="danger"
                        onClick={() => remove(d)}
                        disabled={busy !== null}
                      >
                        {busy === `delete-${d.id}` ? "Deleting…" : "Delete"}
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
        )}
      </>
    );
  }

  return (
    <section>
      <ErrorBanner message={error} onClose={() => setError(null)} />

      <form className="card form-row" onSubmit={create}>
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
          {busy === "create" ? "Creating…" : "Create"}
        </button>
      </form>

      {section("OS images", disks.filter((d) => d.kind === "os"), "No OS images yet.")}
      {section("Game disks", disks.filter((d) => d.kind !== "os"), "No game disks yet.")}
    </section>
  );
}
