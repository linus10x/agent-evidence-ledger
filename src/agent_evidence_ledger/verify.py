"""verify(records, ...) -> LedgerVerdict.

Walks genesis->head and runs five isolated detection checks IN ORDER, returning
the first failure NAMED, else a valid verdict. NEVER raises: malformed/unknown
input returns a structured forgery_class='invalid' verdict (a control that raises
can be swallowed by a caller and resolve to "proceed", so it must not raise).

Three module-level toggles guard exactly one check each (the documented
strip-points). Default True. A reviewer flips one to False and watches exactly
one polarity test go RED.
"""
import dataclasses
import re

from .canonical import entry_hash
from .records import (
    GENESIS_PREV_HASH,
    DecisionEntry,
    VetoRecord,
    DemoteRecord,
    RecordKind,
)

FORGERY_CLASSES = ("edit", "delete", "reorder", "bypass", "truncation")

# ---- POLARITY STRIP-POINTS (each guards exactly one check; default True) -----
# NOTE: __init__.py re-exports the verify FUNCTION into the package namespace,
# which SHADOWS this submodule attribute. An in-process patch of these toggles
# must therefore target sys.modules["agent_evidence_ledger.verify"], not
# agent_evidence_ledger.verify (which resolves to the function). The source-level
# strip — flipping a constant to False in THIS file — works regardless.
_CHECK_EDIT = True          # strip-point E: guards _check_links_and_edit
_CHECK_REORDER = True       # strip-point R: guards _check_sequence
_CHECK_TRUNCATION = True    # strip-point T: guards _check_truncation (centerpiece)
_CHECK_DELETE = True        # strip-point D: guards _check_continuity
_CHECK_BYPASS = True        # strip-point B: guards _check_coverage
# -----------------------------------------------------------------------------

REG_CITE: str = (
    "SEC Rule 17a-4(f)(2)(i)(A) — 17 CFR 240.17a-4(f)(2)(i)(A) (audit-trail alternative): "
    "a complete time-stamped audit trail recording all modifications to and deletions of a record, "
    "enabling re-creation of the original; retention 6 yrs per 240.17a-4(a). "
    "2022 amendment SEC Release 34-96034."
)

_KNOWN_RECORDS = (DecisionEntry, VetoRecord, DemoteRecord)
_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")


@dataclasses.dataclass(frozen=True)
class LedgerVerdict:
    valid: bool
    forgery_class: str | None   # one of FORGERY_CLASSES, "invalid", or None
    index: int | None
    detail: str
    reg_cite: str
    head: str
    count: int


def _verdict(valid, forgery_class, index, detail, head, count):
    return LedgerVerdict(
        valid=valid,
        forgery_class=forgery_class,
        index=index,
        detail=detail,
        reg_cite=REG_CITE,
        head=head,
        count=count,
    )


def _is_real_int(x):
    # bool is a subclass of int; exclude it explicitly.
    return isinstance(x, int) and not isinstance(x, bool)


def _strip_hash(record):
    """A copy with hash='' so canonical() (which excludes hash anyway) recomputes
    cleanly against its stored prev_hash."""
    return dataclasses.replace(record, hash="")


def _check_input_shape(records):
    """Fail-closed guard. Returns an 'invalid' verdict on any malformed input,
    else None. NEVER raises."""
    try:
        if not isinstance(records, (list, tuple)):
            return _verdict(False, "invalid", None, "records is not a sequence",
                            GENESIS_PREV_HASH, 0)
        for i, rec in enumerate(records):
            if not isinstance(rec, _KNOWN_RECORDS):
                return _verdict(False, "invalid", i,
                                "record is not a known record type",
                                GENESIS_PREV_HASH, len(records))
            if not _is_real_int(rec.seq):
                return _verdict(False, "invalid", i, "seq is not an int",
                                GENESIS_PREV_HASH, len(records))
            if not isinstance(rec.kind, RecordKind):
                return _verdict(False, "invalid", i, "kind is not a RecordKind",
                                GENESIS_PREV_HASH, len(records))
            if not isinstance(rec.prev_hash, str) or not _HEX64.match(rec.prev_hash):
                return _verdict(False, "invalid", i, "prev_hash is not 64-hex",
                                GENESIS_PREV_HASH, len(records))
            if not isinstance(rec.hash, str) or not _HEX64.match(rec.hash):
                return _verdict(False, "invalid", i, "hash is not 64-hex",
                                GENESIS_PREV_HASH, len(records))
            # tier fields per record type
            if isinstance(rec, DecisionEntry):
                if not _is_real_int(rec.authority_tier):
                    return _verdict(False, "invalid", i, "authority_tier not int",
                                    GENESIS_PREV_HASH, len(records))
                if not isinstance(rec.action_id, str) or not isinstance(rec.payload, str):
                    return _verdict(False, "invalid", i, "action_id/payload not str",
                                    GENESIS_PREV_HASH, len(records))
            elif isinstance(rec, VetoRecord):
                if not _is_real_int(rec.authority_tier):
                    return _verdict(False, "invalid", i, "authority_tier not int",
                                    GENESIS_PREV_HASH, len(records))
                if not isinstance(rec.vetoes_action_id, str) or not isinstance(rec.reason, str):
                    return _verdict(False, "invalid", i, "veto fields not str",
                                    GENESIS_PREV_HASH, len(records))
            elif isinstance(rec, DemoteRecord):
                if not (_is_real_int(rec.from_tier) and _is_real_int(rec.to_tier)):
                    return _verdict(False, "invalid", i, "tier fields not int",
                                    GENESIS_PREV_HASH, len(records))
                if not isinstance(rec.drift_signal_id, str):
                    return _verdict(False, "invalid", i, "drift_signal_id not str",
                                    GENESIS_PREV_HASH, len(records))
    except Exception as exc:  # defense in depth: any unexpected shape -> invalid
        return _verdict(False, "invalid", None, "malformed input: %r" % (exc,),
                        GENESIS_PREV_HASH, 0)
    return None


