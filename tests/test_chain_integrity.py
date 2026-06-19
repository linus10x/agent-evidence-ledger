"""Group B (part 2) — a valid multi-record chain verifies clean."""
import _pathsetup  # noqa: F401

from agent_evidence_ledger import Ledger, verify


def test_valid_chain_verifies_clean():
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="act-0", payload="open")
    led.append_veto(authority_tier=3, vetoes_action_id="act-1", reason="risk too high")
    led.append_decision(authority_tier=2, action_id="act-2", payload="hedge")
    led.append_demote(from_tier=2, to_tier=1, drift_signal_id="drift-7")
    led.append_decision(authority_tier=1, action_id="act-3", payload="reduce")

    anchor = led.head_anchor()
    receipts = frozenset({"act-0", "act-1", "act-2", "act-3"})
    v = verify(led.records, expected_head=anchor, executed_action_ids=receipts)

    assert v.valid is True
    assert v.forgery_class is None
    assert v.index is None
    assert v.reg_cite
    assert "17a-4" in v.reg_cite
    assert v.head == led.head
    assert v.count == led.count
