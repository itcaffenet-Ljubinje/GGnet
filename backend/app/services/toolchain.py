"""
Add new hardware: an OS image learns a PC's network card the way Windows
learns any new device, by installing it.

A PC whose boot network card the image has never had installed stops at
0x7B: Windows loads the boot card's driver before Plug and Play runs only
when the card's device entry (under its exact instance ID) is configured.
Copying another board's entry (windows_setup.nic_patch) covers the same chip
on another board; a new chip needs a real install. So the server

  1. clones the image's newest version and writes into the clone the agent,
     its service and a job naming the cards (PCI hardware ID + instance ID,
     as the PC's agent or the hardware scan reports them);
  2. boots the clone in a temporary Proxmox VM (ToolchainVm: OVMF, the
     clone as its SATA disk, no network). The agent finds the job, creates
     each card's device under its instance ID with SetupAPI and lets
     Windows install its best driver (inbox or from the driver store),
     writes the result and shuts the VM down;
  3. reads the result, prepares the clone again (the new card's driver is
     marked for a network boot) and makes it the image's next version.

The PCs keep booting the current version while this runs; the VM is
removed when it ends, whatever the outcome. HardwareAdder runs one job per
image in the background and keeps its progress in memory for the UI.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from app.services.provisioning import Provisioner, ProvisioningError
from app.windows_setup import ImagePrep

logger = logging.getLogger("ggnet.toolchain")

VM_NAME_PREFIX = "ggnet-hw-"
VM_TAG = "ggnet-toolchain"
VM_MEMORY_MB = 4096
VM_CORES = 4
# Windows' first start on the VM's devices plus the install; then it is stuck.
VM_TIMEOUT = 30 * 60
POLL_EVERY = 5.0
_STATUS = re.compile(r"^status:\s*(\w+)", re.MULTILINE)


class ToolchainVm:
    """A temporary Proxmox VM that boots one zvol until Windows shuts down."""

    def __init__(self, runner, timeout: float = VM_TIMEOUT, poll: float = POLL_EVERY,
                 sleep: Callable[[float], None] = time.sleep):
        self.runner = runner
        self.timeout = timeout
        self.poll = poll
        self.sleep = sleep

    def next_id(self) -> int | None:
        ok, out, _ = self.runner.run(["pvesh", "get", "/cluster/nextid"])
        try:
            return int(out.strip().strip('"')) if ok else None
        except ValueError:
            return None

    def create_args(self, vmid: int, device: str, label: str) -> list[str]:
        return [
            "qm", "create", str(vmid), "--name", f"{VM_NAME_PREFIX}{label}"[:63],
            "--description", "ggNet Add new hardware: temporary, removed when the run ends",
            "--tags", VM_TAG, "--ostype", "win11", "--machine", "q35", "--bios", "ovmf",
            "--cpu", "host", "--cores", str(VM_CORES), "--memory", str(VM_MEMORY_MB),
            "--sata0", f"{device},cache=none", "--boot", "order=sata0", "--vga", "std",
        ]

    def status(self, vmid: int) -> str | None:
        ok, out, _ = self.runner.run(["qm", "status", str(vmid)], quiet=True)
        m = _STATUS.search(out) if ok else None
        return m.group(1) if m else None

    def remove(self, vmid: int) -> None:
        """Stop the VM and remove it; its disk (the clone) is only detached."""
        if self.status(vmid) == "running":
            self.runner.run(["qm", "stop", str(vmid), "--skiplock", "1"])
        self.runner.run(["qm", "set", str(vmid), "--delete", "sata0"])
        if not self.runner.run(["qm", "destroy", str(vmid), "--skiplock", "1"])[0]:
            logger.error("Could not remove the toolchain VM %s: %s", vmid, self.runner.last_error)

    def run(self, device: str, label: str, cancel: threading.Event | None = None) -> str | None:
        """Boot `device` and wait until the VM stops by itself. None, or why it failed."""
        vmid = self.next_id()
        if vmid is None:
            return f"no free VM ID: {self.runner.last_error}"
        if not self.runner.run(self.create_args(vmid, device, label))[0]:
            return f"creating the toolchain VM failed: {self.runner.last_error}"
        try:
            if not self.runner.run(["qm", "start", str(vmid)])[0]:
                return f"starting the toolchain VM failed: {self.runner.last_error}"
            logger.info("Toolchain VM %s started on %s", vmid, device)
            waited = 0.0
            while waited < self.timeout:
                if cancel is not None and cancel.is_set():
                    return "cancelled"
                self.sleep(self.poll)
                waited += self.poll
                status = self.status(vmid)
                if status == "stopped":
                    logger.info("Toolchain VM %s stopped after %.0f s", vmid, waited)
                    return None
                if status is None:
                    return f"the toolchain VM {vmid} is gone"
            return f"Windows did not finish within {self.timeout // 60:.0f} minutes"
        finally:
            self.remove(vmid)


@dataclass
class HardwareJob:
    nics: list[tuple[str, str]]
    step: str = "starting"
    error: str | None = None
    snapshot: str | None = None
    devices: list[dict] = field(default_factory=list)
    started: float = field(default_factory=time.time)
    finished: float | None = None
    cancel: threading.Event = field(default_factory=threading.Event)

    @property
    def running(self) -> bool:
        return self.finished is None

    def out(self) -> dict:
        return {"cards": [{"nic": n, "instance": i} for n, i in self.nics], "step": self.step,
                "running": self.running, "error": self.error, "snapshot": self.snapshot,
                "devices": self.devices, "started": self.started, "finished": self.finished}


class HardwareAdder:
    """Add new hardware jobs, one per image, in the background."""

    def __init__(self, prov: Provisioner, vm: ToolchainVm, prep: Callable[[], ImagePrep],
                 background: bool = True):
        self.prov = prov
        self.vm = vm
        self.prep = prep
        self.background = background     # tests run the job in the request
        self.jobs: dict[str, HardwareJob] = {}
        self._guard = threading.Lock()

    def job(self, master: str) -> HardwareJob | None:
        return self.jobs.get(master)

    def start(self, master: str, nics: list[tuple[str, str]],
              done: Callable[[str], None] = lambda snapshot: None) -> HardwareJob:
        """Start a job; `done(new snapshot)` runs when it succeeded. ValueError when one runs."""
        with self._guard:
            current = self.jobs.get(master)
            if current is not None and current.running:
                raise ValueError("Add new hardware is already running for this image")
            job = self.jobs[master] = HardwareJob(nics=list(nics))
        if self.background:
            threading.Thread(target=self._run, args=(master, job, done), name="ggnet-hwadd", daemon=True).start()
        else:
            self._run(master, job, done)
        return job

    def cancel(self, master: str) -> bool:
        job = self.jobs.get(master)
        if job is None or not job.running:
            return False
        job.cancel.set()
        return True

    def _run(self, master: str, job: HardwareJob, done: Callable[[str], None]) -> None:
        label = master.rsplit("/", 1)[-1]

        def step(name: str) -> None:
            if job.cancel.is_set():
                raise ProvisioningError("cancelled")
            job.step = name

        try:
            snapshot, devices = self.prov.add_hardware(
                master, job.nics, self.prep(), boot=lambda device: self.vm.run(device, label, job.cancel), step=step)
            job.snapshot, job.devices, job.step = snapshot, devices, "done"
            try:
                comment = "ggNet: added " + ", ".join(f"PCI\\{n}" for n, _ in job.nics)
                self.prov.set_comment(master, snapshot, comment[:200])
            except Exception as e:      # the version is there; only its comment is missing
                logger.warning("%s", e)
            done(snapshot)
            logger.info("Add new hardware on %s done: @%s", master, snapshot)
        except ProvisioningError as e:
            job.error = str(e)
            logger.warning("Add new hardware on %s failed: %s", master, e)
        except Exception as e:
            job.error = f"unexpected error: {e}"
            logger.exception("Add new hardware on %s failed", master)
        finally:
            job.finished = time.time()
