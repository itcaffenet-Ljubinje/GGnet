import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { AddHardwareJob, Hardware } from "../api";
import { disk } from "../test/fixtures";
import { HardwarePanel, parsePnpId } from "./HardwarePanel";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

function stub(body: Hardware, job: AddHardwareJob | null = null) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith("/add-hardware") && init?.method === "POST") {
      const cards = JSON.parse(String(init.body)).cards;
      return json({ ...JOB, cards, running: true, step: "vm", snapshot: null }, 202);
    }
    if (url.endsWith("/add-hardware")) return json(job);
    return json(body);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const I219 = "VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10";
const JOB: AddHardwareJob = {
  cards: [{ nic: I219, instance: "3&11583659&0&FE" }],
  step: "done",
  running: false,
  error: null,
  snapshot: "v3",
  devices: [{ instance_id: `PCI\\${I219}\\3&11583659&0&FE`, ok: true, driver: "Intel I219-V" }],
  started: 0,
  finished: 1,
};

describe("HardwarePanel", () => {
  it("lists which PCs the image can boot and names those it cannot", async () => {
    stub({
      snapshot: "v2",
      problem: null,
      nics: [
        {
          nic: "VEN_10EC&DEV_8168&SUBSYS_E0001458&REV_15",
          instance: "01000000684CE00000",
          status: "ready",
          machines: ["vip-01", "vip-02"],
        },
        { nic: "VEN_10EC&DEV_8168&SUBSYS_E0001458&REV_16", status: "added", machines: ["komp-01"] },
        { nic: "VEN_8086&DEV_15B8&SUBSYS_86721043&REV_00", status: "missing", machines: ["new-pc"] },
        { nic: null, status: "unknown", machines: ["server"] },
      ],
    });
    render(<HardwarePanel disk={disk({ id: 3, kind: "os", snapshot: "v2" })} />);
    expect(await screen.findByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("Added at boot")).toBeInTheDocument();
    expect(screen.getByText("No driver")).toBeInTheDocument();
    expect(screen.getByText("Not seen yet")).toBeInTheDocument();
    expect(screen.getByText(/new-pc cannot boot this image/)).toBeInTheDocument();
    expect(screen.getByText("vip-01, vip-02")).toBeInTheDocument();
    expect(screen.getByText("\\01000000684CE00000")).toBeInTheDocument();
  });

  it("says when the image could not be checked", async () => {
    stub({ snapshot: "base", problem: "no Windows partition found", nics: [] });
    render(<HardwarePanel disk={disk({ id: 3, kind: "os" })} />);
    expect(await screen.findByText(/could not be checked: no Windows partition found/)).toBeInTheDocument();
  });

  it("adds a reported card the image has no driver for", async () => {
    const fetchMock = stub({
      snapshot: "v2",
      problem: null,
      nics: [{ nic: I219, instance: "3&11583659&0&FE", status: "missing", machines: ["komp-11"] }],
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<HardwarePanel disk={disk({ id: 3, kind: "os", snapshot: "v2" })} />);
    fireEvent.click(await screen.findByRole("button", { name: /Add new hardware/ }));
    fireEvent.click(screen.getByRole("button", { name: "Install 1 card" }));
    expect(await screen.findByText(/Windows installs the card in a VM/)).toBeInTheDocument();
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({ cards: [{ nic: I219, instance: "3&11583659&0&FE" }] });
  });

  it("shows the last run's outcome", async () => {
    stub({ snapshot: "v3", problem: null, nics: [] }, JOB);
    render(<HardwarePanel disk={disk({ id: 3, kind: "os", snapshot: "v3" })} />);
    await waitFor(() => expect(screen.getByText("Added")).toBeInTheDocument());
    expect(screen.getByText(/Intel I219-V/)).toBeInTheDocument();
  });

  it("reads a card from the PnP device ID the PC shows", () => {
    expect(parsePnpId(`PCI\\${I219}\\3&11583659&0&FE`)).toEqual({ nic: I219, instance: "3&11583659&0&FE" });
    expect(parsePnpId(`pci\\${I219.toLowerCase()}\\3&11583659&0&fe`)?.instance).toBe("3&11583659&0&FE");
    expect(parsePnpId(I219)).toBeNull();
    expect(parsePnpId("PCI\\VEN_8086&DEV_15BC\\3&1")).toBeNull();
  });
});
