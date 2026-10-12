import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { AgentPackage } from "../api";
import { stubFetch } from "../test/fixtures";
import { ClientApp } from "./ClientApp";

const PKG: AgentPackage = {
  available: true,
  directory: "/var/lib/ggnet/agent",
  version: "0.1.9",
  server_url: "http://192.168.0.40:8088",
  install_command: "irm http://192.168.0.40:8088/api/v1/agent/bootstrap.ps1 | iex",
  files: [{ name: "ggnet-agent.exe", size_bytes: 76 * 1024 * 1024, sha256: "50a2663409fc19e6" }],
};

describe("ClientApp", () => {
  it("shows the version, the install command and the downloads", async () => {
    stubFetch(200, PKG);
    render(<ClientApp />);
    expect(await screen.findByLabelText("Install command")).toHaveValue(PKG.install_command);
    expect(screen.getByText("0.1.9")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download .zip" })).toHaveAttribute("href", "/api/v1/agent/download.zip");
    expect(screen.getByRole("link", { name: "ggnet-agent.exe" })).toHaveAttribute(
      "href",
      "/api/v1/agent/download/ggnet-agent.exe",
    );
    expect(screen.getByText("76.0 MB")).toBeInTheDocument();
  });

  it("copies the command, also without navigator.clipboard (plain http)", async () => {
    stubFetch(200, PKG);
    const exec = vi.fn().mockReturnValue(true);
    Object.defineProperty(document, "execCommand", { value: exec, configurable: true });
    vi.stubGlobal("navigator", { ...navigator, clipboard: undefined });
    render(<ClientApp />);
    await userEvent.click(await screen.findByRole("button", { name: "Copy" }));
    expect(exec).toHaveBeenCalledWith("copy");
    expect(screen.getByRole("button", { name: "Copied" })).toBeInTheDocument();
  });

  it("says where to put the files when the package is missing", async () => {
    stubFetch(200, { ...PKG, available: false, version: null, files: [] });
    render(<ClientApp />);
    expect(await screen.findByText(/not on the server yet/)).toHaveTextContent("/var/lib/ggnet/agent");
    expect(screen.queryByLabelText("Install command")).toBeNull();
  });
});
