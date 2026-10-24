const UNITS = ["B", "KB", "MB", "GB", "TB"];

/** 1536 → "1.5 KB" (binary units, as ZFS reports them). */
export function formatBytes(bytes: number): string {
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < UNITS.length - 1) {
    value /= 1024;
    unit++;
  }
  return `${unit === 0 ? value : value.toFixed(value < 10 ? 2 : 1)} ${UNITS[unit]}`;
}

/** 1000 → "1 Gbit/s", 100 → "100 Mbit/s", 2500 → "2.5 Gbit/s". */
export function formatLink(mbps: number): string {
  return mbps >= 1000 ? `${Number((mbps / 1000).toFixed(1))} Gbit/s` : `${mbps} Mbit/s`;
}

/** Milliseconds → "12 min", "2 h 5 min", "3 d 4 h". */
export function formatDuration(ms: number): string {
  const min = Math.max(0, Math.floor(ms / 60_000));
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} h ${min % 60} min`;
  return `${Math.floor(h / 24)} d ${h % 24} h`;
}

/** Links below 1 Gbit/s are flagged ("Connectivity issue"). */
export const SLOW_LINK_MBPS = 1000;

/** Bytes per second → "12.0 MB/s". */
export function formatRate(bps: number): string {
  return `${formatBytes(Math.round(bps))}/s`;
}

const NIC_VENDORS: Record<string, string> = { "10EC": "Realtek", "8086": "Intel", "14E4": "Broadcom", "1969": "Atheros", "1D6A": "Aquantia" };

/** "Realtek 8168 rev 16" from a PCI hardware ID (VEN_10EC&DEV_8168&SUBSYS_E0001458&REV_16). */
export function formatNic(id: string): string {
  const m = /^VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})&SUBSYS_[0-9A-F]{8}&REV_([0-9A-F]{2})$/.exec(id);
  if (!m) return id;
  return `${NIC_VENDORS[m[1]] ?? `Vendor ${m[1]}`} ${m[2]} rev ${m[3]}`;
}
