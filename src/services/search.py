"""Утилиты семантического поиска (косинусная близость)."""

from __future__ import annotations

import array
import math


def _bytes_to_float_array(b: bytes) -> array.array:
    a = array.array("f")
    a.frombytes(b)
    return a


def cosine_similarity_bytes(a: bytes, b: bytes) -> float:
    va = _bytes_to_float_array(a)
    vb = _bytes_to_float_array(b)
    n = min(len(va), len(vb))
    if n == 0:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(n):
        x = va[i]
        y = vb[i]
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))
