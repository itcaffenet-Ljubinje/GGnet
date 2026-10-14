import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { Discovered } from "../api";
import { calls, machine, stubFetch } from "../test/fixtures";
import { useAsyncAction } from "../useAsyncAction";
import { DiscoveredPanel, suggestName } from "./DiscoveredPanel";

function found(over: Partial<Discovered> = {}): Discovered {
  return {
    id: 7,
    mac: "aa:bb:cc:dd:ee:01",
    source: "agent",
    hostname: "DESKTOP-1A2B3C",
    ip_address: "192.168.0.21",
    agent_version: "0.1.9",
    seen_count: 3,
    ignored: false,
    first_seen_at: "2026-10-14T10:00:00Z",
    last_seen_at: "2026-10-14T10:05:00Z",
    ...over,
  };
}

function Panel({ discovered, reload }: { discovered: Discovered[]; reload: () => Promise<void> }) {
  const { busy, run } = useAsyncAction();
  return <DiscoveredPanel discovered={discovered} busy={busy !== null} run={run} reload={reload} />;
}

describe("DiscoveredPanel", () => {
  it("is hidden when nothing was discovered", () => {
    const { container } = render(<Panel discovered={[]} reload={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("adds a PC under the name typed, in Disk Mode when its agent knocked", async () => {
    const fetchMock = stubFetch(201, machine());
    const reload = vi.fn().mockResolvedValue(undefined);
    render(<Panel discovered={[found()]} reload={reload} />);

    const name = screen.getByLabelText("Name for aa:bb:cc:dd:ee:01");
    expect(name).toHaveValue("desktop-1a2b3c");
    await userEvent.clear(name);
    await userEvent.type(name, "vip-05");
    await userEvent.click(screen.getByRole("button", { name: "Add" }));

    expect(calls(fetchMock)).toEqual([
      { url: "/api/v1/discovery/7/claim", method: "POST", body: { name: "vip-05", mode: "disk" } },
    ]);
    expect(reload).toHaveBeenCalled();
  });

  it("suggests Boot Mode for a PC that booted from the network", () => {
    render(<Panel discovered={[found({ source: "pxe", hostname: null })]} reload={vi.fn()} />);
    expect(screen.getByLabelText("Mode for aa:bb:cc:dd:ee:01")).toHaveValue("boot");
    expect(screen.getByRole("button", { name: "Add" })).toBeDisabled();   // no name yet
  });

  it("ignores a PC after confirming", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const fetchMock = stubFetch(200, found({ ignored: true }));
    render(<Panel discovered={[found()]} reload={vi.fn().mockResolvedValue(undefined)} />);
    await userEvent.click(screen.getByRole("button", { name: "Ignore" }));
    expect(calls(fetchMock)).toEqual([{ url: "/api/v1/discovery/7/ignore", method: "POST", body: undefined }]);
  });

  it("makes a valid machine name from a Windows name", () => {
    expect(suggestName("DESKTOP-1A2B3C")).toBe("desktop-1a2b3c");
    expect(suggestName("-My PC_01")).toBe("my-pc-01");
    expect(suggestName("A-VERY-LONG-COMPUTER-NAME")).toHaveLength(15);
    expect(suggestName(null)).toBe("");
  });
});
