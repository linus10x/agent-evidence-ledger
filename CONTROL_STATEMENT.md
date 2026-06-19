# Control statement: agent-evidence-ledger

The auditable record of what this primitive controls, which regulatory clause
each invariant maps to, the five detection mechanisms, and the polarity
strip-points that prove each check is load-bearing.

## Reg anchor

SEC Rule 17a-4(f)(2)(i)(A), 17 CFR 240.17a-4(f)(2)(i)(A) (the audit-trail
alternative to WORM, added by the 2022 amendment, SEC Release 34-96034). The
clause requires an electronic recordkeeping system to maintain a complete
time-stamped audit trail that records all modifications to and deletions of a
record, with the date and time of every create, modify, and delete, such that
the original can be re-created if modified or deleted. Retention is six years per
240.17a-4(a). The cite is carried verbatim in the `REG_CITE` constant and on
every verdict.

## Clause-to-check mapping

The clause's four operative requirements map to the five checks as follows.

1. "all modifications" detectable. Mapped to the edit check (recompute-link
   mismatch) and the reorder check (the ordinal is bound into the hash). Any
   in-place change to a record, including a positional swap, is detectable and
   localized to an index.

2. "all deletions" detectable. Mapped to the delete check (chain discontinuity)
   AND the truncation check (external head anchor) together. The delete check
   covers removal of an interior record; the truncation check covers removal of
   the tail, which a bare chain misses. This pairing is the precise fit for "all
   deletions of a record."

3. "complete" audit trail (no off-book gaps). Mapped to the bypass coverage
   invariant: a gap-free monotonic sequence plus a check that every governed
   action carries a recorded receipt. The clause's word "complete" maps to
   absence-of-gaps, which the chain alone cannot prove.

4. "identity and authority of the actor" with ordered create, modify, delete.
   Mapped to `authority_tier` bound into every decision record, plus the veto and
   demote records carried in the same chain. The audit trail records not only the
   change but who was allowed to make it and when, in order.

The centerpiece (truncation) is the "deletions enabling re-creation of the
original" requirement applied to the tail. A system that silently accepts a
dropped tail cannot re-create the original and fails 17a-4(f)(2)(i)(A).

## The five detection mechanisms

| Class | Check | Mechanism |
|-------|-------|-----------|
| edit | `_check_links_and_edit` | recompute `entry_hash(record_without_hash, stored_prev_hash)`; if it differs from the stored hash, the content changed without rehash |
| delete | `_check_continuity` | for each record assert `prev_hash == predecessor.hash` (genesis predecessor is the all-zero hash); a break means an interior record was removed |
| reorder | `_check_sequence` | assert `seq == position` for every record; seq is bound into the hash, so a positional swap leaves a seq inconsistent with its position |
| bypass | `_check_coverage` | the set of recorded action-ids must equal the supplied executed set; any executed-but-unrecorded id is named |
| truncation | `_check_truncation` | recompute `(head, count)` and compare to the external anchor; a mismatch names the dropped tail or substituted fork |

A fail-closed input guard (`_check_input_shape`) runs first. On any malformed or
unknown input it returns `forgery_class="invalid"`, distinct from the five named
classes, and never raises.

Check order inside `verify()` is fixed: input shape, then edit, then delete
(continuity), then reorder (sequence), then truncation, then bypass. The order is
chosen so that each forgery fixture trips its own check as the first failure.
Continuity runs before sequence so an interior delete labels as `delete` rather
than `reorder`.

## Polarity strip-points

Three module-level booleans in `verify.py`, each default True, each guarding
exactly one check:

- `_CHECK_EDIT` guards `_check_links_and_edit` (strip-point E).
- `_CHECK_REORDER` guards `_check_sequence` (strip-point R).
- `_CHECK_TRUNCATION` guards `_check_truncation` (strip-point T, the centerpiece).

A reviewer flips one constant to `False` in source and watches exactly one
forgery polarity test go RED while the others stay green
(`test_polarity_each_strip_fells_exactly_one_class` proves the isolation).
Restoring it returns the suite to green. This is the documented, auditable
mechanism that proves each check is load-bearing and that the suite asserts the
PRESENCE of the safe condition (the forgery is caught), not the mere absence of
an unsafe one.

## Failure posture

All failure modes fail closed. Malformed input returns a structured invalid
verdict, never an exception. An empty ledger with no anchor verifies vacuously; an
empty ledger that was anchored non-empty is caught as truncation. A process
killed mid-append leaves the ledger at its last fully-appended record (append is
build-then-swap in memory), and if an anchor exists the dropped tail is caught as
truncation. Nothing here is scheduled, networked, or long-running.

## Out of scope

No PKI or signatures. No storage backend. No real drift detector (demote is
record-only). No replay class. No separate fork class (fork collapses into the
truncation head-anchor mechanism). No network, no scheduled job, no publish step.
No branded authority vocabulary; tiers are plain integers.
