"""Group F — POLARITY proofs. Each detection check is load-bearing.

Mechanism: verify.py carries module-level boolean toggles (default True), each
guarding exactly one check. A polarity test flips a toggle OFF, asserts the
matching forgery now SLIPS THROUGH, restores it, asserts the forgery is caught
again. The toggle IS the documented one-line strip-point.
"""
import _pathsetup  # noqa: F401

import sys

from agent_evidence_ledger import verify
import agent_evidence_ledger.verify  # ensure the submodule is loaded

from _helpers import build_valid_chain, replace, rethread

# The package re-exports the `verify` FUNCTION as agent_evidence_ledger.verify,
# which shadows the submodule attribute. Grab the real module from sys.modules so
# the polarity toggles patch the globals that verify() actually reads.
vmod = sys.modules["agent_evidence_ledger.verify"]


def _make_edit():
    _led, recs = build_valid_chain()
    recs[1] = replace(recs[1], payload="TAMPERED")
    return recs


def _make_reorder():
    _led, recs = build_valid_chain()
    recs[1], recs[2] = recs[2], recs[1]
    return rethread(recs)


def _make_truncation():
    led, recs = build_valid_chain()
    return recs[:2], led.head_anchor()


def test_polarity_truncation_strip_makes_it_pass():
    truncated, anchor = _make_truncation()
    # Guard up (default): caught.
    assert verify(truncated, expected_head=anchor).forgery_class == "truncation"
    orig = vmod._CHECK_TRUNCATION
    try:
        vmod._CHECK_TRUNCATION = False
        slipped = verify(truncated, expected_head=anchor)
        # Moat removed: the truncated chain now verifies VALID.
        assert slipped.valid is True
        assert slipped.forgery_class is None
    finally:
        vmod._CHECK_TRUNCATION = orig
    # Restored: caught again.
    assert verify(truncated, expected_head=anchor).forgery_class == "truncation"


def test_polarity_edit_strip_makes_it_pass():
    recs = _make_edit()
    assert verify(recs).forgery_class == "edit"
    orig = vmod._CHECK_EDIT
    try:
        vmod._CHECK_EDIT = False
        slipped = verify(recs)
        assert slipped.forgery_class != "edit"
    finally:
        vmod._CHECK_EDIT = orig
    assert verify(recs).forgery_class == "edit"


def test_polarity_reorder_strip_makes_it_pass():
    recs = _make_reorder()
    assert verify(recs).forgery_class == "reorder"
    orig = vmod._CHECK_REORDER
    try:
        vmod._CHECK_REORDER = False
        slipped = verify(recs)
        assert slipped.forgery_class != "reorder"
    finally:
        vmod._CHECK_REORDER = orig
    assert verify(recs).forgery_class == "reorder"


def test_polarity_each_strip_fells_exactly_one_class():
    # Stripping truncation must NOT change the edit or reorder verdicts.
    edit_recs = _make_edit()
    reorder_recs = _make_reorder()
    orig = vmod._CHECK_TRUNCATION
    try:
        vmod._CHECK_TRUNCATION = False
        assert verify(edit_recs).forgery_class == "edit"
        assert verify(reorder_recs).forgery_class == "reorder"
    finally:
        vmod._CHECK_TRUNCATION = orig