def _recompute_head_count(records):
    """Recompute the head over the records AS WALKED (relinked from genesis), and
    the count. Used both for the valid verdict's reported head and the anchor
    comparison."""
    prev = GENESIS_PREV_HASH
    for rec in records:
        prev = entry_hash(_strip_hash(rec), prev)
    return prev, len(records)


def _check_links_and_edit(records):
    """STRIP-POINT E. Recompute each record's hash from its stored prev_hash; a
    mismatch means the content changed without rehash -> edit at that seq."""
    for i, rec in enumerate(records):
        recomputed = entry_hash(_strip_hash(rec), rec.prev_hash)
        if recomputed != rec.hash:
            return ("edit", rec.seq, "recomputed hash != stored hash")
    return None


def _check_continuity(records):
    """For each record assert prev_hash == predecessor.hash (genesis predecessor
    == GENESIS_PREV_HASH). A break means an interior record was removed without
    re-linking -> delete at that seq."""
    prev_hash = GENESIS_PREV_HASH
    for i, rec in enumerate(records):
        if rec.prev_hash != prev_hash:
            return ("delete", rec.seq, "prev_hash != predecessor hash")
        prev_hash = rec.hash
    return None


def _check_sequence(records):
    """STRIP-POINT R. Assert record.seq == position (gap-free, +1 from 0). seq is
    bound into the hash, so a positional swap leaves a seq that no longer matches
    its position -> reorder at the first out-of-order position."""
    for i, rec in enumerate(records):
        if rec.seq != i:
            return ("reorder", i, "seq != position")
    return None


def _check_truncation(records, expected_head):
    """STRIP-POINT T (centerpiece). With an external anchor, recompute (head,
    count) and compare. Mismatch -> truncation at index = anchored count (the
    position of the missing tail / forked head)."""
    anchor_head, anchor_count = expected_head
    head, count = _recompute_head_count(records)
    if head != anchor_head or count != anchor_count:
        return ("truncation", anchor_count, "recomputed head/count != anchor")
    return None


def _check_coverage(records, executed_action_ids):
    """If executed_action_ids is supplied, every executed id must be recorded by a
    DECISION action_id or a VetoRecord vetoes_action_id. Any executed-but-unrecorded
    id -> bypass. Precondition: gap-free monotonic seq (check_sequence above)."""
    recorded = set()
    for rec in records:
        if isinstance(rec, DecisionEntry):
            recorded.add(rec.action_id)
        elif isinstance(rec, VetoRecord):
            recorded.add(rec.vetoes_action_id)
    missing = set(executed_action_ids) - recorded
    if missing:
        # The unrecorded action has no position; name the gap at count.
        return ("bypass", len(records), "executed action not recorded: %s"
                % ",".join(sorted(missing)))
    return None


def verify(records, *, expected_head=None, executed_action_ids=None) -> LedgerVerdict:
    # 1. fail-closed input guard (not one of the five classes).
    invalid = _check_input_shape(records)
    if invalid is not None:
        return invalid

    head, count = _recompute_head_count(records)

    # 2. edit (recompute-link). STRIP-POINT E.
    if _CHECK_EDIT:
        res = _check_links_and_edit(records)
        if res is not None:
            cls, idx, detail = res
            return _verdict(False, cls, idx, detail, head, count)

    # 3. delete (continuity). STRIP-POINT D.
    if _CHECK_DELETE:
        res = _check_continuity(records)
        if res is not None:
            cls, idx, detail = res
            return _verdict(False, cls, idx, detail, head, count)

    # 4. reorder (seq-vs-position). STRIP-POINT R.
    if _CHECK_REORDER:
        res = _check_sequence(records)
        if res is not None:
            cls, idx, detail = res
            return _verdict(False, cls, idx, detail, head, count)

    # 5. truncation (external head anchor). STRIP-POINT T (centerpiece).
    if _CHECK_TRUNCATION and expected_head is not None:
        res = _check_truncation(records, expected_head)
        if res is not None:
            cls, idx, detail = res
            return _verdict(False, cls, idx, detail, head, count)

    # 6. bypass (coverage cross-check). STRIP-POINT B.
    if _CHECK_BYPASS and executed_action_ids is not None:
        res = _check_coverage(records, executed_action_ids)
        if res is not None:
            cls, idx, detail = res
            return _verdict(False, cls, idx, detail, head, count)

    return _verdict(True, None, None, "all checks passed", head, count)
