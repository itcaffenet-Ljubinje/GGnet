import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { calls, disk, machine, stubFetch } from "../test/fixtures";

/** Opens the ⋮ menu of `name` and picks `item`. */
async function menu(name: string, item: string) {
  await userEvent.click(screen.getByRole("button", { name: `Actions for ${name}` }));
  await userEvent.click(screen.getByRole("menuitem", { name: item }));
}
import { GameDisksPage } from "./GameDisksPage";

describe("GameDisksPage", () => {
  it("lists disks with their state and assigned machines", () => {
    render(
      <GameDisksPage
        disks={[disk(), disk({ id: 2, name: "valorant", published: false, snapshot: null })]}
        machines={[machine({ game_disk_id: 1 }), machine({ id: 2, name: "pc02", game_disk_id: 1 })]}
        reload={vi.fn()}
      />,
    );
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("cs2");
    expect(rows[1]).toHaveTextContent("Published @base");
    expect(rows[1]).toHaveTextContent("2");
    expect(rows[2]).toHaveTextContent("Draft");
    // Only the draft can be published.
    expect(screen.getAllByRole("button", { name: "Publish" })).toHaveLength(1);
  });

  it("sums up images, kinds and PCs that use them", () => {
    render(
      <GameDisksPage
        disks={[disk(), disk({ id: 3, name: "win11", kind: "os", size_gb: 100, published: false, snapshot: null })]}
        machines={[machine({ game_disk_id: 1 }), machine({ id: 2, name: "pc02", game_disk_id: null })]}
        reload={vi.fn()}
      />,
    );
    const card = (title: string) => screen.getByText(title, { selector: ".kpi-title" }).closest(".kpi-card")!;
    expect(card("Images")).toHaveTextContent("2");
    expect(card("Images")).toHaveTextContent("1 draft");
    expect(card("OS images")).toHaveTextContent("1");
    expect(card("In use")).toHaveTextContent("of 2 PCs");
  });

  it("creates a disk and reloads", async () => {
    const fetchMock = stubFetch(201, disk());
    const reload = vi.fn().mockResolvedValue(undefined);
    render(<GameDisksPage disks={[]} machines={[]} reload={reload} />);

    await userEvent.type(screen.getByLabelText("Name"), "cs2");
    await userEvent.clear(screen.getByLabelText("Size (GB)"));
    await userEvent.type(screen.getByLabelText("Size (GB)"), "50");
    await userEvent.click(screen.getByRole("button", { name: "Create" }));

    expect(calls(fetchMock)).toEqual([
      { url: "/api/v1/game-disks", method: "POST", body: { name: "cs2", size_gb: 50, kind: "game" } },
    ]);
    expect(reload).toHaveBeenCalled();
    expect(screen.getByLabelText("Name")).toHaveValue("");
  });

  it("does nothing when publish is not confirmed", async () => {
    const fetchMock = stubFetch();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    render(
      <GameDisksPage
        disks={[disk({ published: false, snapshot: null })]}
        machines={[]}
        reload={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Publish" }));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renames a disk after asking for the new name", async () => {
    const fetchMock = stubFetch(200, disk({ name: "steam-main" }));
    const prompt = vi.spyOn(window, "prompt").mockReturnValue(" Steam-Main ");
    const reload = vi.fn().mockResolvedValue(undefined);
    render(<GameDisksPage disks={[disk()]} machines={[]} reload={reload} />);
    await menu("cs2", "Edit");
    expect(prompt).toHaveBeenCalledWith(expect.stringContaining('"cs2"'), "cs2");
    expect(calls(fetchMock)).toEqual([
      { url: "/api/v1/game-disks/1", method: "PATCH", body: { name: "steam-main" } },
    ]);
    expect(reload).toHaveBeenCalled();
  });

  it("does not rename when the prompt is cancelled or unchanged", async () => {
    const fetchMock = stubFetch();
    const prompt = vi.spyOn(window, "prompt").mockReturnValueOnce(null).mockReturnValueOnce("cs2");
    render(<GameDisksPage disks={[disk()]} machines={[]} reload={vi.fn()} />);
    await menu("cs2", "Edit");
    await menu("cs2", "Edit");
    expect(prompt).toHaveBeenCalledTimes(2);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows the backend error when delete fails", async () => {
    stubFetch(409, { detail: { error: "Game disk 'cs2' is assigned to 1 machine(s); move them first" } });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<GameDisksPage disks={[disk()]} machines={[]} reload={vi.fn()} />);

    await menu("cs2", "Remove");
    expect(await screen.findByRole("alert")).toHaveTextContent("assigned to 1 machine(s)");
  });

  it("starts editing a draft on a free PC", async () => {
    const fetchMock = stubFetch(200, disk({ published: false, snapshot: null, editor_id: 1 }));
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const reload = vi.fn().mockResolvedValue(undefined);
    render(
      <GameDisksPage
        disks={[disk({ published: false, snapshot: null })]}
        machines={[
          machine(),
          // Not offered: it already has a game disk.
          machine({ id: 2, name: "pc02", game_disk_id: 9, status: "provisioned" }),
        ]}
        reload={reload}
      />,
    );
    const select = screen.getByLabelText("PC to edit cs2 on");
    expect(within(select).getAllByRole("option").map((o) => o.textContent)).toEqual(["PC…", "pc01"]);
    expect(screen.getByRole("button", { name: "Edit on PC" })).toBeDisabled();

    await userEvent.selectOptions(select, "1");
    await userEvent.click(screen.getByRole("button", { name: "Edit on PC" }));
    expect(calls(fetchMock)).toEqual([
      { url: "/api/v1/game-disks/1/edit", method: "POST", body: { machine_id: 1 } },
    ]);
    expect(reload).toHaveBeenCalled();
  });

  it("shows the editor and finishes editing only when the PC is off", async () => {
    const draft = disk({ published: false, snapshot: null, editor_id: 1 });
    const editor = machine({ status: "editing", editing_disk_id: 1, session_active: true });
    const { rerender } = render(<GameDisksPage disks={[draft]} machines={[editor]} reload={vi.fn()} />);

    expect(screen.getByText("Editing on pc01")).toBeInTheDocument();
    // No publish or new edit while the master is mapped to a PC.
    expect(screen.queryByRole("button", { name: "Publish" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Edit on PC" })).toBeNull();
    expect(screen.getByRole("button", { name: "Finish editing" })).toBeDisabled();

    const fetchMock = stubFetch(200, disk({ published: false, snapshot: null }));
    vi.spyOn(window, "confirm").mockReturnValue(true);
    rerender(
      <GameDisksPage
        disks={[draft]}
        machines={[{ ...editor, session_active: false }]}
        reload={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Finish editing" }));
    expect(calls(fetchMock)).toEqual([
      { url: "/api/v1/game-disks/1/finish-edit", method: "POST", body: undefined },
    ]);
  });

  it("opens an image's details page from its name or the menu, and goes back", async () => {
    stubFetch(200, []);
    render(
      <GameDisksPage
        disks={[disk(), disk({ id: 2, name: "draft", published: false, snapshot: null })]}
        machines={[]}
        reload={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "cs2" }));
    expect(screen.getByRole("heading", { level: 2, name: "cs2" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Snapshots" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Writebacks" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Images" }));
    await menu("draft", "Details");
    expect(screen.getByText(/A draft has no snapshots or writebacks yet/)).toBeInTheDocument();
  });

  it("offers Remove only for an image no PC uses", async () => {
    render(<GameDisksPage disks={[disk()]} machines={[machine({ game_disk_id: 1 })]} reload={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "Actions for cs2" }));
    expect(screen.getByRole("menuitem", { name: "Remove" })).toBeDisabled();
  });

  it("lists OS images and game disks apart and creates an OS image", async () => {
    const fetchMock = stubFetch(201, disk({ id: 3, name: "win11", kind: "os" }));
    render(
      <GameDisksPage
        disks={[disk(), disk({ id: 3, name: "win11", kind: "os", zvol_path: "tank/ggnet/images/win11" })]}
        machines={[machine({ mode: "boot", os_disk_id: 3, game_disk_id: 1 })]}
        reload={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(headings).toEqual(["OS images1", "Game disks1"]);
    const [osTable, gameTable] = screen.getAllByRole("table");
    expect(osTable).toHaveTextContent("win11");
    expect(osTable).not.toHaveTextContent("cs2");
    expect(gameTable).toHaveTextContent("cs2");

    await userEvent.type(screen.getByLabelText("Name"), "win11-b");
    await userEvent.selectOptions(screen.getByLabelText("Kind"), "os");
    await userEvent.click(screen.getByRole("button", { name: "Create" }));
    expect(calls(fetchMock).filter((c) => c.method === "POST")[0].body).toMatchObject({ kind: "os" });
  });

  it("prepares an OS image after confirmation; game disks have no such button", async () => {
    const fetchMock = stubFetch(200, disk({ id: 3, name: "win11", kind: "os", snapshot: "v2" }));
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const reload = vi.fn().mockResolvedValue(undefined);
    render(
      <GameDisksPage
        disks={[disk(), disk({ id: 3, name: "win11", kind: "os" })]}
        machines={[]}
        reload={reload}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Actions for cs2" }));
    expect(screen.queryByRole("menuitem", { name: "Prepare image" })).toBeNull();
    await userEvent.keyboard("{Escape}");
    await menu("win11", "Prepare image");
    expect(calls(fetchMock).filter((c) => c.method !== "GET")).toEqual([
      { url: "/api/v1/game-disks/3/prepare", method: "POST", body: undefined },
    ]);
    expect(reload).toHaveBeenCalled();
  });
});
