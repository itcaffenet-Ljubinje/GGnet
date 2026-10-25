import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PoolDisk, ServerStatus, User } from "../api";
import { calls } from "../test/fixtures";
import { ServerPage, diskProblems, recommendedCacheGb } from "./ServerPage";

const GB = 2 ** 30;
const STAFF: User = { id: 2, username: "ana", role: "staff", disabled: false, created_at: "2026-10-19T00:00:00Z", last_login_at: null };
const recent = new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString();
const old = new Date(Date.now() - 115 * 24 * 3600 * 1000).toISOString();

function disk(name: string, overrides: Partial<PoolDisk> = {}): PoolDisk {
  return {
    name,
    group: "mirror-0",
    state: "ONLINE",
    read_errors: 0,
    write_errors: 0,
    checksum_errors: 0,
    trim_state: "COMPLETE",
    trim_percent: null,
    trim_time: old,
    trim_supported: true,
    smart_passed: true,
    model: "TOSHIBA 5SRB384C",
    serial: `SN-${name}`,
    capacity_bytes: 3840 * GB,
    temperature: 32,
    wear_percent: 35,
    power_on_hours: 72361,
    ...overrides,
  };
}

function status(overrides: Partial<ServerStatus> = {}): ServerStatus {
  return {
    pool: {
      name: "STORAGE-01",
      state: "ONLINE",
      size_bytes: 10000 * GB,
      allocated_bytes: 3400 * GB,
      free_bytes: 6600 * GB,
      fragmentation: 22,
      capacity: 34,
      errors: 0,
      scan: { function: "scrub", state: "finished", start_time: recent, end_time: recent, errors: 0, percent: null, paused: false },
      last_trim: old,
      autotrim: false,
      groups: [{ name: "mirror-0", type: "mirror", state: "ONLINE", disks: ["a1", "a2"] }],
      disks: [disk("a1"), disk("a2", { temperature: 64, checksum_errors: 2 })],
    },
    arc: { size_bytes: 64 * GB, max_bytes: 64 * GB, min_bytes: 6 * GB, hit_percent: 95.2 },
    memory: { total_bytes: 188 * GB, available_bytes: 99 * GB },
    writebacks_bytes: 2 * GB,
    writebacks_count: 26,
    smart_read_at: recent,
    ...overrides,
  };
}

function stub(s: ServerStatus) {
  const mock = vi.fn().mockImplementation(async () => new Response(JSON.stringify(s), { status: 200 }));
  vi.stubGlobal("fetch", mock);
  return mock;
}

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
});

const openSection = (name: RegExp) => userEvent.click(screen.getByRole("tab", { name }));

