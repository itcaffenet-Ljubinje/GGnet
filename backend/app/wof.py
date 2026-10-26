"""
Files Windows keeps compressed (Compact OS / WOF): their data lives in a
`WofCompressedData` stream, and ntfs-3g without its system-compression plugin
shows them as unsupported reparse points ("unsupported reparse tag
0x80000017"). Inbox drivers in an image's driver store usually are such
files, so the hardware scan (app.services.scan) decompresses them here with
wimlib's decompressors (libwim, from wimtools; the same LZX and XPRESS
formats).

The stream is a chunk table followed by the chunks: the file is cut into
chunks of 4, 8, 16 KiB (XPRESS) or 32 KiB (LZX); the table holds the offset
of every chunk but the first (4 bytes each, 8 for a file over 4 GiB),
counted from the end of the table. A chunk whose compressed size equals its
size is stored as it is.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import struct

WOF_TAG = 0x80000017
_FILE_PROVIDER = 2
# WOF algorithm -> (wimlib compression type, chunk size)
_XPRESS, _LZX = 1, 2
ALGORITHMS = {0: (_XPRESS, 4096), 1: (_LZX, 32768), 2: (_XPRESS, 8192), 3: (_XPRESS, 16384)}


class WofError(Exception):
    pass


def wof_algorithm(reparse: bytes) -> int | None:
    """The WOF algorithm of a file from its reparse point data; None when it is not a WOF file."""
    if len(reparse) < 24:
        return None
    tag, _length, _reserved = struct.unpack_from("<IHH", reparse, 0)
    _wof_version, provider, _file_version, algorithm = struct.unpack_from("<IIII", reparse, 8)
    if tag != WOF_TAG or provider != _FILE_PROVIDER or algorithm not in ALGORITHMS:
        return None
    return algorithm


class _Libwim:
    def __init__(self):
        name = ctypes.util.find_library("wim") or "libwim.so.15"
        try:
            self.lib = ctypes.CDLL(name)
        except OSError as e:
            raise WofError(f"libwim is not installed (wimtools): {e}") from e
        self.lib.wimlib_create_decompressor.argtypes = [ctypes.c_int, ctypes.c_size_t,
                                                        ctypes.POINTER(ctypes.c_void_p)]
        self.lib.wimlib_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                                               ctypes.c_size_t, ctypes.c_void_p]
        self.lib.wimlib_free_decompressor.argtypes = [ctypes.c_void_p]

    def decompress(self, ctype: int, chunk_size: int, chunks: list[tuple[bytes, int]]) -> bytes:
        handle = ctypes.c_void_p()
        if self.lib.wimlib_create_decompressor(ctype, chunk_size, ctypes.byref(handle)) != 0:
            raise WofError("cannot create the decompressor")
        try:
            out = bytearray()
            for data, size in chunks:
                if len(data) == size:
                    out += data
                    continue
                buf = ctypes.create_string_buffer(size)
                src = ctypes.create_string_buffer(data, len(data))
                if self.lib.wimlib_decompress(src, len(data), buf, size, handle) != 0:
                    raise WofError(f"chunk {len(out) // chunk_size} is corrupt")
                out += buf.raw
            return bytes(out)
        finally:
            self.lib.wimlib_free_decompressor(handle)


_LIB: _Libwim | None = None


def chunks(stream: bytes, size: int, chunk_size: int) -> list[tuple[bytes, int]]:
    """The stream's chunks as (data, uncompressed size)."""
    count = max(1, -(-size // chunk_size))
    entry = 8 if size > 0xFFFFFFFF else 4
    table = (count - 1) * entry
    if table > len(stream):
        raise WofError("the chunk table is longer than the stream")
    starts = [0] + [struct.unpack_from("<Q" if entry == 8 else "<I", stream, i * entry)[0]
                    for i in range(count - 1)]
    ends = starts[1:] + [len(stream) - table]
    out = []
    for i, (start, end) in enumerate(zip(starts, ends)):
        if not 0 <= start <= end <= len(stream) - table:
            raise WofError("the chunk table is corrupt")
        out.append((stream[table + start:table + end], min(chunk_size, size - i * chunk_size)))
    return out


def decompress(stream: bytes, size: int, algorithm: int) -> bytes:
    """A WOF file's data from its WofCompressedData stream and its size."""
    global _LIB
    ctype, chunk_size = ALGORITHMS[algorithm]
    if size == 0:
        return b""
    parts = chunks(stream, size, chunk_size)
    if all(len(data) == n for data, n in parts):          # all stored as they are
        return b"".join(data for data, _ in parts)
    _LIB = _LIB or _Libwim()
    return _LIB.decompress(ctype, chunk_size, parts)


def data_size(ntfsinfo_output: str) -> int | None:
    """The size of the unnamed $DATA attribute in `ntfsinfo -F <file>` output."""
    for block in ntfsinfo_output.split("Dumping attribute ")[1:]:
        if not block.startswith("$DATA") or "Attribute name:" in block:
            continue
        for line in block.splitlines():
            if line.strip().lower().startswith("data size:"):
                try:
                    return int(line.split(":", 1)[1].split()[0])
                except (ValueError, IndexError):
                    return None
    return None


def run_bytes(cmd: list[str], timeout: int = 120) -> tuple[bool, bytes]:
    """A command's binary stdout (ntfscat)."""
    import subprocess

    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return False, b""
    return p.returncode == 0, p.stdout


def read_file(partition: str, path: str, run=run_bytes) -> bytes | None:
    """
    A file of an NTFS partition (mounted read-only or not mounted), WOF
    compressed or not, read with ntfscat/ntfsinfo; `path` is relative to the
    volume root. None when it cannot be read.
    """
    ok, reparse = run(["ntfscat", "-f", "-a", "0xc0", partition, path])
    algorithm = wof_algorithm(reparse) if ok else None
    if algorithm is None:
        ok, data = run(["ntfscat", "-f", partition, path])
        return data if ok else None
    ok, info = run(["ntfsinfo", "-f", "-F", path, partition])
    size = data_size(info.decode("utf-8", "replace")) if ok else None
    ok, stream = run(["ntfscat", "-f", "-a", "0x80", "-n", "WofCompressedData", partition, path])
    if size is None or not ok:
        return None
    try:
        return decompress(stream, size, algorithm)
    except WofError:
        return None


def pe_hashes(data: bytes) -> list[bytes]:
    """The Authenticode SHA-256 and SHA-1 of a PE file (as catalogs list them); [] when it is not one."""
    import hashlib

    try:
        if data[:2] != b"MZ":
            return []
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe:pe + 4] != b"PE\0\0":
            return []
        opt = pe + 24
        magic = struct.unpack_from("<H", data, opt)[0]
        checksum = opt + 64
        cert_dir = opt + (144 if magic == 0x20B else 128)
        cert_off, _ = struct.unpack_from("<II", data, cert_dir)
    except struct.error:
        return []
    end = cert_off if 0 < cert_off <= len(data) else len(data)
    out = []
    for algo in (hashlib.sha256, hashlib.sha1):
        h = algo()
        h.update(data[:checksum])
        h.update(data[checksum + 4:cert_dir])
        h.update(data[cert_dir + 8:end])
        out.append(h.digest())
    return out


def embedded_signature(data: bytes) -> bool:
    """Whether a PE file carries its own signature (a certificate table)."""
    try:
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        opt = pe + 24
        magic = struct.unpack_from("<H", data, opt)[0]
        _, size = struct.unpack_from("<II", data, opt + (144 if magic == 0x20B else 128))
        return size > 0
    except struct.error:
        return False
