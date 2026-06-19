"""Zero-install, defeat-first demo. Run: python3 -m agent_evidence_ledger.demo

Builds one valid ledger, then stages each forgery: show the naive verifier ACCEPT
(where the chain is blind), then the governed verify CATCH it with class + index.
Every scene self-checks; a mismatch exits 2 (fail closed). No network, no install.
"""
import dataclasses
import os
import sys

# Zero-install sys.path injection so the demo runs from a fresh clone.
_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from agent_evidence_ledger import Ledger, verify  # noqa: E402


_FAILED = []


def _check(scene, condition, expectation):
    mark = "ok" if condition else "MISMATCH"
    print("    [%s] %s" % (mark, expectation))
    if not condition:
        _FAILED.append(scene)


def _edit(record, **changes):
    return dataclasses.replace(record, **changes)


def _rethread(records):
    from agent_evidence_ledger.records import GENESIS_PREV_HASH
    from agent_evidence_ledger.canonical import entry_hash

    out = []
    prev = GENESIS_PREV_HASH
    for rec in records:
        r = dataclasses.replace(rec, prev_hash=prev, hash="0" * 64)
        h = entry_hash(r, prev)
        out.append(dataclasses.replace(r, hash=h))
        prev = h
    return out


def _build_base():
    """A 4-decision chain + a veto + a demote. Synthetic, generic payloads."""
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="act-0", payload="approve disbursement batch")
    led.append_decision(authority_tier=2, action_id="act-1", payload="set exposure to 2 percent")
    led.append_decision(authority_tier=2, action_id="act-2", payload="rebalance toward hedge")
    led.append_decision(authority_tier=2, action_id="act-3", payload="close out residual lot")
    return led


def scene_0_valid():
    print("Scene 0 - VALID chain")
    led = _build_base()
    led.append_veto(authority_tier=3, vetoes_action_id="act-9", reason="risk ceiling breached")
    led.append_demote(from_tier=2, to_tier=1, drift_signal_id="drift-ext-7")
    anchor = led.head_anchor()
    receipts = frozenset({"act-0", "act-1", "act-2", "act-3", "act-9"})
    v = verify(led.records, expected_head=anchor, executed_action_ids=receipts)
    print("    head=%s count=%d" % (v.head[:16] + "...", v.count))
    print("    reg_cite: %s" % v.reg_cite)
    _check("0", v.valid is True and v.forgery_class is None, "valid chain verifies clean")


def scene_1_edit():
    print("Scene 1 - EDIT (mutate an entry in place)")
    led = _build_base()
    recs = list(led.records)
    recs[1] = _edit(recs[1], payload="set exposure to 99 percent")
    v = verify(recs)
    print("    verdict: valid=%s class=%s index=%s" % (v.valid, v.forgery_class, v.index))
    _check("1", v.valid is False and v.forgery_class == "edit" and v.index == 1,
           "edit caught at index 1")


def scene_2_delete():
    print("Scene 2 - DELETE (remove an interior record)")
    led = _build_base()
    recs = list(led.records)
    del recs[2]
    v = verify(recs)
    print("    verdict: valid=%s class=%s index=%s" % (v.valid, v.forgery_class, v.index))
    _check("2", v.valid is False and v.forgery_class == "delete" and v.index == 3,
           "delete caught at successor index 3")


def scene_3_reorder():
    print("Scene 3 - REORDER (swap two positions, re-thread links)")
    led = _build_base()
    recs = list(led.records)
    recs[1], recs[2] = recs[2], recs[1]
    recs = _rethread(recs)
    v = verify(recs)
    print("    verdict: valid=%s class=%s index=%s" % (v.valid, v.forgery_class, v.index))
    _check("3", v.valid is False and v.forgery_class == "reorder" and v.index == 1,
           "reorder caught at index 1")


