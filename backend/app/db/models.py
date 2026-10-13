"""
ORM models. Relations are real foreign keys, never IDs stored as strings.
"""

from __future__ import annotations

import enum
import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Stable constraint names; Alembic cannot reliably alter unnamed ones.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """
    Timezone-aware datetime that always comes back in UTC. SQLite drops the
    offset, so without this a value read back from the database is naive and
    the API would send it without "Z" (browsers then read it as local time).
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("naive datetime; use timezone-aware UTC values")
        return value.astimezone(timezone.utc) if value is not None else None

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


def _str_enum(cls: type[enum.Enum]) -> Enum:
    """Store an enum by its value as a plain string column (portable across databases)."""
    return Enum(cls, native_enum=False, length=16, values_callable=lambda e: [m.value for m in e])


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class DiskKind(str, enum.Enum):
    GAME = "game"    # game disk: Disk Mode D:, Boot Mode LUN 1
    OS = "os"        # Windows system disk of Boot Mode machines (LUN 0)


class GameDisk(Base):
    """
    Master image (shared disk). `kind` says whether it holds games or a
    Boot Mode Windows install. Until `snapshot` is set the disk is a draft
    and must not be assigned to machines. After publish_master(), `snapshot`
    is the name of the current snapshot (`base`, later `vN`).

    A draft is filled through one machine (`editor`): the draft zvol itself
    is mapped as that machine's game disk until editing is finished.
    """

    __tablename__ = "game_disks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    zvol_path: Mapped[str] = mapped_column(String(255), unique=True)
    size_gb: Mapped[int] = mapped_column(Integer)
    kind: Mapped[DiskKind] = mapped_column(
        _str_enum(DiskKind), default=DiskKind.GAME, server_default=DiskKind.GAME.value
    )
    snapshot: Mapped[str | None] = mapped_column(String(64), default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now)

    machines: Mapped[list["Machine"]] = relationship(
        back_populates="game_disk", foreign_keys="Machine.game_disk_id"
    )
    editor: Mapped["Machine | None"] = relationship(
        back_populates="editing_disk", foreign_keys="Machine.editing_disk_id"
    )

    @property
    def editor_id(self) -> int | None:
        return self.editor.id if self.editor else None

    @property
    def published(self) -> bool:
        return self.snapshot is not None

    @property
    def snapshot_path(self) -> str | None:
        return f"{self.zvol_path}@{self.snapshot}" if self.snapshot else None


class MachineMode(str, enum.Enum):
    DISK = "disk"    # local Windows on C:, game disk over iSCSI
    BOOT = "boot"    # diskless UEFI PXE boot: OS disk (LUN 0) + game disk (LUN 1)


class MachineStatus(str, enum.Enum):
    IDLE = "idle"                  # no disk assigned
    PROVISIONED = "provisioned"    # clone exists and is mapped on the shared target
    EDITING = "editing"            # a draft master is mapped as its game disk
    ERROR = "error"                # a host operation failed; see last_error


class Machine(Base):
    """
    Client PC. The iSCSI ACL is bound to `initiator_iqn`; the MAC is only
    for DHCP/WoL.

    `clone_zvol`/`iscsi_target_iqn` are recorded at provisioning time; they
    are the source of truth for cleanup even if the config changes later.
    """

    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    mode: Mapped[MachineMode] = mapped_column(_str_enum(MachineMode), default=MachineMode.DISK)
    initiator_iqn: Mapped[str] = mapped_column(String(223), unique=True)
    mac: Mapped[str | None] = mapped_column(String(17), unique=True, default=None)

    game_disk_id: Mapped[int | None] = mapped_column(
        ForeignKey("game_disks.id", ondelete="RESTRICT"), default=None, index=True
    )
    game_disk: Mapped[GameDisk | None] = relationship(
        back_populates="machines", foreign_keys=[game_disk_id]
    )
    # The draft master this machine is filling (status `editing`); at most
    # one editor per disk.
    editing_disk_id: Mapped[int | None] = mapped_column(
        ForeignKey("game_disks.id", ondelete="RESTRICT"), default=None, unique=True
    )
    editing_disk: Mapped[GameDisk | None] = relationship(
        back_populates="editor", foreign_keys=[editing_disk_id]
    )

    # Boot Mode: the OS image (kind `os`) and this machine's writeback of it.
    # It follows the image's active version (no pin yet) and is discarded
    # together with the game writeback.
    os_disk_id: Mapped[int | None] = mapped_column(
        ForeignKey("game_disks.id", ondelete="RESTRICT"), default=None, index=True
    )
    os_disk: Mapped[GameDisk | None] = relationship(foreign_keys=[os_disk_id])
    os_clone_zvol: Mapped[str | None] = mapped_column(String(255), default=None)
    os_clone_snapshot: Mapped[str | None] = mapped_column(String(320), default=None)

    # Game disk letter on the PC (Disk Mode; Boot Mode is always D:).
    drive_letter: Mapped[str] = mapped_column(String(1), default="D", server_default="D")

    status: Mapped[MachineStatus] = mapped_column(
        _str_enum(MachineStatus), default=MachineStatus.IDLE
    )
    last_error: Mapped[str | None] = mapped_column(Text, default=None)

    clone_zvol: Mapped[str | None] = mapped_column(String(255), default=None)
    clone_snapshot: Mapped[str | None] = mapped_column(String(320), default=None)
    iscsi_target_iqn: Mapped[str | None] = mapped_column(String(223), default=None)

    # Snapshot pin (ggRock Advanced → Game Image Snapshot): the version of the
    # game disk this machine runs instead of the active one; None follows it.
    pinned_snapshot: Mapped[str | None] = mapped_column(String(64), default=None)

    # Writeback lifecycle (ggRock model): the server discards the writeback
    # after every disconnect unless keep_writeback is set.
    keep_writeback: Mapped[bool] = mapped_column(Boolean, default=False)
    # The client wrote (was connected) since the clone was made; a clean
    # clone is never discarded again.
    writeback_dirty: Mapped[bool] = mapped_column(Boolean, default=False)
    # Last iSCSI session state seen in LIO (None = never read) and since when.
    session_active: Mapped[bool | None] = mapped_column(Boolean, default=None)
    session_changed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), default=None)
    # Windows boot time reported by the agent; a newer value means a new boot.
    booted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), default=None)

    # Reported by ggnet-agent in its heartbeat; never used for provisioning.
    last_seen_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), default=None)
    agent_version: Mapped[str | None] = mapped_column(String(32), default=None)
    reported_iqn: Mapped[str | None] = mapped_column(String(223), default=None)
    iscsi_connected: Mapped[bool | None] = mapped_column(Boolean, default=None)
    # The agent's last heartbeat said its service is stopping (Windows shutting
    # down): the PC is offline now, not only after missed heartbeats.
    agent_stopped: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    reported_drive_letter: Mapped[str | None] = mapped_column(String(1), default=None)
    # Inventory from the agent: the network it reaches the server on and the
    # hardware (ggRock's IP and Link Speed columns, Hardware tab). JSON text.
    # Shutdown / reboot for the agent: handed out once in the next heartbeat
    # answer, and dropped when older than POWER_COMMAND_TTL (app.services.power).
    pending_command: Mapped[str | None] = mapped_column(String(16), default=None)
    pending_command_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), default=None)
    reported_ip: Mapped[str | None] = mapped_column(String(45), default=None)
    reported_mac: Mapped[str | None] = mapped_column(String(17), default=None)
    link_speed_mbps: Mapped[int | None] = mapped_column(Integer, default=None)
    hardware: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=_now, onupdate=_now
    )

    @property
    def hardware_info(self) -> dict | None:
        return json.loads(self.hardware) if self.hardware else None

    @property
    def target_snapshot_path(self) -> str | None:
        """The version this machine is cloned from: its pin, else the disk's active one."""
        if self.game_disk is None or not self.game_disk.published:
            return None
        if self.pinned_snapshot:
            return f"{self.game_disk.zvol_path}@{self.pinned_snapshot}"
        return self.game_disk.snapshot_path

    @property
    def os_snapshot_path(self) -> str | None:
        """The OS version a Boot Mode machine is cloned from: the image's active one."""
        if self.mode is not MachineMode.BOOT or self.os_disk is None:
            return None
        return self.os_disk.snapshot_path

    @property
    def outdated(self) -> bool:
        """A clone was made from another snapshot than the one it should run."""
        game = (
            self.clone_snapshot is not None
            and self.target_snapshot_path is not None
            and self.clone_snapshot != self.target_snapshot_path
        )
        os_ = (
            self.os_clone_snapshot is not None
            and self.os_snapshot_path is not None
            and self.os_clone_snapshot != self.os_snapshot_path
        )
        return game or os_


class AppSetting(Base):
    """
    Settings the admin changes in the web UI (Settings page), one JSON value
    per key. Settings that need a restart stay in config.toml.
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now, onupdate=_now)
