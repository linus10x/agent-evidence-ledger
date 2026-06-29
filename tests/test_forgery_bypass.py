"""Group C class 4 — bypass. Caught by the coverage cross-check."""
import _pathsetup  # noqa: F401

from agent_evidence_ledger import verify
from _helpers import build_valid_chain


def test_offbook_action_is_caught_as_bypass():
    led, recs = build_valid_chain()
    # An action really executed but no entry was ever written for it.
    executed = frozenset({"act-0", "act-1", "act-2", "act-3", "act-OFFBOOK"})
    v = verify(recs, expected_head=led.head_anchor(), executed_action_ids=executed)
    assert v.valid is False
    assert v.forgery_class == "bypass"
    # The unrecorded action has no position; index names the gap at count.
    assert v.index == len(recs)
