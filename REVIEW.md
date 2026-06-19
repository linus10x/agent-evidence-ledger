# Review worksheet: agent-evidence-ledger

Adversarial-read worksheet. The independent reviewer (code-reviewer at step 5.3)
fills the verdict column. The rows are the attacks an adversary tries and the
mechanism that is supposed to catch each one. The job of the review is to confirm
each mechanism actually fires and that the test asserts PRESENCE of detection.

## What an attacker tries

| # | Attack | Intended catch | Test | Reviewer verdict |
|---|--------|----------------|------|------------------|
| 1 | edit a record's payload in place, leave its stored hash | recompute-link mismatch names `edit` at the seq | `test_forgery_edit.py` | (pending) |
| 2 | remove an interior record, do not re-link | continuity break names `delete` at the successor seq | `test_forgery_delete.py` | (pending) |
| 3 | swap two records' positions, re-thread links so continuity holds | seq-vs-position mismatch names `reorder` at the first out-of-order position | `test_forgery_reorder.py` | (pending) |
| 4 | execute an action and write no record for it | coverage cross-check names `bypass` | `test_forgery_bypass.py` | (pending) |
| 5 | drop the last K records (the chain stays internally consistent) | external head anchor names `truncation` at the anchored count | `test_forgery_truncation.py` | (pending) |
| 6 | substitute a wholesale alternate valid chain (fork) | head anchor names `truncation` (fork collapses into the same mechanism) | `test_fork_substitution_caught_by_anchor` | (pending) |
| 7 | move a veto to after the action it vetoes | reorder or continuity catches the timing forgery | `test_veto_position_cannot_be_forged` | (pending) |
| 8 | forge a post-demote decision to claim the higher tier again | tier is bound into the hash; caught as `edit` | `test_decisions_after_demote_carry_lower_tier` | (pending) |
| 9 | feed malformed or unknown input to crash the verifier into "proceed" | fail-closed guard returns `invalid`, never raises | `test_fail_closed.py` | (pending) |
| 10 | hide instructions in a payload string | payload is hashed as opaque bytes, never evaluated | `test_payload_is_data_not_instructions` | (pending) |

## Polarity (is each check load-bearing)

| Strip-point | Toggle | Test that goes RED | Reviewer verdict |
|-------------|--------|--------------------|------------------|
| E (edit) | `_CHECK_EDIT=False` | `test_polarity_edit_strip_makes_it_pass` | (pending) |
| R (reorder) | `_CHECK_REORDER=False` | `test_polarity_reorder_strip_makes_it_pass` | (pending) |
| T (truncation) | `_CHECK_TRUNCATION=False` | `test_polarity_truncation_strip_makes_it_pass` | (pending) |
| isolation | flip one toggle | other forgery tests stay green: `test_polarity_each_strip_fells_exactly_one_class` | (pending) |

## Polarity check (the assertion's direction)

The reviewer should confirm each forgery test asserts the PRESENCE of the safe
condition, not merely the absence of an unsafe one. Concretely: every forgery
test asserts all three of `verdict.valid is False`, `verdict.forgery_class ==
"<class>"`, and `verdict.index == <expected>`. A test that asserted only "not
valid" could false-pass on a different forgery or on a malformed-input verdict;
naming the class and the index is what closes that gap.

## Honest threat boundary

The edit, delete, and reorder checks catch localized tampering inside the records
the verifier is given. Bypass (an action with no record) and truncation (a tail
silently dropped, or a fork substituted) are caught ONLY by the external head
anchor and the executed-action set passed into `verify()`. Without those two
inputs, `verify()` runs in the naive mode the truncation class defeats. That is
the moat and it is stated plainly: the chain proves the records it contains are
intact; it is blind to records never written or dropped from the end. The anchor
must be held outside the chain by the caller for the truncation guarantee to
hold.
