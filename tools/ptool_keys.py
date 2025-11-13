#!/usr/bin/env python3
import base64
import json
from pathlib import Path


def b64url_decode(s: str) -> bytes:
    s = s.strip()
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()


def load_json(path: str) -> dict:
    p = Path(path)
    with p.open('r', encoding='utf-8') as f:
        return json.load(f)


def get_field(d: dict, path: str):
    # path like 'ed25519.private' or 'keys.0.private'
    cur = d
    for part in path.split('.'):
        if part.isdigit():
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def load_b64url_from_keyfile(path: str, field: str) -> bytes:
    d = load_json(path)
    val = get_field(d, field)
    if isinstance(val, dict):
        raise ValueError('field resolves to object; need base64 string')
    return b64url_decode(val)
