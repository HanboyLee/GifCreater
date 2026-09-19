# -*- coding: utf-8 -*-
"""API Key 密文存储（与 JSON 设置、sqlite 收藏分离）。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Protocol


class SecretStoreError(Exception):
    pass


class Protector(Protocol):
    def protect(self, data: bytes) -> bytes: ...
    def unprotect(self, data: bytes) -> bytes: ...


class FakeProtector:
    """单测用，禁止当作用户明文 JSON。"""

    PREFIX = b"GC1:"

    def protect(self, data: bytes) -> bytes:
        return self.PREFIX + bytes(b ^ 0x5A for b in data)

    def unprotect(self, data: bytes) -> bytes:
        if not data.startswith(self.PREFIX):
            raise SecretStoreError("密文格式无效")
        payload = data[len(self.PREFIX) :]
        return bytes(b ^ 0x5A for b in payload)


class DpapiProtector:
    def protect(self, data: bytes) -> bytes:
        return _dpapi_protect(data)

    def unprotect(self, data: bytes) -> bytes:
        return _dpapi_unprotect(data)


def _dpapi_protect(data: bytes) -> bytes:
    if sys.platform != "win32":
        raise SecretStoreError("需要 Windows DPAPI")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    in_buf = ctypes.create_string_buffer(data, len(data))
    in_blob = DATA_BLOB(len(data), in_buf)
    out_blob = DATA_BLOB()
    if not crypt32.CryptProtectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise SecretStoreError("DPAPI 加密失败")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    if sys.platform != "win32":
        raise SecretStoreError("需要 Windows DPAPI")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    in_buf = ctypes.create_string_buffer(data, len(data))
    in_blob = DATA_BLOB(len(data), in_buf)
    out_blob = DATA_BLOB()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise SecretStoreError("DPAPI 解密失败")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)


def default_protector() -> Protector:
    if sys.platform == "win32":
        return DpapiProtector()
    return FakeProtector()


class SecretStore:
    def __init__(self, path: Optional[Path] = None, protector: Optional[Protector] = None):
        self.path = Path(path) if path else default_secrets_path()
        self.protector = protector or default_protector()

    def save_key(self, key: str) -> None:
        text = (key or "").strip()
        if not text:
            self.clear()
            return
        blob = self.protector.protect(text.encode("utf-8"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(blob)

    def load_key(self) -> str:
        if not self.path.exists():
            return ""
        try:
            raw = self.path.read_bytes()
            return self.protector.unprotect(raw).decode("utf-8")
        except (OSError, SecretStoreError, UnicodeDecodeError):
            return ""

    def has_key(self) -> bool:
        return bool(self.load_key())

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()


def default_secrets_path() -> Path:
    from ..utils.paths import get_default_output_dir

    return Path(get_default_output_dir()) / "gifcreater-secrets.bin"
