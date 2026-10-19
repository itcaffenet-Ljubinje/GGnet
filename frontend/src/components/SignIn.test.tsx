import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SIGNED_OUT, api, type User } from "../api";
import { calls, stubFetch } from "../test/fixtures";
import { SignIn } from "./SignIn";

const OWNER: User = {
  id: 1,
  username: "owner",
  role: "admin",
  disabled: false,
  created_at: "2026-10-19T10:00:00Z",
  last_login_at: null,
};

describe("SignIn", () => {
  it("signs in and hands over the user", async () => {
    const mock = stubFetch(200, { setup_required: false, user: OWNER });
    const onSignedIn = vi.fn();
    render(<SignIn setup={false} onSignedIn={onSignedIn} />);
    await userEvent.type(screen.getByLabelText("Username"), " owner ");
    await userEvent.type(screen.getByLabelText("Password"), "cafe-owner-1");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(calls(mock)).toEqual([
      { url: "/api/v1/auth/login", method: "POST", body: { username: "owner", password: "cafe-owner-1" } },
    ]);
    expect(onSignedIn).toHaveBeenCalledWith(OWNER);
    expect(screen.queryByLabelText("Setup code")).toBeNull();
  });

  it("shows a wrong password", async () => {
    stubFetch(401, { detail: { error: "Wrong username or password" } });
    const onSignedIn = vi.fn();
    render(<SignIn setup={false} onSignedIn={onSignedIn} />);
    await userEvent.type(screen.getByLabelText("Username"), "owner");
    await userEvent.type(screen.getByLabelText("Password"), "nope-nope");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Wrong username or password");
    expect(onSignedIn).not.toHaveBeenCalled();
  });

  it("creates the first admin with the setup code", async () => {
    const mock = stubFetch(200, { setup_required: false, user: OWNER });
    const onSignedIn = vi.fn();
    render(<SignIn setup onSignedIn={onSignedIn} />);
    expect(screen.getByText(/ggnet-admin setup-code/)).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Setup code"), "3f9a-0c71-b2e4");
    await userEvent.type(screen.getByLabelText("Username"), "owner");
    await userEvent.type(screen.getByLabelText("Password"), "cafe-owner-1");
    await userEvent.type(screen.getByLabelText("Password again"), "cafe-owner-2");
    await userEvent.click(screen.getByRole("button", { name: "Create admin" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("The passwords differ");
    expect(calls(mock)).toEqual([]);

    await userEvent.clear(screen.getByLabelText("Password again"));
    await userEvent.type(screen.getByLabelText("Password again"), "cafe-owner-1");
    await userEvent.click(screen.getByRole("button", { name: "Create admin" }));
    expect(calls(mock)).toEqual([
      {
        url: "/api/v1/auth/setup",
        method: "POST",
        body: { setup_code: "3f9a-0c71-b2e4", username: "owner", password: "cafe-owner-1" },
      },
    ]);
    expect(onSignedIn).toHaveBeenCalledWith(OWNER);
  });

  it("an ended session tells the app to show the sign-in", async () => {
    stubFetch(401, { detail: { error: "Sign in first" } });
    const listener = vi.fn();
    window.addEventListener(SIGNED_OUT, listener);
    await expect(api.listMachines()).rejects.toThrow("Sign in first");
    await expect(api.login("x", "y")).rejects.toThrow();   // a wrong password is not a lost session
    window.removeEventListener(SIGNED_OUT, listener);
    expect(listener).toHaveBeenCalledTimes(1);
  });
});
