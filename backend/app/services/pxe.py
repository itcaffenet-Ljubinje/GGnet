"""
Network boot (PXE) for the Settings page: the boot settings the admin
changes in the web UI, and the state of the PXE service (proxyDHCP + TFTP).

Boot settings: `[boot] gateway` and `[boot] unregistered` in config.toml are
the defaults; once the admin saves them in the web UI, the saved values win
(table `settings`, key "boot"). They are read at every iPXE request, so a
change applies to the next PC that boots, with no restart.

The PXE service is ggNet's own dnsmasq (`ggnet-pxe`, scripts/install_ggnet.sh;
`[boot] pxe_service` names another unit, e.g. on the dev instance). The web
UI shows its state and can restart it; it never changes its configuration.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_config
from app.db.models import AppSetting
from app.runner import CommandRunner

logger = logging.getLogger("ggnet.pxe")

SETTINGS_KEY = "boot"
DEFAULT_UNIT = "ggnet-pxe"
# What the PCs fetch over TFTP: iPXE (snponly.efi uses the board's own network
# driver, ipxe.efi its built-in ones) and the script that sends iPXE to ggNet.
TFTP_FILES = ("snponly.efi", "ipxe.efi", "autoexec.ipxe")


@dataclass
class BootSettings:
    # iBFT gateway for Windows: "none" (0.0.0.0), "dhcp" or an IPv4 address.
    gateway: str = "none"
    # A PC whose MAC is not registered: "wait" on screen, or boot its "local" disk.
    unregistered: str = "wait"


def _defaults(cfg: dict[str, Any]) -> BootSettings:
    boot = cfg.get("boot") or {}
    return BootSettings(
        gateway=str(boot.get("gateway") or "none").strip() or "none",
        unregistered=str(boot.get("unregistered") or "wait"),
    )


def load_settings(db: Session, cfg: dict[str, Any] | None = None) -> tuple[BootSettings, bool]:
    """The saved boot settings and whether the admin saved them (else config.toml's)."""
    s = _defaults(cfg if cfg is not None else get_config())
    row = db.get(AppSetting, SETTINGS_KEY)
    if row is None:
        return s, False
    known = BootSettings.__dataclass_fields__
    saved = {k: v for k, v in json.loads(row.value).items() if k in known}
    return BootSettings(**{**asdict(s), **saved}), True


def save_settings(db: Session, s: BootSettings) -> None:
    row = db.get(AppSetting, SETTINGS_KEY)
    if row is None:
        db.add(AppSetting(key=SETTINGS_KEY, value=json.dumps(asdict(s))))
    else:
        row.value = json.dumps(asdict(s))
    db.commit()


def effective_config(db: Session, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """The config with `[boot]` replaced by the settings saved in the web UI, if any."""
    cfg = cfg if cfg is not None else get_config()
    s, saved = load_settings(db, cfg)
    if not saved:
        return cfg
    return {**cfg, "boot": {**(cfg.get("boot") or {}), **asdict(s)}}


@dataclass
class PxeStatus:
    unit: str
    installed: bool
    # systemd's ActiveState (active, inactive, failed, activating, ...) and SubState.
    state: str
    sub_state: str
    since: datetime | None
    tftp_root: str
    # Which of TFTP_FILES are in the TFTP root.
    files: dict[str, bool]


class PxeService:
    def __init__(self, unit: str, tftp_root: Path, runner: CommandRunner | None = None):
        self.unit = unit
        self.tftp_root = tftp_root
        self.runner = runner or CommandRunner(timeout=30)

    @classmethod
    def from_config(cls, cfg: dict[str, Any] | None = None) -> "PxeService":
        cfg = cfg if cfg is not None else get_config()
        root = (cfg.get("services") or {}).get("tftp_root") or Path(cfg["paths"]["data_dir"]) / "tftp"
        unit = str((cfg.get("boot") or {}).get("pxe_service") or DEFAULT_UNIT)
        return cls(unit, Path(root))

    def status(self) -> PxeStatus | None:
        """The service's state, or None when systemctl cannot be asked."""
        ok, out, _ = self.runner.run(
            ["systemctl", "show", self.unit,
             "--property=LoadState,ActiveState,SubState,ActiveEnterTimestamp", "--timestamp=unix"],
        )
        if not ok:
            return None
        props = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
        return PxeStatus(
            unit=self.unit,
            installed=props.get("LoadState") == "loaded",
            state=props.get("ActiveState") or "unknown",
            sub_state=props.get("SubState") or "",
            since=_unix_time(props.get("ActiveEnterTimestamp", "")),
            tftp_root=str(self.tftp_root),
            files={f: (self.tftp_root / f).is_file() for f in TFTP_FILES},
        )

    def restart(self) -> bool:
        ok, _, err = self.runner.run(["systemctl", "restart", self.unit])
        if ok:
            logger.info("PXE service %s restarted from the web UI", self.unit)
        else:
            logger.error("Restarting the PXE service %s failed: %s", self.unit, err)
        return ok


def _unix_time(value: str) -> datetime | None:
    """systemd's `@1760814131` (with --timestamp=unix); empty when never started."""
    try:
        return datetime.fromtimestamp(int(value.lstrip("@")), tz=timezone.utc) if value else None
    except ValueError:
        return None
