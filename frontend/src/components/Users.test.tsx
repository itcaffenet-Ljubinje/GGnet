import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { User } from "../api";
import { calls } from "../test/fixtures";
import { AccountCard, ActivityCard, UsersCard } from "./Users";

const user = (over: Partial<User>): User => ({
  id: 1,
  username: "owner",
  role: "admin",
  disabled: false,
  created_at: "2026-10-19T10:00:00Z",
  last_login_at: null,
  ...over,
});
const OWNER = user({});
const ANA = user({ id: 2, username: "ana", role: "staff" });

function stubUsers(list: User[] = [OWNER, ANA]) {
  const mock = vi.fn().mockImplementation(async (_url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    const body = method === "GET" ? list : method === "DELETE" ? null : ANA;
    return method === "DELETE" ? new Response(null, { status: 204 }) : new Response(JSON.stringify(body), { status: 200 });
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

const actions = (mock: ReturnType<typeof vi.fn>) => calls(mock).filter((c) => c.method !== "GET");

describe("Users", () => {
  it("lists users; you cannot disable or delete yourself", async () => {
    stubUsers();
    render(<UsersCard me={OWNER} />);
    const row = (await screen.findByText("ana")).closest("tr")!;
    expect(within(row).getByRole("button", { name: "Disable" })).toBeInTheDocument();
    const mine = screen.getByText("owner").closest("tr")!;
    expect(within(mine).queryByRole("button", { name: "Disable" })).toBeNull();
    expect(within(mine).queryByLabelText("Delete owner")).toBeNull();
  });

  it("adds a staff user, changes a role and resets a password", async () => {
    const mock = stubUsers();
    vi.spyOn(window, "prompt").mockReturnValue("new-pass-12");
    render(<UsersCard me={OWNER} />);
    await screen.findByText("ana");
    const form = screen.getByLabelText("Add user");
    await userEvent.type(within(form).getByLabelText("Username"), "marko");
    await userEvent.type(within(form).getByLabelText("Password"), "staff-pass-2");
    await userEvent.click(within(form).getByRole("button", { name: "Add user" }));
    await userEvent.selectOptions(screen.getByLabelText("Role of ana"), "admin");
    await userEvent.click(screen.getByLabelText("New password for ana"));
    expect(actions(mock)).toEqual([
      { url: "/api/v1/users", method: "POST", body: { username: "marko", password: "staff-pass-2", role: "staff" } },
      { url: "/api/v1/users/2", method: "PATCH", body: { role: "admin" } },
      { url: "/api/v1/users/2", method: "PATCH", body: { password: "new-pass-12" } },
    ]);
  });

  it("shows the activity log", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify([
            { id: 2, at: "2026-10-19T10:05:00Z", username: "owner", action: "POST /api/v1/machines", status_code: 409, ip_address: "192.168.0.253" },
            { id: 1, at: "2026-10-19T10:00:00Z", username: null, action: "POST /api/v1/auth/login (x)", status_code: 401, ip_address: null },
          ]),
          { status: 200 },
        ),
      ),
    );
    render(<ActivityCard />);
    expect(await screen.findByText("POST /api/v1/machines")).toBeInTheDocument();
    expect(screen.getByText("409")).toBeInTheDocument();
  });

  it("changes one's own password and then signs out", async () => {
    const mock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", mock);
    const onChanged = vi.fn();
    render(<AccountCard me={ANA} onPasswordChanged={onChanged} />);
    await userEvent.type(screen.getByLabelText("Current password"), "staff-pass-1");
    await userEvent.type(screen.getByLabelText("New password"), "staff-pass-9");
    await userEvent.type(screen.getByLabelText("New password again"), "staff-pass-9");
    await userEvent.click(screen.getByRole("button", { name: "Change password" }));
    expect(calls(mock)).toEqual([
      {
        url: "/api/v1/auth/password",
        method: "POST",
        body: { current_password: "staff-pass-1", new_password: "staff-pass-9" },
      },
    ]);
    expect(onChanged).toHaveBeenCalled();
  });
});
