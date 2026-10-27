import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Hardware } from "../api";
import { disk } from "../test/fixtures";
import { HardwarePanel } from "./HardwarePanel";

function stub(body: Hardware) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 200 })));
}

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
        { nic: "VEN_8086&DEV_15B8&SUBSYS_86721043&REV_00", status: "missing", machines: ["new-pc"] },
        { nic: null, status: "unknown", machines: ["server"] },
      ],
    });
    const add = vi.fn();
    render(<HardwarePanel disk={disk({ id: 3, kind: "os", snapshot: "v2" })} onAddHardware={add} />);
    expect(await screen.findByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("Needs Add new hardware")).toBeInTheDocument();
    expect(screen.getByText("Not seen yet")).toBeInTheDocument();
    expect(screen.getByText(/new-pc cannot boot this image yet/)).toBeInTheDocument();
    expect(screen.getByText("vip-01, vip-02")).toBeInTheDocument();
    expect(screen.getByText("\\01000000684CE00000")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Add new hardware/ }));
    expect(add).toHaveBeenCalled();
  });

  it("says when the image could not be checked", async () => {
    stub({ snapshot: "base", problem: "no Windows partition found", nics: [] });
    render(<HardwarePanel disk={disk({ id: 3, kind: "os" })} />);
    expect(await screen.findByText(/could not be checked: no Windows partition found/)).toBeInTheDocument();
  });
});
