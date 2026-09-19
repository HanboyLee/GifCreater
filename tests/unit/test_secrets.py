# -*- coding: utf-8 -*-
import sys

import pytest

from src.gifcreater.config.secrets import (
    FakeProtector,
    SecretStore,
    SecretStoreError,
    default_protector,
)


def test_fake_protector_roundtrip(tmp_path):
    store = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    assert store.has_key() is False
    store.save_key("sk-test-key")
    raw = (tmp_path / "gifcreater-secrets.bin").read_bytes()
    assert b"sk-test-key" not in raw
    assert store.load_key() == "sk-test-key"
    assert store.has_key() is True
    store.clear()
    assert store.has_key() is False


def test_fake_protector_rejects_garbage():
    p = FakeProtector()
    with pytest.raises(SecretStoreError):
        p.unprotect(b"nope")


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI is Windows-only")
def test_dpapi_roundtrip(tmp_path):
    store = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=default_protector())
    store.save_key("hello-dpapi")
    assert b"hello-dpapi" not in (tmp_path / "gifcreater-secrets.bin").read_bytes()
    assert store.load_key() == "hello-dpapi"


def test_empty_key_clears(tmp_path):
    store = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    store.save_key("abc")
    store.save_key("  ")
    assert store.has_key() is False
