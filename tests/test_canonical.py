"""Group A — canonical hash reproducibility."""
import _pathsetup  # noqa: F401
import hashlib

from agent_evidence_ledger import canonical, GENESIS_PREV_HASH
from agent_evidence_ledger.canonical import entry_hash
from agent_evidence_ledger.records import DecisionEntry, VetoRecord, RecordKind


def _fixed_entry():
    # A fully-pinned entry. Field values are fixed so its digest is reproducible.
    return DecisionEntry(
        seq=0,
        authority_tier=2,
        action_id="act-0",
        payload="open position A",
        prev_hash=GENESIS_PREV_HASH,
        hash="ignored-in-canonical",
        kind=RecordKind.DECISION,
    )


def test_canonical_is_deterministic_across_calls():
    e = _fixed_entry()
    assert canonical(e) == canonical(e)
    # Independent of field-construction order: a logically-equal entry built with
    # keyword args in a different order yields identical bytes.
    e2 = DecisionEntry(
        kind=RecordKind.DECISION,
        hash="something-else-entirely",
        prev_hash=GENESIS_PREV_HASH,
        payload="open position A",
        action_id="act-0",
        authority_tier=2,
        seq=0,
    )
    assert canonical(e) == canonical(e2)


def test_canonical_excludes_hash_field():
    e = _fixed_entry()
    assert b"ignored-in-canonical" not in canonical(e)
    assert b'"hash"' not in canonical(e)


def test_kind_discriminator_in_canonical():
    # A decision and a veto with otherwise-equal field values must differ in bytes.
    d = DecisionEntry(
        seq=1, authority_tier=2, action_id="x", payload="x",
        prev_hash=GENESIS_PREV_HASH, hash="h", kind=RecordKind.DECISION,
    )
    v = VetoRecord(
        seq=1, authority_tier=2, vetoes_action_id="x", reason="x",
        prev_hash=GENESIS_PREV_HASH, hash="h", kind=RecordKind.VETO,
    )
    assert canonical(d) != canonical(v)
    assert b"decision" in canonical(d)
    assert b"veto" in canonical(v)


def test_known_entry_known_digest():
    # THE reproducibility lock. The literal below is the committed pin computed
    # from the canonical encoding of _fixed_entry() chained off genesis.
    e = _fixed_entry()
    digest = entry_hash(e, GENESIS_PREV_HASH)
    assert digest == "4b71ec6afb866bc4a5531f4d16f13d10baf0dfdd9b9dd6ffa3c577def30b36e8"


def test_entry_hash_domain_separation():
    e = _fixed_entry()
    real = entry_hash(e, GENESIS_PREV_HASH)
    naive = hashlib.sha256(canonical(e) + GENESIS_PREV_HASH.encode("utf-8")).hexdigest()
    # The b'|' separator must make the real hash differ from naive concatenation.
    assert real != naive
