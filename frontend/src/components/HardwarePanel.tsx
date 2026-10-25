import { useEffect, useState } from "react";
import { Cpu } from "lucide-react";

import { api, type GameDisk, type Hardware, type NicSupport } from "../api";

const STATUS: Record<NicSupport["status"], { badge: string; label: string; text: string }> = {
  ready: { badge: "badge-provisioned", label: "Ready", text: "The image knows this network card." },
  added: {
    badge: "badge-idle",
    label: "Added at boot",
    text: "The image knows the chip under another revision or board; ggNet adds the card when the PC boots.",
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

/** Which PCs an OS image's active version can boot, by their boot network card. */
export function HardwarePanel({ disk }: { disk: GameDisk }) {
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
              {missing.join(", ")} cannot boot this image: add their network card first (Add new hardware).
            </p>
          )}
          <ul className="nic-list">
            {hardware.nics.map((n) => (
              <li key={n.nic ?? "unknown"}>
                <span className={`badge ${STATUS[n.status].badge}`} title={STATUS[n.status].text}>
                  {STATUS[n.status].label}
                </span>
                <span className="mono small">{n.nic ?? "network card not known"}</span>
                <span className="small">{n.machines.join(", ")}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
