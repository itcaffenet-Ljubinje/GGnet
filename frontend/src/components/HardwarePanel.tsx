import { useCallback, useEffect, useState } from "react";
import { Cpu, Plus, X } from "lucide-react";

import { api, type AddHardwareJob, type GameDisk, type Hardware, type HardwareCard, type NicSupport } from "../api";

const STATUS: Record<NicSupport["status"], { badge: string; label: string; text: string }> = {
  ready: { badge: "badge-provisioned", label: "Ready", text: "The image knows this network card." },
  added: {
    badge: "badge-idle",
    label: "Added at boot",
    text:
      "The image knows the chip under another revision, board or instance; ggNet adds the card with the " +
      "PC's own instance ID when the PC boots.",
  },
  missing: {
    badge: "badge-error",
    label: "No driver",
    text: "These PCs cannot boot this image: its Windows has no driver for their network card.",
  },
  unknown: {
    badge: "badge-warn",
    label: "Not seen yet",
    text: "Never booted over the network, so their network card is not known yet.",
  },
};

const STEPS: Record<AddHardwareJob["step"], string> = {
  starting: "Starting…",
  job: "Copying the newest version and writing the job into it…",
  vm: "Windows installs the card in a VM on the server (a few minutes)…",
  result: "Reading what Windows did…",
  prepare: "Preparing the new version for a network boot…",
  apply: "Making it the next version…",
  done: "Done",
};

const POLL_MS = 3000;
const NIC_RE = /^VEN_[0-9A-F]{4}&DEV_[0-9A-F]{4}&SUBSYS_[0-9A-F]{8}&REV_[0-9A-F]{2}$/;
const INSTANCE_RE = /^[A-Za-z0-9&_.-]{1,64}$/;

/**
 * A card from what the PC reports, e.g. Get-NetAdapter's PnPDeviceID
 * PCI\VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10\3&11583659&0&FE.
 */
export function parsePnpId(text: string): HardwareCard | null {
  const parts = text.trim().toUpperCase().replace(/^PCI\\/, "").split("\\");
  if (parts.length !== 2 || !NIC_RE.test(parts[0]) || !INSTANCE_RE.test(parts[1])) return null;
  return { nic: parts[0], instance: parts[1] };
}

interface Props {
  disk: GameDisk;
  /** After a new version was made: reload the image. */
  onChanged?: () => Promise<void>;
}

