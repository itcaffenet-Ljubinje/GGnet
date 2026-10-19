// Typed client for the ggNet backend API (/api/v1).

export interface Health {
  status: string;
  version: string;
  pool: string;
  server_ip: string;
}

export interface GameDisk {
  id: number;
  name: string;
  zvol_path: string;
  size_gb: number;
  snapshot: string | null;
  published: boolean;
  editor_id: number | null;
  created_at: string;
  /** "os": a Boot Mode Windows image; "game": a game disk. Older servers send none (game). */
  kind?: DiskKind;
}

export type DiskKind = "game" | "os";

/** Which kept writebacks Apply Writebacks turns into versions (Boot Mode has two). */
export interface ApplyChoice {
  os?: boolean;
  game?: boolean;
  /** Set on every version Apply Writebacks makes. */
  comment?: string;
}

/** One version of a game disk (a ZFS snapshot of its master). */
export interface Snapshot {
  name: string;
  created_at: string;
  used_bytes: number;
  referenced_bytes: number;
  active: boolean;
  machines: string[];
  pinned: string[];
  /** Who, when, what changed; null when unset. */
  comment?: string | null;
}

/** A PC's writeback (clone) of a game disk. */
export interface Writeback {
  machine_id: number | null;
  machine_name: string;
  zvol: string;
  snapshot: string;
  used_bytes: number;
  keep_writeback: boolean;
  pinned_snapshot: string | null;
  session_active: boolean | null;
  outdated: boolean;
}

/** Automated snapshot and writeback removal (Settings → Retention). */
export interface RetentionSettings {
  enabled: boolean;
  dry_run: boolean;
  reserved_percent: number;
  warning_percent: number;
  unused_snapshot_days: number;
  keep_newest_snapshots: number;
  inactive_writeback_hours: number;
}

export interface RetentionAction {
  kind: "snapshot" | "writeback" | "error";
  target: string;
  reason: string;
  done: boolean;
  error: string | null;
}

export interface RetentionReport {
  at: string;
  dry_run: boolean;
  actions: RetentionAction[];
}

export interface Retention extends RetentionSettings {
  saved: boolean;
  last_run: RetentionReport | null;
}

/** Settings → Network boot: what iPXE gets; config.toml's until saved. */
export interface BootSettings {
  /** "none" (0.0.0.0), "dhcp" (the router's) or an IPv4 address. */
  gateway: string;
  unregistered: "wait" | "local";
}

export interface BootSettingsOut extends BootSettings {
  saved: boolean;
}

export interface SecureBootKey {
  subject: string;
  /** SHA-256, as MokManager shows it. */
  fingerprint: string;
  expires: string | null;
  /** Whether sb/grubx64.efi is signed with this key; null: not there. */
  ipxe_signed: boolean | null;
}

/** The PXE service (proxyDHCP + TFTP) as systemd sees it. */
export interface PxeStatus {
  unit: string;
  installed: boolean;
  state: string;
  sub_state: string;
  since: string | null;
  tftp_root: string;
  files: Record<string, boolean>;
  /** The ggNet Secure Boot key the PCs enroll; null until the installer made it. */
  secure_boot?: SecureBootKey | null;
}

export interface Storage {
  pool: string;
  total_bytes: number;
  used_bytes: number;
  available_bytes: number;
  used_percent: number;
  reserved_bytes: number;
  warning_percent: number;
  warning: boolean;
}

/** Hardware the agent reports (ggRock's Hardware tab). */
export interface MachineHardware {
  nic: string | null;
  cpu: string | null;
  gpus: string[];
  motherboard: string | null;
  memory_bytes: number | null;
  /** Windows booted with Secure Boot on; null or missing: unknown (not UEFI, or an older agent). */
  secure_boot?: boolean | null;
}

/** iSCSI traffic of a mapped machine since its writeback was last cloned. */
export interface MachineTraffic {
  machine_id: number;
  sent_bytes: number;
  received_bytes: number;
  sent_bps: number | null;
  received_bps: number | null;
}

/** Settings → Client app: the ggnet-agent package on the server. */
export interface AgentPackage {
  available: boolean;
  directory: string;
  version: string | null;
  server_url: string;
  install_command: string;
  files: { name: string; size_bytes: number; sha256: string }[];
}

