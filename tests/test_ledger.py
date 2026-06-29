"""Group B (part 1) — append API, head/count, authority binding, genesis."""
import _pathsetup  # noqa: F401

from agent_evidence_ledger import Ledger, GENESIS_PREV_HASH, canonical


def test_empty_ledger_head_is_genesis():
    led = Ledger()
    assert led.head == GENESIS_PREV_HASH
    assert led.count == 0


def test_append_assigns_gapfree_seq():
    led = Ledger()
    a = led.append_decision(authority_tier=2, action_id="a", payload="p0")
    b = led.append_decision(authority_tier=2, action_id="b", payload="p1")
    c = led.append_decision(authority_tier=2, action_id="c", payload="p2")
    assert (a.seq, b.seq, c.seq) == (0, 1, 2)
    assert led.count == 3


def test_append_links_prev_hash():
    led = Ledger()
    a = led.append_decision(authority_tier=2, action_id="a", payload="p0")
    b = led.append_decision(authority_tier=2, action_id="b", payload="p1")
    assert a.prev_hash == GENESIS_PREV_HASH
    assert b.prev_hash == a.hash


def test_authority_tier_bound_in_every_decision():
    led = Ledger()
    e = led.append_decision(authority_tier=3, action_id="a", payload="p0")
    assert e.authority_tier == 3
    # tier is inside the hashed canonical bytes
    assert b'"authority_tier":3' in canonical(e)


def test_head_anchor_is_head_and_count():
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="a", payload="p0")
    led.append_decision(authority_tier=2, action_id="b", payload="p1")
    assert led.head_anchor() == (led.head, led.count)
    assert led.head_anchor() == (led.head, 2)