describe("ServerPage", () => {
  it("shows the pool, the RAM cache and the writebacks", async () => {
    stub(status());
    render(<ServerPage />);
    expect(await screen.findByText("Pool STORAGE-01")).toBeInTheDocument();
    expect(screen.getByText("95.2% of reads from RAM")).toBeInTheDocument();
    expect(screen.getByText("26 writebacks of all PCs")).toBeInTheDocument();
    expect(screen.getByText(/fragmentation 22%/)).toBeInTheDocument();
    expect(screen.getByText(/no errors/)).toBeInTheDocument();
  });

  it("warns about an old TRIM and a disk that needs a look", async () => {
    stub(status());
    render(<ServerPage />);
    expect(await screen.findByText(/skips pools that are not all NVMe: start it here/)).toBeInTheDocument();
    expect(screen.getByText("2 disks, 1 need a look")).toBeInTheDocument();
    await openSection(/Disks/);
    const row = screen.getByText("SN-a2", { exact: false }).closest("tr")!;
    expect(row).toHaveClass("row-warn");
    expect(within(row).getByText("0/0/2")).toBeInTheDocument();
  });

  it("starts a scrub after asking; staff cannot", async () => {
    const mock = stub(status());
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const { unmount } = render(<ServerPage />);
    await userEvent.click(await screen.findByRole("button", { name: /Start scrub/ }));
    expect(calls(mock).filter((c) => c.method === "POST")).toEqual([
      { url: "/api/v1/server/scrub", method: "POST", body: { action: "start" } },
    ]);
    unmount();
    render(<ServerPage user={STAFF} />);
    expect(await screen.findByText("Pool STORAGE-01")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /scrub/ })).toBeNull();
  });

  it("reads SMART only on request, and starts or stops a TRIM", async () => {
    const s = status({ smart_read_at: null });
    s.pool!.disks[0] = disk("a1", { trim_state: "ACTIVE", trim_percent: 40 });
    s.pool!.disks[1] = disk("a2", { trim_state: "ACTIVE", trim_percent: 60 });
    const mock = stub(s);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<ServerPage />);
    expect(await screen.findByText("Running: 50%")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Stop TRIM/ }));
    await openSection(/Disks/);
    expect(screen.getByText(/SMART not read yet/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Read SMART/ }));
    expect(calls(mock).filter((c) => c.method === "POST")).toEqual([
      { url: "/api/v1/server/trim", method: "POST", body: { action: "stop" } },
      { url: "/api/v1/server/smart", method: "POST", body: undefined },
    ]);
  });

  it("with autotrim on, an old full TRIM is no warning", async () => {
    const s = status();
    s.pool!.autotrim = true;
    stub(s);
    render(<ServerPage />);
    expect(await screen.findByText(/Autotrim on/)).toBeInTheDocument();
    expect(screen.queryByText(/skips pools that are not all NVMe/)).toBeNull();
  });

  it("says when the pool cannot be read", async () => {
    stub(status({ pool: null }));
    render(<ServerPage />);
    expect(await screen.findByText("The ZFS pool could not be read.")).toBeInTheDocument();
  });

  it("shows one section at a time and remembers the last one", async () => {
    stub(status());
    const { unmount } = render(<ServerPage />);
    expect(await screen.findByText("Pool STORAGE-01")).toBeInTheDocument();
    expect(screen.queryByText(/SMART not read yet|SMART read/)).toBeNull();
    await openSection(/RAM cache/);
    expect(screen.getByRole("tab", { name: /RAM cache/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByText("Pool STORAGE-01")).toBeNull();
    unmount();
    render(<ServerPage />);
    expect(await screen.findByRole("tab", { name: /RAM cache/ })).toHaveAttribute("aria-selected", "true");
  });

  it("sets the RAM cache maximum after asking; staff cannot", async () => {
    const s = status();
    s.arc = { ...s.arc!, allowed_min_bytes: 6 * 1024 ** 3, allowed_max_bytes: 141 * 1024 ** 3 };
    const mock = stub(s);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const { unmount } = render(<ServerPage pcs={17} />);
    await screen.findByText("Pool STORAGE-01");
    await openSection(/RAM cache/);
    expect(screen.getByText(/For 17 PCs about 32 GB is enough/)).toBeInTheDocument();
    const input = screen.getByLabelText("Maximum (GB)");
    await userEvent.clear(input);
    await userEvent.type(input, "48");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(calls(mock).filter((c) => c.method === "PUT")).toEqual([
      { url: "/api/v1/server/arc", method: "PUT", body: { max_gb: 48 } },
    ]);
    unmount();
    render(<ServerPage user={STAFF} />);
    await screen.findByText(/of reads served from RAM/);
    expect(screen.queryByLabelText("Maximum (GB)")).toBeNull();
  });

  it("recommends the RAM cache by the number of PCs", () => {
    expect([10, 20, 40, 100, 150, 250].map(recommendedCacheGb)).toEqual([32, 32, 64, 128, 256, 384]);
  });

  it("lists a disk's problems", () => {
    expect(diskProblems(disk("x"))).toEqual([]);
    expect(diskProblems(disk("x", { state: "FAULTED", smart_passed: false, wear_percent: 91 }))).toEqual([
      "FAULTED",
      "SMART failed",
      "91% worn",
    ]);
  });
});