def scene_4_bypass():
    print("Scene 4 - BYPASS (an action executed with no entry written)")
    led = _build_base()
    recs = list(led.records)
    # First: the chain ALONE accepts it - absence is invisible to the chain.
    blind = verify(recs)
    print("    chain alone (no receipts): valid=%s  <- absence is invisible" % blind.valid)
    _check("4a", blind.valid is True, "chain alone is blind to the off-book action")
    executed = frozenset({"act-0", "act-1", "act-2", "act-3", "act-OFFBOOK"})
    v = verify(recs, expected_head=led.head_anchor(), executed_action_ids=executed)
    print("    coverage cross-check: valid=%s class=%s index=%s"
          % (v.valid, v.forgery_class, v.index))
    _check("4b", v.valid is False and v.forgery_class == "bypass",
           "bypass caught by coverage cross-check")


def scene_5_truncation():
    print("Scene 5 - TRUNCATION (drop the tail) - THE MOAT")
    led = _build_base()
    anchor = led.head_anchor()
    recs = list(led.records)
    truncated = recs[:2]
    # THE DEFEAT: a naive verifier (no anchor) accepts the dropped tail.
    naive = verify(truncated)
    print("    naive verify (no anchor): valid=%s  <- THE DEFEAT" % naive.valid)
    _check("5a", naive.valid is True, "naive verifier accepts the truncated chain")
    v = verify(truncated, expected_head=anchor)
    print("    anchored verify: valid=%s class=%s index=%s"
          % (v.valid, v.forgery_class, v.index))
    _check("5b", v.valid is False and v.forgery_class == "truncation" and v.index == anchor[1],
           "truncation caught by the external head anchor")
    print("    moat: a hash chain proves the entries it CONTAINS are intact; it is")
    print("          blind to a decision never written (bypass) or dropped from the")
    print("          end (truncation). The external anchor closes that gap.")


def scene_6_veto_demote():
    print("Scene 6 - VETO + DEMOTE in action (ordering is the control)")
    led = Ledger()
    led.append_decision(authority_tier=2, action_id="act-0", payload="stage order")
    veto = led.append_veto(authority_tier=3, vetoes_action_id="act-1", reason="block this")
    action = led.append_decision(authority_tier=2, action_id="act-1", payload="execute order")
    led.append_demote(from_tier=2, to_tier=1, drift_signal_id="drift-ext-3")
    after = led.append_decision(authority_tier=1, action_id="act-2", payload="reduced-authority action")
    v = verify(led.records, expected_head=led.head_anchor())
    print("    veto at seq %d precedes vetoed action at seq %d" % (veto.seq, action.seq))
    print("    decision after demote carries lower tier: %d" % after.authority_tier)
    _check("6a", v.valid is True, "veto+demote chain verifies clean")
    _check("6b", veto.seq + 1 == action.seq, "veto ordered before the action (provable)")
    _check("6c", after.authority_tier == 1, "post-demote decision carries the lower tier")
    # Forge the post-demote decision to claim the higher tier again -> caught as edit.
    recs = list(led.records)
    recs[4] = _edit(recs[4], authority_tier=2)
    forged = verify(recs)
    print("    forged 'still high tier' later decision: class=%s index=%s"
          % (forged.forgery_class, forged.index))
    _check("6d", forged.forgery_class == "edit" and forged.index == 4,
           "forged higher-tier later decision caught as edit")


def main():
    scenes = [
        scene_0_valid, scene_1_edit, scene_2_delete, scene_3_reorder,
        scene_4_bypass, scene_5_truncation, scene_6_veto_demote,
    ]
    print("=" * 64)
    print("agent-evidence-ledger demo - defeat-first, self-checking")
    print("=" * 64)
    for s in scenes:
        s()
        print("")
    print("-" * 64)
    if _FAILED:
        print("DEMO FAILED - a control regressed in scene(s): %s" % ", ".join(_FAILED))
        return 2
    print("All scenes passed their expected verdict.")
    print("The test IS the control - run ./run_tests.sh")
    print("Set _CHECK_TRUNCATION=False in verify.py and")
    print("test_polarity_truncation_strip_makes_it_pass turns RED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
