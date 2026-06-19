"""Group C class 1 — edit. Caught by the recompute-link check."""
import _pathsetup  # noqa: F401

from agent_evidence_ledger import verify
from _helpers import build_valid_chain, replace


def test_edit_in_place_is_caught_as_edit():
    _led, recs = build_valid_chain()
    # Mutate entry at seq 1's payload in place; leave its stored hash unchanged.
    recs[1] = replace(recs[1], payload="TAMPERED size to 99pct")
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "edit"
    assert v.index == 1