/** Which PCs an OS image's active version can boot, by their boot network card; Add new hardware. */
export function HardwarePanel({ disk, onChanged }: Props) {
  const [hardware, setHardware] = useState<Hardware | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<AddHardwareJob | null>(null);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    let current = true;
    setHardware(null);
    api
      .getHardware(disk.id)
      .then((h) => current && setHardware(h))
      .catch((e) => current && setError(e instanceof Error ? e.message : String(e)));
    api
      .getAddHardware(disk.id)
      .then((j) => current && setJob(j))
      .catch(() => undefined);
    return () => {
      current = false;
    };
  }, [disk.id, disk.snapshot]);

  // Follow a running job until it ends.
  const running = job?.running ?? false;
  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(async () => {
      try {
        const j = await api.getAddHardware(disk.id);
        setJob(j);
        if (j && !j.running && j.snapshot && onChanged) await onChanged();
      } catch {
        // keep polling
      }
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [running, disk.id, onChanged]);

  const missing = hardware?.nics.filter((n) => n.status === "missing").flatMap((n) => n.machines) ?? [];
  return (
    <div className="card" aria-label="Hardware">
      <h3 className="card-title title-with-icon">
        <Cpu size={16} aria-hidden />
        Hardware
        {hardware?.snapshot && <span className="muted small">@{hardware.snapshot}</span>}
        {!adding && !running && (
          <button type="button" className="secondary card-title-action" onClick={() => setAdding(true)}>
            <Plus size={14} />
            Add new hardware
          </button>
        )}
      </h3>
      {job && <JobStatus job={job} diskId={disk.id} onJob={setJob} />}
      {adding && hardware && (
        <AddHardwareForm
          diskId={disk.id}
          nics={hardware.nics}
          onStarted={(j) => {
            setJob(j);
            setAdding(false);
          }}
          onClose={() => setAdding(false)}
        />
      )}
      {error ? (
        <p className="error-text small">{error}</p>
      ) : hardware === null ? (
        <p className="muted small">Checking which network cards the image knows…</p>
      ) : hardware.problem ? (
        <p className="warn-text small">The image could not be checked: {hardware.problem}</p>
      ) : hardware.nics.length === 0 ? (
        <p className="muted small">No PCs registered yet.</p>
      ) : (
        <>
          {missing.length > 0 && (
            <p className="error-text small">
              {missing.join(", ")} cannot boot this image: add their network card first (Add new hardware).
            </p>
          )}
          <ul className="nic-list">
            {hardware.nics.map((n) => (
              <li key={`${n.nic ?? "unknown"}\\${n.instance ?? ""}`}>
                <span className={`badge ${STATUS[n.status].badge}`} title={STATUS[n.status].text}>
                  {STATUS[n.status].label}
                </span>
                <span className="mono small" title={n.instance ? `Instance ${n.instance}` : "Instance not reported yet"}>
                  {n.nic ?? "network card not known"}
                  {n.instance && <span className="muted">\{n.instance}</span>}
                </span>
                <span className="small">{n.machines.join(", ")}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function JobStatus({
  job,
  diskId,
  onJob,
}: {
  job: AddHardwareJob;
  diskId: number;
  onJob: (j: AddHardwareJob | null) => void;
}) {
  const [cancelling, setCancelling] = useState(false);
  const cards = job.cards.map((c) => c.nic).join(", ");
  async function cancel() {
    setCancelling(true);
    try {
      onJob(await api.cancelAddHardware(diskId));
    } catch {
      // it ended meanwhile
    }
    setCancelling(false);
  }
  if (job.running) {
    return (
      <div className="hw-job" role="status">
        <p className="small">
          <span className="badge badge-editing">Add new hardware</span> {STEPS[job.step]}
        </p>
        <p className="muted small mono">{cards}</p>
        <button type="button" className="secondary" onClick={cancel} disabled={cancelling}>
          {cancelling ? "Cancelling…" : "Cancel"}
        </button>
      </div>
    );
  }
  if (job.error) {
    return (
      <p className="error-text small" role="status">
        Add new hardware ({cards}) failed: {job.error}
      </p>
    );
  }
  const drivers = job.devices.map((d) => d.driver).filter(Boolean).join(", ");
  return (
    <p className="small" role="status">
      <span className="badge badge-provisioned">Added</span> {cards} in @{job.snapshot}
      {drivers && <span className="muted"> ({drivers})</span>}. PCs move to it at their next boot.
    </p>
  );
}

function AddHardwareForm({
  diskId,
  nics,
  onStarted,
  onClose,
}: {
  diskId: number;
  nics: NicSupport[];
  onStarted: (job: AddHardwareJob) => void;
  onClose: () => void;
}) {
  // Cards the PCs reported that the image does not have under their own instance.
  const reported = nics.filter(
    (n): n is NicSupport & { nic: string; instance: string } =>
      n.nic !== null && !!n.instance && (n.status === "missing" || n.status === "added"),
  );
  const [chosen, setChosen] = useState<Set<string>>(
    new Set(reported.filter((n) => n.status === "missing").map((n) => `${n.nic}\\${n.instance}`)),
  );
  const [manual, setManual] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = useCallback(
    (key: string) => {
      const next = new Set(chosen);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      setChosen(next);
    },
    [chosen],
  );

  const typed = manual.trim() ? parsePnpId(manual) : null;
  const cards: HardwareCard[] = [
    ...reported.filter((n) => chosen.has(`${n.nic}\\${n.instance}`)).map((n) => ({ nic: n.nic, instance: n.instance })),
    ...(typed ? [typed] : []),
  ];

  async function start() {
    const msg =
      `Install ${cards.map((c) => c.nic).join(", ")} into a new version of this image?\n\n` +
      "The newest version is copied and booted in a temporary VM on the server, where Windows installs the " +
      "card's driver; it then becomes the active version. PCs keep using the current version meanwhile.";
    if (!window.confirm(msg)) return;
    setBusy(true);
    setError(null);
    try {
      onStarted(await api.addHardware(diskId, cards));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    setBusy(false);
  }

  return (
    <div className="hw-add" aria-label="Add new hardware">
      <div className="hw-add-head">
        <span className="strong">Add new hardware</span>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
          <X size={16} />
        </button>
      </div>
      <p className="muted small">
        Windows in the image installs the PC&apos;s network card under the card&apos;s own instance ID, so the PC
        boots it over the network.
      </p>
      {reported.length > 0 && (
        <ul className="nic-list">
          {reported.map((n) => {
            const key = `${n.nic}\\${n.instance}`;
            return (
              <li key={key}>
                <label className="check">
                  <input type="checkbox" checked={chosen.has(key)} onChange={() => toggle(key)} />
                  <span className="mono small">
                    {n.nic}
                    <span className="muted">\{n.instance}</span>
                  </span>
                </label>
                <span className="small">{n.machines.join(", ")}</span>
              </li>
            );
          })}
        </ul>
      )}
      <label className="small">
        Another card (its PnP device ID, from the PC: <span className="mono">Get-NetAdapter -Physical | fl PnPDeviceID</span>)
        <input
          className="mono"
          value={manual}
          onChange={(e) => setManual(e.target.value)}
          placeholder="PCI\VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10\3&11583659&0&FE"
          aria-label="PnP device ID"
        />
      </label>
      {manual.trim() && !typed && <p className="warn-text small">Not a PCI device ID with its instance.</p>}
      {error && <p className="error-text small">{error}</p>}
      <div className="hw-add-actions">
        <button type="button" className="btn-primary" onClick={start} disabled={busy || cards.length === 0}>
          {busy ? "Starting…" : cards.length === 1 ? "Install 1 card" : `Install ${cards.length} cards`}
        </button>
      </div>
    </div>
  );
}
