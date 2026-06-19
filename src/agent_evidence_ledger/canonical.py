"""The pinned deterministic encoding (locked by test_known_entry_known_digest).

canonical(record) -> bytes serializes every hashed field EXCEPT `hash`, with the
`kind` discriminator rendered as its .value string. The encoding is fully pinned
so the hash is reproducible across runs and machines. Changing the encoding turns
the known-digest lock test RED.
"""
import dataclasses
import hashlib
import json

from .records import RecordKind


def canonical(record) -> bytes:
    """Deterministic, machine-independent serialization of a record's hashed
    fields. Pinned encoding (DO NOT change without re-pinning the digest test):
      1. ordered dict of EVERY field except `hash`, `kind` rendered as .value.
      2. json.dumps(d, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
      3. .encode('utf-8')
    sort_keys makes field order irrelevant; separators removes whitespace;
    ensure_ascii makes the byte stream identical across locales/machines.
    """
    d = {}
    for f in dataclasses.fields(record):
        if f.name == "hash":
            continue
        value = getattr(record, f.name)
        if isinstance(value, RecordKind):
            value = value.value
        d[f.name] = value
    text = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return text.encode("utf-8")


def entry_hash(record, prev_hash: str) -> str:
    """sha256( canonical(record) + b'|' + prev_hash.encode('utf-8') ).hexdigest()

    The b'|' domain-separator prevents a canonical-bytes/prev-hash boundary
    ambiguity (so two different (canonical, prev) splits cannot collide).
    """
    payload = canonical(record) + b"|" + prev_hash.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
