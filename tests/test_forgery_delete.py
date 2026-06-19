"""Group C class 2 — interior delete. Caught by the continuity check."""
import _pathsetup  # noqa: F401

from agent_evidence_ledger import verify
from _helpers import build_valid_chain


def test_interior_delete_is_caught_as_delete():
    _led, recs = build_valid_chain()
    # Remove the interior record at seq 2 WITHOUT re-linking. The successor
    # (originally seq 3) still carries prev_hash pointing at the removed record.
    del recs[2]
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "delete"
    # Detected at the successor whose prev_hash no longer matches its predecessor.
    # After deletion the successor sits at list position 2 and carries seq 3.
    assert v.index == 3
