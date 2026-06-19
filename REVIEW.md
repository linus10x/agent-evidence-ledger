# Review verdict: agent-evidence-ledger

Independent code-reviewer (A2), step 5.3. Writer != reviewer; reviewer did NOT
write this code. Reviewed from a CLEAN CLONE (`/tmp/ael-review-clean`, since
removed). Source treated READ-ONLY except temporary, reverted polarity strips in
the clone (never in this origin repo). Fail-closed mandate: anything not
positively confirmed is treated as a finding.

## VERDICT: PASS

The primitive does what the control page claims. All five forgery classes are
genuinely detected with the correct class + index; the fail-closed guard never
raises and never false-accepts garbage; the canonical-encoding digest pin is real
(independently recomputed by hand); the polarity toggles are load-bearing (each
strip turns the matching forgery test RED, restore returns to green); and the one
residual surface (anchorless verify is blind to absence; fork collapses into
truncation) is an honestly documented threat boundary, not a hidden defect.

No CRITICAL or MAJOR findings. Three MINOR / informational notes below.

---

## Evidence (commands re-run by the reviewer, not trusted from the build log)

### (a) Demo — zero-install, no network, clean clone
`./demo.sh` -> exit 0. All seven scenes self-checked; all five forgeries named
with class+index: `edit @1`, `delete @3`, `reorder @1`, `bypass @4`,
`truncation @4`; valid chain verified clean; veto/demote ordering provable;
forged higher-tier post-demote decision caught as `edit @4`.
Source audit: `grep` for `socket|urllib|http|requests|ssl|subprocess|os.system|eval(|exec(|__import__`
across `src/` -> NONE. No network, no eval/exec/subprocess anywhere.

### (b) Tests green on BOTH runners
- `./run_tests.sh` (pytest path) -> `39 passed`, exit 0.
- Pure-python fallback `python3 -m agent_evidence_ledger._testrunner` -> `39 passed, 0 failed`, exit 0.
- The `run_tests.sh` ELSE branch was exercised (forced the `import pytest` probe
  to fail via a shim `python3`): it printed "pytest not found - using the
  pure-python fallback runner" and ran the fallback to `39 passed`, exit 0. A
  clone with no pytest still gets a real pass/fail.

### (b) Each forgery class — independently constructed (NOT the repo's fixtures)
Reviewer hand-built each forgery against a fresh 4-decision ledger:

