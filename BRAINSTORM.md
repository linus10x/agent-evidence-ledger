# BRAINSTORM — agent-evidence-ledger (Task 5, step 5.0)

*The spec the architect executes. Output of the 5.0 threat-model brainstorm. Council lens: xai_verifiability — "could a frontier-lab verifiability engineer drop this ONE primitive in and trust that a regulated decision ledger cannot be forged, and that a drifting agent is auto-demoted?"*

## What this primitive is

An append-only, tamper-evident record of the decisions an autonomous agent made. Each
entry binds: the decision payload, an ordinal sequence number, the authority tier the agent
held at decision time, and the hash of the predecessor entry. Spine:

```
H(0) = hash(genesis_record)
H(n) = hash(canonical(entry_n) || H(n-1))
```

`verify()` returns a STRUCTURED verdict (not a bare bool) that NAMES which forgery class was
detected and at which index. Boundary (owner-confirmed 5.0): record-integrity only — no PKI /
signatures, no storage backend, no real drift detector. Simplest thing that proves the threat
model (~200-400 LOC).

## Confirmed forgery-class set (owner-confirmed 5.0)

Five classes. The locked four PLUS truncation. Each gets a RED-first test; each detection
check has a polarity proof (remove the check -> its test goes RED).

| # | Class | What the adversary does | How a hash chain alone fares | Detection mechanism |
|---|-------|------------------------|------------------------------|---------------------|
| 1 | **edit** | mutate an existing entry's content in place | CAUGHT — recomputed H(n) != stored H(n) at that index | recompute every link from stored payload + stored prev-hash |
| 2 | **delete** (interior) | remove an interior entry | CAUGHT — successor's stored prev-hash no longer matches; chain discontinuity | walk genesis->head, assert each entry's prev-hash == predecessor's H |
| 3 | **reorder** | swap two entries' positions | CAUGHT ONLY IF the ordinal is inside the hashed payload | bind `seq` into `canonical(entry)`; assert seq strictly increments by 1 from genesis |
| 4 | **bypass** | an action happened but NO entry was written (off-book decision) | INVISIBLE to the chain — nothing to verify | COVERAGE invariant: monotonic seq with no gaps + every governed action carries a ledger receipt id; verify cross-checks the action-id set against ledger entries and flags any acted-but-unrecorded id |
| 5 | **truncation** (NEW) | drop the tail (last K entries) | INVISIBLE — a valid, internally-consistent shorter chain; a naive verifier accepts it | EXTERNAL HEAD ANCHOR: the agent attests/publishes the head (hash + count) at checkpoint; verify(expected_head) flags recomputed-head-or-count != anchored |

Rationale for ADD (truncation): it is the class a verifiability engineer tries FIRST
("can I just lop off the embarrassing tail?") and the one the chain natively misses. It is
cheap (a stored head hash + count; seq machinery already exists for reorder). It and bypass
together are the moat: **the chain proves the entries it CONTAINS are intact; it is blind to
entries that were never written (bypass) or silently dropped from the end (truncation).**

Dropped/duplicate from the candidate list:
- **fork/replace-chain** (wholesale substitution of an alternate valid chain) — collapses into
  the SAME external-anchor mechanism as truncation (pin genesis + head). Detected by the head
  anchor for free; not a separate demoed class (owner chose truncation-only to keep LOC down).
- **replay** (re-submit a past valid entry as new) — largely a duplicate of the seq-monotonicity
  already required for reorder/truncation; an auth/protocol concern, not record-integrity. Out.

## Why sovereign-veto + auto-demote-on-drift belong in the SAME primitive

Not three tools. Two SPECIAL RECORD TYPES whose entire value depends on being tamper-evidently
ORDERED relative to decisions — which is exactly what the ledger provides and three separate
tools cannot.

- **Sovereign-veto record:** a higher authority blocks/overrides an agent decision. Its value is
  proving the veto's TIMING relative to the action ("the human vetoed at seq N, before the action
  at seq N+1"). In a separate tool an adversary forges the ordering ("the veto came too late").
  Binding it into the same chain makes the veto's position non-forgeable.
- **Auto-demote-on-drift record:** on a drift signal the agent is demoted to a lower authority
  tier. The primitive RECORDS the demotion as an ordered event AND binds `authority_tier` into
  every decision entry, so you can prove "after the demotion at seq N, every later decision
  carried the lower tier." A demotion living in another tool cannot prove the agent did not keep
  acting at full authority. (Owner-confirmed 5.0: RECORD only — the primitive does not DETECT
  drift; it consumes an externally-supplied drift signal. Authority-at-decision-time is the
  invariant; detecting drift is a separate concern.)

Common thread: relative ordering across decisions, vetoes, and demotions is only provable inside
ONE chain. That ordering IS the control.

## The moat sentence (must land on the control page in 5.4)