export type BulkKind = "on" | "shutdown" | "reboot" | "assign" | "pin" | "drive_letter" | "stop_keep_writeback";

/** What happened to one machine in a bulk operation. */
export interface BulkResult {
  machine_id: number;
  name: string | null;
  ok: boolean;
  error: string | null;
}

export type MachineMode = "disk" | "boot";
export type MachineStatus = "idle" | "provisioned" | "editing" | "error";

export interface Machine {
  id: number;
  name: string;
  mode: MachineMode;
  initiator_iqn: string;
  mac: string | null;
  game_disk_id: number | null;
  os_disk_id?: number | null;      // Boot Mode: the OS image
  os_clone_snapshot?: string | null; // Boot Mode: the OS image version the PC runs
  editing_disk_id: number | null;
  drive_letter: string;
  reported_drive_letter: string | null;
  pinned_snapshot: string | null;
  pending_command: "shutdown" | "reboot" | null;
  reported_ip: string | null;
  reported_mac: string | null;
  link_speed_mbps: number | null;
  hardware: MachineHardware | null;
  /** Boot Mode: the boot network card's PCI ID as iPXE read it (VEN_10EC&DEV_8168&SUBSYS_…&REV_16). */
  boot_nic?: string | null;
  status: MachineStatus;
  last_error: string | null;
  clone_zvol: string | null;
  clone_snapshot: string | null;
  iscsi_target_iqn: string | null;
  outdated: boolean;
  last_seen_at: string | null;
  agent_version: string | null;
  reported_iqn: string | null;
  iscsi_connected: boolean | null;
  agent_stopped: boolean;
  keep_writeback: boolean;
  writeback_dirty: boolean;
  session_active: boolean | null;
  session_changed_at: string | null;
  booted_at: string | null;
  created_at: string;
  updated_at: string;
}

/** A PC that knocked (iPXE or its agent) but is not registered yet. */
export interface Discovered {
  id: number;
  mac: string;
  source: "pxe" | "agent";
  hostname: string | null;
  ip_address: string | null;
  agent_version: string | null;
  boot_nic?: string | null;
  seen_count: number;
  ignored: boolean;
  first_seen_at: string;
  last_seen_at: string;
}

export interface DiscoveryClaim {
  name: string;
  mode?: MachineMode;
  game_disk_id?: number | null;
  os_disk_id?: number | null;     // Boot Mode: the OS image
}

export interface MachineCreate {
  name: string;
  mode?: MachineMode;
  /** Identifies the PC; the server derives the initiator IQN from it. */
  mac?: string | null;
  game_disk_id?: number | null;
  os_disk_id?: number | null;     // Boot Mode: the OS image
  drive_letter?: string;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Turn a FastAPI error body into one readable message. */
export function errorMessage(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (detail && typeof detail === "object" && "error" in detail) {
    return String((detail as { error: unknown }).error);
  }
  if (Array.isArray(detail)) {
    // 422 validation errors: [{loc: [...], msg: "..."}]
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => {
        const field = (d.loc ?? []).filter((p) => p !== "body").join(".");
        const msg = (d.msg ?? "invalid value").replace(/^Value error, /, "");
        return field ? `${field}: ${msg}` : msg;
      })
      .join("; ");
  }
  if (typeof detail === "string") return detail;
  return `Request failed (HTTP ${status})`;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 204) return undefined as T;
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    // Non-JSON body (e.g. a proxy error page).
  }
  if (!res.ok) throw new ApiError(res.status, errorMessage(res.status, data));
  return data as T;
}