| Attack (reviewer's own construction) | Result |
|---|---|
| edit entry[1].payload, leave stored hash | `valid=False class=edit index=1` |
| delete interior record (no relink) | `valid=False class=delete index=3` |
| swap pos 1/2, re-thread links, leave seq attached | `valid=False class=reorder index=1` |
| off-book action_id in executed set | `valid=False class=bypass index=4` |
| drop tail K=2, supply anchor | `valid=False class=truncation index=4` |
| re-linked interior delete (relinked, seq left 0,2,3) | `valid=False class=reorder index=1` (no false-accept) |

Every forgery test asserts ALL THREE of `valid is False`, the exact
`forgery_class`, and `index` (verified by reading each `test_forgery_*.py`).
This is PRESENCE-of-detection, not mere absence-of-acceptance.

### (c) FALSE-ACCEPT HUNT — no false-accept path found
- **(c-i) Fork without anchor.** A fully re-written/re-hashed alternate chain
  reads `valid=True` when NO `expected_head` is supplied. With the genuine anchor
  it is caught as `truncation`. Documented naive mode, not a defect — see "Honest
  threat boundary".
- **(c-ii) Truncation without anchor.** Reads `valid=True` (documented blindness;
  proved by `test_naive_verify_accepts_truncated_chain`). Caught once the anchor
  is supplied.
- **(c-iii) Reorder with seq ALSO renumbered + links re-threaded.** Reads
  `valid=True` without an anchor — because it is no longer a forgery: the attacker
  has produced a genuinely different, internally consistent chain (a fork) with
  payloads in a real, self-consistent order. Caught by the anchor as `truncation`.
  Mathematically indistinguishable from a legitimately-different ledger; the anchor
  is the only thing that can pin "this is not the chain I attested." Honestly
  disclosed.
- **(c-iv) Malformed-input fuzz.** 29 garbage inputs (None, 42, "string", floats,
  bytes, dicts, lists of junk, `object()`, bool-as-int seq, str seq, short hash,
  UPPERCASE 64-hex hash, None hash, bad prev_hash, bool/str tier, non-str
  action/payload, mixed valid+junk, NaN): **0 raised, 0 false-accepted.** Every one
  returned a structured `forgery_class='invalid'` verdict. Uppercase 64-hex is
  correctly rejected as `invalid` (regex pins lowercase, the canonical sha256 form).

### (d) Polarity — reproduced, load-bearing, isolated (source strip, full suite)
Each toggle flipped to `False` in `verify.py`, full suite run, then restored:

- `_CHECK_EDIT=False` -> RED: `test_forgery_edit`, `test_polarity_edit_strip`,
  `test_polarity_each_strip_fells_exactly_one_class`,
  `test_payload_is_data_not_instructions`,
  `test_decisions_after_demote_carry_lower_tier` (the last two are edit-class
  detections by another name — payload tamper and forged-tier are both caught AS
  edit). Restore -> `39 passed`.
- `_CHECK_REORDER=False` -> RED: `test_forgery_reorder`, its polarity test, the
  isolation test, `test_veto_position_cannot_be_forged` (a reorder by another
  name). Restore -> `39 passed`.
- `_CHECK_TRUNCATION=False` -> RED: `test_forgery_truncation` (dropped tail),
  `test_fork_substitution_caught_by_anchor`, `test_polarity_truncation_strip`.
  Restore -> `39 passed`.

Each strip fells exactly ONE forgery CLASS (edit / reorder / truncation); the
extra RED tests within a strip are additional assertions that DEPEND on that same
class, not a second class leaking. In-process confirmation via the correctly
patched module (`sys.modules["agent_evidence_ledger.verify"]`): with
`_CHECK_EDIT=False`, the payload-tampered chain reads `valid=True,
forgery_class=None` — the moat is genuinely removed, proving the check is
load-bearing (not shadowed by a downstream guard).

### (e) The verdict cannot lie
- No path yields `valid=True` on a tampered chain the verifier is given in full
  (every tamper localized to the records present is caught; absence/fork is caught
  by the anchor).
- `valid=False` always carries a non-None `forgery_class` (one of the five, or
  `'invalid'`) — confirmed across all constructions.
- Known-digest lock: reviewer **independently hand-recomputed** the sha256 of the
  spec's canonical encoding (json `sort_keys`+tight separators+`ensure_ascii`,
  `b'|'` separator) WITHOUT importing repo code and got
  `4b71ec6afb866bc4a5531f4d16f13d10baf0dfdd9b9dd6ffa3c577def30b36e8`, matching the
  committed pin. The encoding is genuinely pinned; the `b'|'` domain separator is
  exercised by `test_entry_hash_domain_separation`.

---

## Findings

### CRITICAL — none.
### MAJOR — none.

### MINOR / informational
1. **Two of five classes have no polarity toggle.** `delete` (continuity) and
   `bypass` (coverage) are always-on with no `_CHECK_*` strip-point, so the suite
   has no polarity proof they are load-bearing the way edit/reorder/truncation do.
   They ARE covered by their forgery tests, and the reviewer independently
   confirmed both fire (delete @3; bypass @4; re-linked delete degrades to reorder,
   never to valid). Adding `_CHECK_DELETE`/`_CHECK_COVERAGE` toggles would complete
   the polarity matrix. Not blocking — the plan scoped three toggles deliberately.
2. **Re-export shadowing footgun.** `agent_evidence_ledger.verify` resolves to the
   `verify` FUNCTION (re-exported in `__init__`), which shadows the submodule, so a
   caller that monkeypatches `agent_evidence_ledger.verify._CHECK_EDIT` patches the
   wrong object and the strip silently does nothing. The polarity tests already
   work around this (`sys.modules["agent_evidence_ledger.verify"]`) and document
   it, and the SOURCE-level strip (the documented reviewer action) works correctly.
   Worth a one-line caution in CONTROL_STATEMENT so a future reviewer doing an
   in-process strip does not get a false "still caught" result. Not a defect in the
   primitive.
3. **`LedgerVerdict.forgery_class`/`index` typed as `object`.** Functionally fine
   (frozen dataclass; values are always str|None / int|None in practice), but the
   plan's stated type was `str | None` / `int | None`. Cosmetic; no behavior impact.

---

