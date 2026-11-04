from __future__ import annotations

import secrets
import time

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

PREFIXES = {
    "session": "sess_",
    "question": "q_",
    "answer": "ans_",
    "plan": "plan_",
    "step": "step_",
    "preparation": "prep_",
    "job": "job_",
    "feedback": "fb_",
    "observation": "obs_",
    "revision": "rev_",
    "recipe": "recipe_",
    "tasting": "taste_",
    "adjustment": "adj_",
    "media": "media_",
    "reference": "ref_",
    "outcome": "out_",
    "qa": "qa_",
    "request": "req_",
}


def _encode(value: int, length: int) -> str:
    chars = []
    for _ in range(length):
        chars.append(_ALPHABET[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def ulid_like() -> str:
    timestamp_ms = int(time.time() * 1000)
    random_part = secrets.randbits(80)
    return _encode(timestamp_ms, 10) + _encode(random_part, 16)


def new_id(kind: str) -> str:
    return PREFIXES[kind] + ulid_like()