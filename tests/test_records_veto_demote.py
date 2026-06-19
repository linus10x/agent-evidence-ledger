"""Group D — sovereign-veto + auto-demote ordered record types."""
import _pathsetup  # noqa: F401

from agent_evidence_ledger import Ledger, verify
from agent_evidence_ledger.records import RecordKind
from _helpers import replace, rethread


def test_veto_ordered_before_action_is_provable():
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="act-0", payload="open")
    veto = led.append_veto(authority_tier=3, vetoes_action_id="act-2", reason="block")
    action = led.append_decision(authority_tier=2, action_id="act-2", payload="trade")
    # The veto at seq N precedes the vetoed action at seq N+1, readable from chain.
    assert veto.seq + 1 == action.seq
    assert veto.vetoes_action_id == action.action_id
    v = verify(led.records, expected_head=led.head_anchor())
    assert v.valid is True


def test_veto_position_cannot_be_forged():
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="act-0", payload="open")
    led.append_veto(authority_tier=3, vetoes_action_id="act-2", reason="block")
    led.append_decision(authority_tier=2, action_id="act-2", payload="trade")
    recs = list(led.records)
    # Move the veto to AFTER the action it vetoes (swap positions 1 and 2),
    # re-thread links so only ordering breaks. Caught as reorder.
    recs[1], recs[2] = recs[2], recs[1]
    recs = rethread(recs)
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "reorder"


def test_demote_record_is_ordered_in_chain():
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="act-0", payload="open")
    dem = led.append_demote(from_tier=2, to_tier=1, drift_signal_id="drift-9")
    assert dem.from_tier == 2
    assert dem.to_tier == 1
    assert dem.to_tier < dem.from_tier
    assert dem.drift_signal_id == "drift-9"
    assert dem.kind == RecordKind.DEMOTE
    assert dem.seq == 1
    v = verify(led.records, expected_head=led.head_anchor())
    assert v.valid is True


def test_decisions_after_demote_carry_lower_tier():
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="act-0", payload="open")
    led.append_demote(from_tier=2, to_tier=1, drift_signal_id="drift-9")
    after = led.append_decision(authority_tier=1, action_id="act-1", payload="reduce")
    assert after.authority_tier == 1
    recs = list(led.records)
    # Forge the later decision to claim the higher tier again -> changes its
    # canonical bytes, stored hash no longer matches -> caught as edit.
    recs[2] = replace(recs[2], authority_tier=2)
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "edit"
    assert v.index == 2


def test_demote_is_record_only_not_detection():
    led = Ledger()
    # The API exposes NO drift-detection entrypoint. Boundary asserted by
    # absence of a detector method AND presence of the supplied-signal field.
    assert not hasattr(led, "detect_drift")
    assert not hasattr(led, "drift_detector")
    dem = led.append_demote(from_tier=2, to_tier=1, drift_signal_id="ext-signal-1")
    # The signal is consumed and recorded, never computed here.
    assert dem.drift_signal_id == "ext-signal-1"
