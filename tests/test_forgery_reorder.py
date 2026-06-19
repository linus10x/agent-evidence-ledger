"""Group C class 3 — reorder. Caught by the sequence (seq-vs-position) check.

Fixture-construction contract (from .plan.md §2.4):
take a valid 4-record chain, swap the LIST POSITIONS of the records at index 1
and 2, then re-thread prev_hash+hash for the new order so links/continuity hold.
The giveaway left behind is that the record now at position 1 carries seq == 2.
_check_sequence fires `reorder`. This keeps reorder mapped to exactly one
strip-point (it must NOT trip the edit or delete checks first).
"""
import _pathsetup  # noqa: F401

from agent_evidence_ledger import verify
from _helpers import build_valid_chain, rethread


def test_swap_positions_is_caught_as_reorder():
    _led, recs = build_valid_chain()
    # Swap adjacent positions 1 and 2 (seq values stay attached to their records).
    recs[1], recs[2] = recs[2], recs[1]
    # Re-thread links so continuity + edit checks pass for the swapped order;
    # only the seq-vs-position invariant is left broken.
    recs = rethread(recs)
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "reorder"
    # First out-of-order position: position 1 now carries seq 2.
    assert v.index == 1
