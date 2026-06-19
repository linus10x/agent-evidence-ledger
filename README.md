# agent-evidence-ledger

A standalone, append-only, tamper-evident ledger of the decisions an autonomous
agent made. Each record binds the decision payload, an ordinal sequence number,
the authority tier the agent held at decision time, and the hash of the
predecessor record into a hash chain. `verify()` returns a structured verdict
that NAMES which of five forgery classes was detected and at which index.

Record integrity only. No PKI, no signatures, no storage backend, no drift
detector. The smallest thing that proves the threat model.

## The one command

```
python3 -m agent_evidence_ledger.demo
```

or `./demo.sh`. Zero install, no network, no make. The demo builds one valid
ledger, then stages each forgery: it first shows a naive verifier ACCEPT the
tampered chain where the chain is blind, then shows the governed `verify()` CATCH
it with the class and the index. It self-checks every scene and exits non-zero if
any control regressed.

Run the tests with `./run_tests.sh` (pytest if present, otherwise a pure-python
fallback runner so a fresh clone with no pytest still gets a real pass or fail).

## The five forgery classes

| Class | What the adversary does | How it is caught |
|-------|-------------------------|------------------|
| edit | mutate an existing record in place | recompute every link from the stored payload and stored prev-hash; the recomputed hash no longer matches the stored hash |
| delete | remove an interior record | walk genesis to head; the successor's stored prev-hash no longer matches its predecessor's hash (chain discontinuity) |
| reorder | swap two records' positions | the ordinal is bound into the hash; the seq value no longer matches its list position |
| bypass | an action executed but no record was written | coverage cross-check: the set of executed action-ids must equal the recorded set; any acted-but-unrecorded id is named |
| truncation | drop the tail (or substitute a fork) | an external head anchor (head hash plus count) captured at a checkpoint; the recomputed head or count no longer matches the anchor |

## The moat

A hash chain proves the records it contains were not altered. It proves nothing
about a decision that was never written down, or one silently dropped from the
end. A regulated decision ledger therefore has to bind a gap-free sequence and an
external head anchor, and put the ledger write on the critical path of the
action. It also has to carry the veto and the demotion in the same chain, because
what an examiner needs is not the decision in isolation but its order relative to
who was allowed to make it.

Two record types live in the same chain for exactly this reason:

- A sovereign-veto record proves a higher authority blocked a decision, and
  proves the veto's timing relative to the action (the veto at seq N precedes the
  action at seq N+1). In a separate tool an adversary forges the ordering.
- An auto-demote record records that the agent was demoted to a lower authority
  tier on an externally-supplied drift signal. Because the authority tier is
  bound into every decision record, you can prove that after the demotion at seq
  N, every later decision carried the lower tier.

The primitive RECORDS the demotion. It does not detect drift. The drift signal is
supplied from outside; authority-at-decision-time is the invariant this primitive
proves.

## What it verifies

```
from agent_evidence_ledger import Ledger, verify

led = Ledger()
led.append_decision(authority_tier=2, action_id="act-0", payload="open position")
led.append_veto(authority_tier=3, vetoes_action_id="act-1", reason="risk ceiling")
led.append_demote(from_tier=2, to_tier=1, drift_signal_id="drift-7")
led.append_decision(authority_tier=1, action_id="act-2", payload="reduce")

anchor = led.head_anchor()                       # (head_hash, count) checkpoint
receipts = frozenset({"act-0", "act-1", "act-2"})
v = verify(led.records, expected_head=anchor, executed_action_ids=receipts)
# v.valid, v.forgery_class, v.index, v.detail, v.reg_cite, v.head, v.count
```

`verify()` never raises. Malformed or unknown input returns a structured verdict
with `forgery_class="invalid"` (distinct from the five named classes, so a
reviewer can tell "we caught a forgery" from "we refused garbage"). A control
that raises can be swallowed by a caller and resolve to "proceed", so it fails
closed instead.

## The head anchor is held outside the chain

`head_anchor()` returns `(head_hash, count)`. It is a return value, not a record
inside the chain. An anchor stored as an interior record would itself be subject
to truncation (drop the tail including the anchor). Its whole job is to be held
outside the chain, attested at a checkpoint, and passed back into
`verify(expected_head=...)`. Without the anchor, `verify()` runs in the naive mode
that the truncation class defeats. That surface is deliberate and documented, and
is proved by `test_naive_verify_accepts_truncated_chain`.

## The test is the control

Each detection check has a documented one-line strip-point: a module-level
boolean in `verify.py` (`_CHECK_EDIT`, `_CHECK_REORDER`, `_CHECK_TRUNCATION`,
each default True) guarding exactly one check. Set one to `False` in source and
exactly one polarity test goes RED while the others stay green. That is the
auditable proof that each check is load-bearing and that the suite asserts the
PRESENCE of detection, not the mere absence of a failure.

```
# in src/agent_evidence_ledger/verify.py
_CHECK_TRUNCATION = False
# then: ./run_tests.sh  -> test_polarity_truncation_strip_makes_it_pass is RED
```

## Reg anchor

Maps to SEC Rule 17a-4(f)(2)(i)(A), 17 CFR 240.17a-4(f)(2)(i)(A), the audit-trail
alternative to WORM added by the 2022 amendment (SEC Release 34-96034): a
complete time-stamped audit trail that records all modifications to and deletions
of a record, enabling re-creation of the original, retained six years per
240.17a-4(a). The cite is carried verbatim in the `REG_CITE` constant and in
every verdict. See CONTROL_STATEMENT.md for the clause-to-check mapping.

## Scope limits

- No PKI, no digital signatures, no key management. Record integrity only.
- No storage backend, no persistence format beyond the in-memory records.
- No real drift detector. Demote is record-only of an externally-supplied signal.
- No replay class and no separate fork class. Fork collapses into the truncation
  head-anchor mechanism. Replay is an auth concern, out of scope.
- No network, no scheduled job, no publish step.

The ledger ingests no external content at runtime. Every input is constructed by
the demo or the tests. A payload string is treated strictly as data: it is
canonically serialized and hashed, never evaluated and never able to select a
code path. This is asserted by `test_payload_is_data_not_instructions`.