## Honest threat boundary (confirmed accurate as documented)
The edit/delete/reorder checks catch localized tampering inside the records the
verifier is given. Bypass and truncation (including fork substitution) are caught
ONLY by the external head anchor and the executed-action set passed into
`verify()`. Without those inputs, `verify()` runs in the naive mode the truncation
class defeats — the chain proves the records it CONTAINS are intact but is blind to
a record never written or dropped from the end. README, CONTROL_STATEMENT, and
`test_naive_verify_accepts_truncated_chain` state this plainly and prove the anchor
closes the gap. This is the moat, disclosed honestly — NOT a false-accept.

## Reviewer worksheet (filled)

| # | Attack | Reviewer verdict |
|---|--------|------------------|
| 1 | edit in place | PASS — `edit @ seq`, independently reproduced |
| 2 | interior delete | PASS — `delete @ successor`, reproduced |
| 3 | swap + re-thread | PASS — `reorder @ first-out-of-order`, reproduced |
| 4 | off-book action | PASS — `bypass`, reproduced |
| 5 | drop tail | PASS — `truncation @ anchored count`, reproduced |
| 6 | fork substitution | PASS — caught as `truncation` by anchor, reproduced |
| 7 | move veto after action | PASS — caught (reorder/continuity), test asserts it |
| 8 | forge post-demote higher tier | PASS — caught as `edit`, reproduced via demo |
| 9 | malformed input | PASS — 29-input fuzz: 0 raises, 0 false-accepts, all `invalid` |
| 10 | instructions in payload | PASS — payload hashed as opaque bytes, never evaluated |

| Strip-point | Reviewer verdict |
|-------------|------------------|
| E (edit) | PASS — strip -> edit chain reads VALID; restore -> caught |
| R (reorder) | PASS — strip -> reorder slips; restore -> caught |
| T (truncation) | PASS — strip -> truncated chain reads VALID; restore -> caught |
| isolation | PASS — stripping truncation leaves edit+reorder caught |

**False-accept path: NONE found.** Every forgery the verifier can see is caught;
absence/fork is caught by the anchor; the anchorless blindness is documented, not
silent. Clean clone `/tmp/ael-review-clean` removed after review.

---

## Post-review fixes + orchestrator re-confirmation (2026-06-19)

All three MINOR notes were actioned (writer != reviewer preserved — fixes by the
code-writer, re-confirmed by the orchestrating session, not by the original reviewer):

- **MINOR 1 (closed — it was an absolute-guardrail gap, not optional polish).** The
  project guardrail requires EACH forgery class (edit/delete/reorder/bypass) to have a
  test that goes RED when its detection check is removed. Added `_CHECK_DELETE` (guards
  `_check_continuity`) and `_CHECK_BYPASS` (guards `_check_coverage`), each with a
  RED-first polarity test. Suite 39 -> **41 tests**. The polarity matrix is now complete
  for all five classes.
- **MINOR 2 (closed).** One-line caution added beside the toggle block in `verify.py`
  about the `sys.modules["agent_evidence_ledger.verify"]` patch handle (re-export
  shadowing).
- **MINOR 3 (closed).** `LedgerVerdict.forgery_class: str | None` and `.index: int | None`
  (were `object`), matching `.plan.md` §2.4.

**Orchestrator independently reproduced the full 5-way polarity matrix** (bytecode
caching disabled — see the gotcha below), default path catching all five:

```
default: 41 passed; ./demo.sh exit 0; classes named = edit,delete,reorder,bypass,truncation
STRIP _CHECK_EDIT       -> test_polarity_edit_strip_makes_it_pass       : 1 failed (RED)
STRIP _CHECK_REORDER    -> test_polarity_reorder_strip_makes_it_pass    : 1 failed (RED)
STRIP _CHECK_TRUNCATION -> test_polarity_truncation_strip_makes_it_pass : 1 failed (RED)
STRIP _CHECK_DELETE     -> test_polarity_delete_strip_makes_it_pass     : 1 failed (RED)
STRIP _CHECK_BYPASS     -> test_polarity_bypass_strip_makes_it_pass     : 1 failed (RED)
RESTORED -> 41 passed
```

**GATE-INTEGRITY GOTCHA (carry into any polarity reproduction):** Python's stale
`__pycache__/*.pyc` can make a stripped toggle FALSELY read "passed" — a green that hides
a removed safety check. Reproduce polarity with bytecode caching OFF: `PYTHONDONTWRITEBYTECODE=1`
and clear `__pycache__` between strips (or run `python3 -B`). The matrix above was produced
that way.

**5.3 status: PASS — confirmed.** No CRITICAL/MAJOR; all MINORs closed; the polarity matrix
is complete and independently reproduced.
