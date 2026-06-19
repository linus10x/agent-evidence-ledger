"""Group E — fail-closed: malformed input -> structured invalid verdict, never raises."""
import _pathsetup  # noqa: F401

import pytest

from agent_evidence_ledger import verify
from _helpers import build_valid_chain, replace


def test_verify_on_non_sequence_returns_invalid():
    for garbage in (None, 42):
        v = verify(garbage)
        assert v.valid is False
        assert v.forgery_class == "invalid"


def test_verify_on_unknown_record_type_returns_invalid():
    _led, recs = build_valid_chain()
    recs.append({"not": "a record"})
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "invalid"


def test_verify_on_malformed_hash_returns_invalid():
    _led, recs = build_valid_chain()
    recs[0] = replace(recs[0], hash="not-64-hex")
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "invalid"


def test_verify_on_bool_seq_returns_invalid():
    _led, recs = build_valid_chain()
    # bool is a subclass of int; seq == True must be rejected as malformed.
    recs[0] = replace(recs[0], seq=True)
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "invalid"


@pytest.mark.parametrize("garbage", [
    None,
    42,
    "a string",
    object(),
    [object()],
    [None],
    [{"k": "v"}],
])
def test_verify_never_raises_on_any_garbage(garbage):
    # NONE of these may raise; ALL return a structured invalid verdict.
    v = verify(garbage)
    assert v.valid is False
    assert v.forgery_class == "invalid"


def test_payload_is_data_not_instructions():
    # A payload containing control-flow-looking text is hashed as bytes, never
    # evaluated. verify treats it as opaque data (injection invariant).
    led, recs = build_valid_chain()
    recs[1] = replace(recs[1], payload="__import__('os').system('echo pwned')")
    # That mutation changes content without rehash -> caught as edit, NOT executed.
    v = verify(recs)
    assert v.valid is False
    assert v.forgery_class == "edit"
    assert v.index == 1
