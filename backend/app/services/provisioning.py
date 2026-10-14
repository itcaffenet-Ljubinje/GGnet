"""
Provisioner: host operations for game disks and machines, always in the
order the rules require. It knows nothing about the database: it takes
values and returns a result, or raises ProvisioningError with the reason.

All operations go through one lock: one backend process, ~17 machines, and
parallel zfs/targetcli calls on the same zvol would collide.
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass

from app.iscsi_manager import SLOTS, Disk, ISCSIManager
from app.windows_setup import OsSetup, WindowsSetup
from app.zfs_manager import ZFSManager

logger = logging.getLogger("ggnet.provisioning")


class ProvisioningError(Exception):
    """A host operation failed. The message is shown to the user."""


_VERSION_RE = re.compile(r"^v(\d+)$")


def next_version(snapshots: list[str]) -> str:
    """Name of the next image version: `base` counts as v1, so base → v2 → v3 ..."""
    numbers = [1 if s == "base" else int(m.group(1))
               for s in snapshots if s == "base" or (m := _VERSION_RE.match(s))]
    return f"v{max(numbers, default=0) + 1}"


@dataclass
class ClientDisk:
    clone_zvol: str
    clone_snapshot: str
    iscsi_target_iqn: str
    # Boot Mode only: the machine's writeback of its OS image (mapped LUN 0).
    os_clone_zvol: str | None = None
    os_clone_snapshot: str | None = None
    # Why the fresh OS writeback could not be set up as this PC (it boots
    # with the image's name then); None when it was, or nothing was asked.
    os_setup_problem: str | None = None


class Provisioner:
    def __init__(self, zfs: ZFSManager, iscsi: ISCSIManager, windows: WindowsSetup | None = None):
        self.zfs = zfs
        self.iscsi = iscsi
        # Boot Mode: writes the PC's identity into its fresh OS writeback.
        self.windows = windows
        self.lock = threading.Lock()

    # ── Helpers ───────────────────────────────────────────────────────

    def _fail(self, msg: str, runner=None) -> ProvisioningError:
        detail = (runner or self.zfs.runner).last_error
        full = f"{msg}: {detail}" if detail else msg
        logger.error(full)
        return ProvisioningError(full)

    def _clear(self) -> None:
        self.zfs.runner.last_error = ""
        self.iscsi.runner.last_error = ""

    def image_path(self, disk_name: str) -> str:
        return f"{self.zfs.layout.images}/{disk_name}"

    def client_path(self, machine_name: str) -> str:
        return f"{self.zfs.layout.writebacks}/{machine_name}"

    def os_client_path(self, machine_name: str) -> str:
        """Boot Mode OS writeback; machine names never end in `-os`, so no game clone collides."""
        return f"{self.zfs.layout.writebacks}/{machine_name}-os"

    def _disks(self, clone: str, os_clone: str | None) -> list[Disk]:
        """The machine's LUNs: Disk Mode game = LUN 0; Boot Mode OS = LUN 0, game = LUN 1."""
        game = Disk("game", self.zfs.zvol_device_path(clone))
        if os_clone is None:
            return [game]
        return [Disk("os", self.zfs.zvol_device_path(os_clone)), game]

    def _set_up_os(self, os_clone: str | None, os_setup: OsSetup | None) -> str | None:
        """Personalize a fresh OS clone before it is mapped (app.windows_setup)."""
        if os_clone is None or os_setup is None or self.windows is None:
            return None
        problem = self.windows.personalize(self.zfs.zvol_device_path(os_clone), os_setup)
        if problem:
            logger.warning("%s boots with the image's identity: %s", os_setup.computer_name, problem)
        return problem

    def _detach(self, machine_name: str, initiator_iqn: str) -> None:
        """
        Remove the machine's ACL and backstores and verify the backstores are
        really gone: LIO keeps a zvol open while its backstore exists, so
        destroying the clone would fail with "dataset is busy" (or, worse, the
        client would keep a session to a disk that is being replaced).
        """
        self.iscsi.detach(machine_name, initiator_iqn)
        for slot in SLOTS:
            if self.iscsi.backstore_exists(machine_name, slot) is not False:
                raise self._fail("The iSCSI disk was not removed", self.iscsi.runner)

    # ── Game disk (master) ────────────────────────────────────────────

    def create_disk(self, name: str, size_gb: int, os_image: bool = False) -> str:
        """
        Empty zvol for a master (draft). Returns the ZFS path. An OS image
        gets the properties for Windows' small random I/O (16k, lz4, sync);
        see docs/architecture.md, "Properties".
        """
        path = self.image_path(name)
        props = dict(volblocksize="16k", compression="lz4", sync="standard") if os_image else {}
        with self.lock:
            self._clear()
            if self.zfs.dataset_exists(path):
                raise ProvisioningError(f"Zvol {path} already exists on the host")
            if not self.zfs.create_zvol(path, size_gb, **props):
                raise self._fail(f"Creating zvol {path} failed")
        return path

    def publish_disk(self, zvol_path: str, snap_name: str = "base") -> str:
        """publish_master(): snapshot → hold → readonly."""
        with self.lock:
            self._clear()
            if not self.zfs.publish_master(zvol_path, snap_name):
                raise self._fail(f"Publishing master {zvol_path}@{snap_name} failed")
        return snap_name

    def snapshots(self, zvol_path: str) -> list[dict]:
        """Versions of a master with their sizes and clones (see ZFSManager.snapshot_details)."""
        details = self.zfs.snapshot_details(zvol_path)
        if details is None:
            raise self._fail(f"Listing versions of {zvol_path} failed")
        return details

    def writebacks(self) -> list[dict]:
        """Every client clone on the host with its size and origin."""
        return self.zfs.list_clients()

    def delete_snapshot(self, zvol_path: str, name: str) -> None:
        with self.lock:
            self._clear()
            if not self.zfs.destroy_snapshot(f"{zvol_path}@{name}"):
                raise self._fail(f"Deleting {zvol_path}@{name} failed")

    def pool_space(self) -> dict:
        space = self.zfs.pool_space()
        if space is None:
            raise self._fail(f"Reading the space of pool {self.zfs.layout.pool} failed")
        return space

    def reserved_bytes(self) -> int:
        return self.zfs.reserved_bytes()

    def set_reserved_percent(self, percent: int) -> int:
        """Reserve `percent` of the pool's usable space; returns the bytes reserved."""
        with self.lock:
            self._clear()
            space = self.pool_space()
            nbytes = space["total"] * percent // 100
            if not self.zfs.set_reserved(nbytes):
                raise self._fail(f"Reserving {percent}% of pool {self.zfs.layout.pool} failed")
        return nbytes

    def delete_disk(self, zvol_path: str, published: bool) -> None:
        """
        A published master goes only through destroy_master(); a draft has
        no snapshots or holds, so a plain destroy is enough.
        """
        with self.lock:
            self._clear()
            if not self.zfs.dataset_exists(zvol_path):
                logger.warning("Zvol %s does not exist on the host; deleting the record only", zvol_path)
                return
            ok = (self.zfs.destroy_master(zvol_path) if published
                  else self.zfs.destroy(zvol_path, recursive=True))
            if not ok:
                raise self._fail(f"Deleting {zvol_path} failed")

    def start_edit(self, machine_name: str, initiator_iqn: str, zvol_path: str) -> str:
        """
        Map a DRAFT master as the machine's game disk so it can be filled on
        that PC. Returns the target IQN. The caller makes sure the disk is a
        draft and the machine has nothing else mapped.
        """
        with self.lock:
            self._clear()
            if self.zfs.get_property(zvol_path, "readonly") != "off":
                raise self._fail(f"{zvol_path} is not a writable draft")
            iqn = self.iscsi.attach(
                machine_name, initiator_iqn, [Disk("game", self.zfs.zvol_device_path(zvol_path))]
            )
            if iqn is None:
                raise self._fail("Exposing the master over iSCSI failed", self.iscsi.runner)
        return iqn

    def finish_edit(self, machine_name: str, initiator_iqn: str) -> None:
        """Unmap the master from the editing machine. The client must be shut down."""
        with self.lock:
            self._clear()
            self._detach(machine_name, initiator_iqn)

    # ── Machines ──────────────────────────────────────────────────────

    def provision(
        self, machine_name: str, initiator_iqn: str, snapshot_path: str,
        os_snapshot_path: str | None = None, os_setup: OsSetup | None = None,
    ) -> ClientDisk:
        """
        Clone of the game disk snapshot, exposed on the shared iSCSI target
        as mapped LUN 0 of an ACL for the machine's initiator IQN. With
        `os_snapshot_path` (Boot Mode) the OS image is cloned too and becomes
        LUN 0, the game disk LUN 1; `os_setup` is written into the OS clone
        before it is mapped.
        """
        clones = [(snapshot_path, self.client_path(machine_name))]
        if os_snapshot_path is not None:
            clones.append((os_snapshot_path, self.os_client_path(machine_name)))
        with self.lock:
            self._clear()
            for _, clone in clones:
                if self.zfs.dataset_exists(clone):
                    raise ProvisioningError(
                        f"Clone {clone} already exists on the host; deprovision first"
                    )
            made: list[str] = []

            def rollback() -> None:
                for clone in made:
                    if not self.zfs.destroy(clone, recursive=True):
                        logger.error("Rollback: clone %s left on the host", clone)

            for snap, clone in clones:
                if not self.zfs.clone(snap, clone):
                    err = self._fail(f"Clone {snap} -> {clone} failed")
                    rollback()
                    raise err
                made.append(clone)
            os_clone = clones[1][1] if os_snapshot_path is not None else None
            problem = self._set_up_os(os_clone, os_setup)
            iqn = self.iscsi.attach(machine_name, initiator_iqn, self._disks(clones[0][1], os_clone))
            if iqn is None:
                err = self._fail("Exposing the disk over iSCSI failed", self.iscsi.runner)
                # attach() cleaned up its own iSCSI state; roll back the clones.
                rollback()
                raise err
        return ClientDisk(clones[0][1], snapshot_path, iqn, os_clone, os_snapshot_path, problem)

    def reset(
        self, machine_name: str, initiator_iqn: str, clone_zvol: str, snapshot_path: str,
        os_clone_zvol: str | None = None, os_snapshot_path: str | None = None,
        os_setup: OsSetup | None = None,
    ) -> ClientDisk:
        """
        Order: detach (ACL + backstores) → destroy clones → clone → attach.
        `snapshot_path` is the disk's CURRENT snapshot, so a reset also moves
        the machine to the newest version of the master. Boot Mode passes the
        OS clone and snapshot too; both writebacks are reset together, and
        `os_setup` is written into the fresh OS clone before it is mapped.
        The client must be powered off or disconnected.
        """
        if (os_clone_zvol is None) != (os_snapshot_path is None):
            raise ProvisioningError("An OS writeback needs both its zvol and its snapshot")
        with self.lock:
            self._clear()
            self._detach(machine_name, initiator_iqn)
            if not self.zfs.reset_clone(clone_zvol, snapshot_path):
                raise self._fail(f"Resetting clone {clone_zvol} failed")
            if os_clone_zvol is not None and not self.zfs.reset_clone(os_clone_zvol, os_snapshot_path):
                raise self._fail(f"Resetting clone {os_clone_zvol} failed")
            problem = self._set_up_os(os_clone_zvol, os_setup)
            iqn = self.iscsi.attach(machine_name, initiator_iqn, self._disks(clone_zvol, os_clone_zvol))
            if iqn is None:
                raise self._fail("Exposing the disk over iSCSI failed", self.iscsi.runner)
        return ClientDisk(clone_zvol, snapshot_path, iqn, os_clone_zvol, os_snapshot_path, problem)

    def deprovision(
        self, machine_name: str, initiator_iqn: str, clone_zvol: str | None,
        os_clone_zvol: str | None = None,
    ) -> None:
        """
        Detach from iSCSI, then delete the clones. Safe to call when nothing
        exists. The OS clone is only deleted when it is named: a Disk Mode
        machine has none.
        """
        clones = [clone_zvol or self.client_path(machine_name)]
        if os_clone_zvol is not None:
            clones.append(os_clone_zvol)
        with self.lock:
            self._clear()
            self._detach(machine_name, initiator_iqn)
            for clone in clones:
                if self.zfs.dataset_exists(clone) and not self.zfs.destroy(clone, recursive=True):
                    raise self._fail(f"Deleting clone {clone} failed")

    # ── Writeback lifecycle ───────────────────────────────────────────

    def session_active(self, initiator_iqn: str, target_iqn: str | None = None) -> bool | None:
        """Live LIO session state of a machine; None when unknown."""
        return self.iscsi.session_active(initiator_iqn, target_iqn)

    def set_keep_writeback(self, clone_zvol: str, keep: bool, os_clone_zvol: str | None = None) -> None:
        """
        A kept writeback holds the admin's installs, so it gets sync=standard;
        a disposable one sync=disabled (it is thrown away anyway). Boot Mode
        keeps the OS writeback too.
        """
        with self.lock:
            self._clear()
            for clone in filter(None, (clone_zvol, os_clone_zvol)):
                if self.zfs.dataset_exists(clone) and not self.zfs.set_property(
                    clone, "sync", "standard" if keep else "disabled"
                ):
                    raise self._fail(f"Setting sync on {clone} failed")

    def apply_writebacks(
        self, machine_name: str, initiator_iqn: str, clone_zvol: str, master: str, base_snap: str
    ) -> str:
        """
        Make the clone's content the next version of `master` (ggRock
        "Apply Writebacks"). Returns the new snapshot name. The machine must
        be powered off. The clone itself becomes the master, so it is
        unmapped first; the caller re-clones the machine from the new
        version. On failure the clone is mapped again.
        """
        with self.lock:
            self._clear()
            snaps = self.zfs.list_snapshots(master)
            if snaps is None:
                raise self._fail(f"Listing versions of {master} failed")
            new = next_version(snaps)
            self._detach(machine_name, initiator_iqn)
            if not self.zfs.apply_clone(clone_zvol, master, base_snap, new):
                err = self._fail(f"Applying {clone_zvol} to {master} failed")
                if self.iscsi.attach(machine_name, initiator_iqn,
                                     [Disk("game", self.zfs.zvol_device_path(clone_zvol))]) is None:
                    logger.error("Apply failed and %s could not be mapped again", clone_zvol)
                raise err
        return new
