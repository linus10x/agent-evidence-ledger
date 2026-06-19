"""Shared chain builders for the forgery tests.

These construct a known-good ledger and the precise forged variants the plan
describes, so each forgery test trips exactly its own detection check.
"""
import _pathsetup  # noqa: F401
import dataclasses

from agent_evidence_ledger import (
    Ledger,
    DecisionEntry,
    canonical,
)
from agent_evidence_ledger.canonical import entry_hash


def build_valid_chain():
    """A 4-decision chain. Returns (ledger, records_list)."""
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="act-0", payload="open position A")
    led.append_decision(authority_tier=2, action_id="act-1", payload="size to 2pct")
    led.append_decision(authority_tier=2, action_id="act-2", payload="hedge with B")
    led.append_decision(authority_tier=2, action_id="act-3", payload="close position A")
    return led, list(led.records)


def replace(record, **changes):
    """Return a copy of a frozen record with fields changed (no rehash)."""
    return dataclasses.replace(record, **changes)


def rethread(records):
    """Recompute prev_hash + hash for the whole list in its CURRENT order,
    preserving each record's existing seq value. Used by the reorder fixture:
    after swapping list positions, links/continuity are made consistent so only
    the seq-vs-position invariant breaks."""
    from agent_evidence_ledger.records import GENESIS_PREV_HASH

    out = []
    prev = GENESIS_PREV_HASH
    for rec in records:
        relinked = dataclasses.replace(rec, prev_hash=prev, hash="0" * 64)
        h = entry_hash(relinked, prev)
        relinked = dataclasses.replace(relinked, hash=h)
        out.append(relinked)
        prev = h
    return out