export const api = {
  health: () => request<Health>("GET", "/health"),

  listDisks: () => request<GameDisk[]>("GET", "/v1/game-disks"),
  createDisk: (name: string, size_gb: number, kind: DiskKind = "game") =>
    request<GameDisk>("POST", "/v1/game-disks", { name, size_gb, kind }),
  publishDisk: (id: number) => request<GameDisk>("POST", `/v1/game-disks/${id}/publish`),
  startEdit: (id: number, machine_id: number) =>
    request<GameDisk>("POST", `/v1/game-disks/${id}/edit`, { machine_id }),
  finishEdit: (id: number) => request<GameDisk>("POST", `/v1/game-disks/${id}/finish-edit`),
  deleteDisk: (id: number) => request<void>("DELETE", `/v1/game-disks/${id}`),
  listSnapshots: (id: number) => request<Snapshot[]>("GET", `/v1/game-disks/${id}/snapshots`),
  setActiveSnapshot: (id: number, snapshot: string) =>
    request<GameDisk>("PUT", `/v1/game-disks/${id}/active-snapshot`, { snapshot }),
  deleteSnapshot: (id: number, name: string) =>
    request<void>("DELETE", `/v1/game-disks/${id}/snapshots/${encodeURIComponent(name)}`),
  setSnapshotComment: (id: number, name: string, comment: string) =>
    request<Snapshot>("PUT", `/v1/game-disks/${id}/snapshots/${encodeURIComponent(name)}/comment`, { comment }),
  mergeIntoBase: (id: number, name: string) =>
    request<GameDisk>("POST", `/v1/game-disks/${id}/snapshots/${encodeURIComponent(name)}/merge-into-base`),
  listWritebacks: (id: number) => request<Writeback[]>("GET", `/v1/game-disks/${id}/writebacks`),

  getAgentPackage: () => request<AgentPackage>("GET", "/v1/agent/package"),
  getStorage: () => request<Storage>("GET", "/v1/storage"),
  getRetention: () => request<Retention>("GET", "/v1/settings/retention"),
  getBootSettings: () => request<BootSettingsOut>("GET", "/v1/settings/boot"),
  saveBootSettings: (body: BootSettings) => request<BootSettingsOut>("PUT", "/v1/settings/boot", body),
  getPxe: () => request<PxeStatus>("GET", "/v1/pxe"),
  restartPxe: () => request<PxeStatus>("POST", "/v1/pxe/restart"),
  saveRetention: (body: RetentionSettings) => request<Retention>("PUT", "/v1/settings/retention", body),
  previewRetention: (body: RetentionSettings) =>
    request<RetentionAction[]>("POST", "/v1/settings/retention/preview", body),
  runRetention: () => request<RetentionReport>("POST", "/v1/settings/retention/run"),

  machineTraffic: () => request<MachineTraffic[]>("GET", "/v1/machines/traffic"),
  listMachines: () => request<Machine[]>("GET", "/v1/machines"),
  createMachine: (body: MachineCreate) => request<Machine>("POST", "/v1/machines", body),
  updateMachine: (id: number, body: Partial<MachineCreate>) =>
    request<Machine>("PATCH", `/v1/machines/${id}`, body),
  /** Game disk, and in Boot Mode the OS image (not sent keeps the current one). */
  assignDisk: (id: number, game_disk_id: number | null, os_disk_id?: number | null) =>
    request<Machine>(
      "POST",
      `/v1/machines/${id}/assign`,
      os_disk_id === undefined ? { game_disk_id } : { game_disk_id, os_disk_id },
    ),
  setDriveLetterAll: (drive_letter: string) =>
    request<Machine[]>("PUT", "/v1/machines/drive-letter", { drive_letter }),
  setKeepWriteback: (id: number, enabled: boolean) =>
    request<Machine>("PUT", `/v1/machines/${id}/keep-writeback`, { enabled }),
  applyWritebacks: (id: number, choice?: ApplyChoice) =>
    request<Machine>("POST", `/v1/machines/${id}/apply-writebacks`, choice),
  pinSnapshot: (id: number, snapshot: string | null) =>
    request<Machine>("PUT", `/v1/machines/${id}/pin`, { snapshot }),
  bulk: (
    machine_ids: number[],
    action: BulkKind,
    extra: { game_disk_id?: number | null; snapshot?: string | null; drive_letter?: string } = {},
  ) => request<BulkResult[]>("POST", "/v1/machines/bulk", { machine_ids, action, ...extra }),
  power: (id: number, action: "on" | "shutdown" | "reboot") =>
    request<Machine>("POST", `/v1/machines/${id}/power`, { action }),
  discardWriteback: (id: number) => request<Machine>("POST", `/v1/machines/${id}/discard-writeback`),
  deleteMachine: (id: number) => request<void>("DELETE", `/v1/machines/${id}`),

  listDiscovered: () => request<Discovered[]>("GET", "/v1/discovery"),
  claimDiscovered: (id: number, body: DiscoveryClaim) =>
    request<Machine>("POST", `/v1/discovery/${id}/claim`, body),
  ignoreDiscovered: (id: number) => request<Discovered>("POST", `/v1/discovery/${id}/ignore`),
};
