import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Maintenance } from "../api";
import { calls } from "../test/fixtures";
import { MaintenanceSchedule } from "./MaintenanceSchedule";

const OFF: Maintenance = {
  enabled: false,
  weekday: 6,
  start: "03:00",
  end: "07:00",
  trim: true,
  scrub: true,
  order: "trim_first",
  next_window: null,
  last_run: null,
};

function stub(m: Maintenance) {
  const mock = vi.fn().mockImplementation(async (_url: string, init?: RequestInit) => {
    const body = init?.method === "PUT" ? { ...JSON.parse(init.body as string), next_window: "2026-10-25T02:00:00", last_run: null } : m;
    return new Response(JSON.stringify(body), { status: 200 });
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

afterEach(() => vi.restoreAllMocks());

describe("MaintenanceSchedule", () => {
  it("saves a weekly window with scrub first", async () => {
    const mock = stub(OFF);
    render(<MaintenanceSchedule admin />);
    expect(await screen.findByText(/Off: nothing runs on its own/)).toBeInTheDocument();
    await userEvent.click(screen.getByLabelText("Run TRIM and scrub on a schedule"));
    await userEvent.selectOptions(screen.getByLabelText("Order"), "scrub_first");
    expect(screen.getByText(/Every Sunday 03:00–07:00: scrub, then TRIM\./)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Save schedule/ }));
    expect(calls(mock).filter((c) => c.method === "PUT")).toEqual([
      {
        url: "/api/v1/server/schedule",
        method: "PUT",
        body: { enabled: true, weekday: 6, start: "03:00", end: "07:00", trim: true, scrub: true, order: "scrub_first" },
      },
    ]);
    expect(await screen.findByRole("button", { name: /Saved/ })).toBeInTheDocument();
  });

  it("shows the last window; staff only look", async () => {
    stub({
      ...OFF,
      enabled: true,
      last_run: {
        window_start: "2026-10-18T03:00:00",
        window_end: "2026-10-18T07:00:00",
        closed: true,
        steps: [
          { name: "trim", status: "done", started_at: null, finished_at: null, error: null },
          { name: "scrub", status: "paused", started_at: null, finished_at: null, error: null },
        ],
      },
    });
    render(<MaintenanceSchedule admin={false} />);
    expect(await screen.findByText(/TRIM done, scrub paused at the end of the window/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Save/ })).toBeNull();
    expect(screen.getByLabelText("Run TRIM and scrub on a schedule")).toBeDisabled();
  });
});
