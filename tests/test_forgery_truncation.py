"""Group C class 5 — truncation (CENTERPIECE). Caught only by the head anchor."""
import _pathsetup  # noqa: F401

from agent_evidence_ledger import Ledger, verify
from _helpers import build_valid_chain


def test_dropped_tail_is_caught_as_truncation():
    led, recs = build_valid_chain()
    anchor = led.head_anchor()  # captured BEFORE the drop (head, count=4)
    # Drop the last 2 records. The remaining 2-record chain is internally
    # consistent: a naive verifier passes it.
    truncated = recs[:2]
    v = verify(truncated, expected_head=anchor)
    assert v.valid is False
    assert v.forgery_class == "truncation"
    # index names the anchored count (the position of the missing tail).
    assert v.index == anchor[1]
    assert v.index == 4


def test_naive_verify_accepts_truncated_chain():
    # DEFEAT proof: WITHOUT the anchor, the truncated chain verifies VALID.
    _led, recs = build_valid_chain()
    truncated = recs[:2]
    v = verify(truncated)  # no expected_head
    assert v.valid is True
    assert v.forgery_class is None


def test_fork_substitution_caught_by_anchor():
    # A wholesale alternate valid chain with a different head, anchored against
    # the original head, collapses into the same truncation mechanism.
    orig, _recs = build_valid_chain()
    anchor = orig.head_anchor()

    fork = Ledger()
    fork.append_decision(authority_tier=2, action_id="x-0", payload="alt 0")
    fork.append_decision(authority_tier=2, action_id="x-1", payload="alt 1")
    fork.append_decision(authority_tier=2, action_id="x-2", payload="alt 2")
    fork.append_decision(authority_tier=2, action_id="x-3", payload="alt 3")

    v = verify(fork.records, expected_head=anchor)
    assert v.valid is False
    assert v.forgery_class == "truncation"
