import { useEffect, useState } from "react";
import { Cpu, Plus } from "lucide-react";

import { api, type GameDisk, type Hardware, type NicSupport } from "../api";

const STATUS: Record<NicSupport["status"], { badge: string; label: string; text: string }> = {
  ready: { badge: "badge-provisioned", label: "Ready", text: "The image knows this network card." },
  added: {
    badge: "badge-idle",
    label: "Added at boot",
    text:
      "Old way ([boot] legacy_nic_patch): the image knows the chip on another board, and ggNet copies the card " +
      "into the PC's writeback at every boot. Run Add new hardware to put it in the image.",
  },
  missing: {
    badge: "badge-error",
    label: "Needs Add new hardware",
    text: "These PCs cannot boot this image: their board's network card is not in it yet.",
  },
  unknown: {
    badge: "badge-warn",
    label: "Not seen yet",
    text: "Never booted over the network, so their network card is not known yet.",
  },
};

interface Props {
  disk: GameDisk;
  /** Open the Add new hardware wizard. */
  onAddHardware?: () => void;
}

/** Which PCs an OS image's active version can boot, by their boot network card. */
export function HardwarePanel({ disk, onAddHardware }: Props) {
  const [hardware, setHardware] = useState<Hardware | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    setHardware(null);
    api
      .getHardware(disk.id)
      .then((h) => current && setHardware(h))
      .catch((e) => current && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      current = false;
    };
  }, [disk.id, disk.snapshot]);

  const missing = hardware?.nics.filter((n) => n.status === "missing").flatMap((n) => n.machines) ?? [];
  return (
    <div className="card" aria-label="Hardware">
      <h3 className="card-title title-with-icon">
        <Cpu size={16} aria-hidden />
        Hardware
        {hardware?.snapshot && <span className="muted small">@{hardware.snapshot}</span>}
        {onAddHardware && (
          <button type="button" className="secondary card-title-action" onClick={onAddHardware}>
            <Plus size={14} />
            Add new hardware
          </button>
        )}
      </h3>
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
              {missing.join(", ")} cannot boot this image yet: run Add new hardware once for their board.
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
