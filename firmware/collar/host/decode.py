"""Decode Phase-2 collar CBOR maps produced by firmware/collar/src/frame.c."""

from __future__ import annotations

from typing import Any


def _u8(buf: bytes, i: int) -> tuple[int, int]:
    if i >= len(buf):
        raise ValueError("short CBOR")
    return buf[i], i + 1


def _uint(buf: bytes, i: int) -> tuple[int, int]:
    t, i = _u8(buf, i)
    if t >> 5 != 0:
        raise ValueError("not uint")
    ai = t & 0x1F
    if ai < 24:
        return ai, i
    if ai == 24:
        v, i = _u8(buf, i)
        return v, i
    if ai == 25:
        hi, i = _u8(buf, i)
        lo, i = _u8(buf, i)
        return (hi << 8) | lo, i
    if ai == 26:
        b0, i = _u8(buf, i)
        b1, i = _u8(buf, i)
        b2, i = _u8(buf, i)
        b3, i = _u8(buf, i)
        return (b0 << 24) | (b1 << 16) | (b2 << 8) | b3, i
    raise ValueError("uint too wide")


def _text(buf: bytes, i: int) -> tuple[str, int]:
    t, i = _u8(buf, i)
    if t >> 5 != 3:
        raise ValueError("not text")
    n = t & 0x1F
    if n >= 24 or i + n > len(buf):
        raise ValueError("text too long")
    return buf[i : i + n].decode("utf-8"), i + n


def _f32(buf: bytes, i: int) -> tuple[float, int]:
    import struct

    t, i = _u8(buf, i)
    if t != 0xFA or i + 4 > len(buf):
        raise ValueError("not f32")
    return struct.unpack(">f", buf[i : i + 4])[0], i + 4


def _value(buf: bytes, i: int) -> tuple[Any, int]:
    t = buf[i]
    if t == 0xF4:
        return False, i + 1
    if t == 0xF5:
        return True, i + 1
    if t == 0xF6:
        return None, i + 1
    if t == 0xFA:
        return _f32(buf, i)
    if t >> 5 == 0:
        return _uint(buf, i)
    if t >> 5 == 3:
        return _text(buf, i)
    raise ValueError(f"unsupported CBOR 0x{t:02x}")


def decode_collar_cbor(buf: bytes) -> dict[str, Any]:
    if not buf or (buf[0] & 0xE0) != 0xA0:
        raise ValueError("not a CBOR map")
    pairs = buf[0] & 0x1F
    i = 1
    out: dict[str, Any] = {}
    for _ in range(pairs):
        key, i = _text(buf, i)
        val, i = _value(buf, i)
        out[key] = val
    return out
