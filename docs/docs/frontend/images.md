# Images Management Frontend Plan

## Scope
- `Images` tab experience covering system and game images.
- Snapshot lifecycle (creation, promotion, writeback handling).
- Integrations with automated cleanup flows and machine assignments.

## Image Catalog
- Split view by image type (`System`, `Game`); allow combined filter and search by name ([Images KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860371/Images)).
- Card/table hybrid: show `Name`, `Type`, `Base Size`, `Latest Snapshot`, `Writebacks`, `Last Modified`, `Assigned Machines`.
- Default sort by last updated. Provide tag for default boot images.
- Surface compatibility hints reminding operators to keep paired system/game images in sync (Images doc export, Nov 9 2025).

## Creating Images
- **Wizard:** `Name`, `Type`, `Volume Size`, `Source` (clone existing vs. upload), `Make Default`.
- For system images, include OS template selection guidance; for game images, remind of storage impact.
- Validate disk space against array reserved space; show warning if under threshold.
- Present support note that native creation flow is currently recommended for game images unless otherwise advised (Images doc export, Nov 9 2025).
- Microcopy:
  - `Name` placeholder: `e.g. "Game Library 2025"`.
  - `Image Type` tooltip: `Select "Game" unless instructed by support staff`.
  - `Make Default` helper: `Machines assigned this image type will switch on next reboot`.
  - Volume size hint: `Ensure free space exceeds requested size and reserved disk threshold`.

## Snapshot Management
- For each image display snapshot timeline with metadata (created, author, notes).
- Actions: `Create Snapshot`, `Promote to Default`, `Assign to Machines`, `Delete`.
- Deleting requires dependency check (warn if machines pinned). Integrate with automation policy for aged snapshots ([Automated Snapshot Removal](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860543/Automated+Snapshot+and+Writeback+Removal)).
- Microcopy:
  - `Promote to Default` tooltip: `Machines adopt this snapshot after their next reboot`.
  - `Apply Writebacks` button text: `Commit pending changes to make them permanent`.
  - Deletion confirmation copy: `Snapshots in use may disrupt boots; proceed with caution`.

## Writeback Handling
- Show active writebacks count per image with size. Provide button to `Apply Writebacks` (commit) mirroring machines UI.
- Allow per-image retention override to opt-out of automated cleanup.
- Warning banner: `Large writebacks can quickly consume reserved space. Apply or purge to maintain performance.`

## Image Settings & Metadata
- Support editing description, change log, custom labels.
- Display checksum and build version when available (useful for QA).
- Expose advanced options (pinned snapshot, protected flag) behind expandable panel.

## Bulk Operations
- Multi-select to delete snapshots, change defaults, or export metadata.
- Provide progress feedback; block bulk delete if any selected snapshot currently mounted.

## Edge Cases
- If upload feature used, show resumable progress and hash verification.
- Handle missing base snapshot gracefully (mark image as `Requires Repair` with guidance).
- When automated cleanup scheduled, highlight upcoming deletions with ability to protect snapshot.
- Provide tooling for local/remote backups and restores:
  - Local backup workflow: select destination path, show progress and success banner.
  - Remote backup workflow: capture SSH credentials/target, display job status.
  - Restore flows (local/remote) must validate checksum and map to target pool.
  - Advanced users may access CLI instructions (link to knowledge base) for scripted backups ([Images KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860371/Images); Images doc export, Nov 9 2025).

## Data Flow
- APIs: `GET/POST /images`, `POST /images/{id}/snapshots`, `POST /images/{id}/writebacks/apply`, `DELETE /images/{id}`.
- Requires cross-module data with machines (assignment counts) and array (storage utilisation).
- Consider WebSocket updates for snapshot creation progress.

## Open Questions
- Should snapshot timeline support annotations? confirm requirement with stakeholders.
- Determine UX for exporting images (download vs. replicate).
- Clarify whether system+game pairing rules need to be enforced in UI.

## References
- [Images KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860371/Images)
- [Automated Snapshot and Writeback Removal](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860543/Automated+Snapshot+and+Writeback+Removal)
- Confluence export: `GGROCK/docs/Images.doc` (local manual snapshot)