> "A hash chain proves the entries it contains were not altered. It proves nothing about a
> decision that was never written down, or one silently dropped from the end. A regulated
> decision ledger therefore has to bind a gap-free sequence and an external head anchor, and put
> the ledger write on the critical path of the action — and it has to carry the veto and the
> demotion in the same chain, because what an examiner needs is not the decision in isolation but
> its order relative to who was allowed to make it. The chain is commodity. Deciding that absence
> and ordering are the threats that bite a regulated agent is the judgment."

A frontier model emits `H(n)=hash(decision||H(n-1))` in minutes. It does NOT volunteer that the
chain is blind to absence, nor that veto/demote must share the chain to be provable. That
omission is the moat.

## Candidate reg anchor (confirm in 5.1 vs PRIMARY source — never from memory)

SSOT survey result: the canonical clone `active_regs.yaml` has NO records-preservation /
audit-trail-integrity anchor. One must be ADDED (Task-2 pattern: sourced + verified vs primary).

Best-grounded fit: **SEC Rule 17a-4(f), 17 CFR 240.17a-4(f)** — preservation of records in
electronic form. The 2022 amendment (SEC Release No. 34-96034, compliance 2023) ADDED an
**audit-trail alternative** to the long-standing WORM (write-once-read-many) requirement: a
broker-dealer may preserve records on an electronic system that EITHER (A) maintains records in
a non-rewriteable, non-erasable (WORM) format, OR (B) maintains a complete time-stamped
**audit trail** that records all modifications to and deletions of a record. The audit-trail
alternative is, almost verbatim, a tamper-evident time-ordered record of every change — i.e. a
hash-chained decision ledger. THIS is the precise anchor, tighter than bare WORM.

ARCHITECT MUST: WebFetch the eCFR primary (https://www.ecfr.gov/current/title-17/chapter-II/part-240/section-240.17a-4)
and confirm the exact (f) subsection language for the audit-trail alternative BEFORE adding the
entry. Add `sec_17a_4_f` to the canonical clone with citation + subsection + source + verified
date + framing_confidence, following the `ofac_sdn_screening` schema. Do NOT re-derive the cite
from memory; quote the primary.

## Open questions for the architect (listed, not guessed)

1. Canonical serialization of an entry for hashing — recommend a deterministic, sorted-key,
   ASCII-safe encoding (e.g. `json.dumps(..., sort_keys=True, separators=(',',':'))` UTF-8 ->
   sha256). Architect to pin the exact canonical form and lock it with a test (a known entry ->
   a known digest) so the hash is reproducible across runs/machines.
2. Verdict shape: a frozen dataclass `LedgerVerdict(valid: bool, forgery_class: str|None,
   index: int|None, detail: str, reg_cite: str, head: str, count: int)`. Architect to finalize
   fields; `forgery_class` must be one of the 5 named strings; `valid==False` always names the
   class + index.
3. Head anchor representation for the truncation/coverage checks — recommend `(head_hash, count)`
   captured at a checkpoint and passed to `verify(expected_head=...)`. Architect to decide
   whether the anchor lives as a tiny attestation record or a return value of `append`.
4. Bypass coverage check interface — verify needs the set of action-ids that actually executed
   (the "receipts") to cross-check against recorded entries. Architect to decide how that set is
   supplied to the demo (a small fixture is fine; this is a primitive, not an integration).
5. Authority-tier vocabulary — plain control language, NO branded ladder vocabulary (seat
   blocklist: no A0-A4, no "Autonomy Ladder"). Recommend integer tiers (e.g. tier 2 -> tier 1)
   with plain labels, demotion described as "demoted to a lower authority tier."
6. One-command entrypoint: `python3 -m agent_evidence_ledger.demo` OR `./demo.sh` (zero-install,
   no network, NO make). Test runner zero-install (pytest if present; pure-python fallback per
   the audit-packet pattern).
7. Polarity proof: the centerpiece is truncation (the moat class). Removing the head-anchor check
   must turn the truncation test RED. Architect to also wire polarity for at least edit/reorder.

## Reuse patterns (from the funds-gate + audit-packet survey — reuse the STRUCTURE, not the domain)

- Defeat-first demo + a `naive_mode`/check-toggle so removing a detection check flips the result
  (polarity).
- Structured frozen-dataclass verdict that NAMES the failed assertion + carries the reg cite.
- Fail-closed input validation: never raise on malformed input; return a structured "tampered/
  invalid" verdict, not a crash.
- Zero-install `sys.path` injection in the demo; `python3 -m pkg.demo` entrypoint.
- README + CONTROL_STATEMENT + REVIEW.md conventions; the test file is the proof, the README is
  the claim, the control statement is the auditable record.
- Do NOT copy the OFAC ordering invariant, the SDN types, or the OFAC cite — those are the gate's
  domain; the ledger's domain is its own.
