"""The append-only Ledger: build-then-swap appends, head/count, head anchor.

append_* assigns seq = self.count, prev_hash = self.head, computes the hash, then
appends the fully-built frozen record (so a partial record is never stored).
Authority tier is bound into every decision entry, so "after demotion at seq N,
later decisions carry the lower tier" is provable from the chain alone.
"""
import dataclasses

from .canonical import entry_hash
from .records import (
    GENESIS_PREV_HASH,
    DecisionEntry,
    VetoRecord,
    DemoteRecord,
)


class Ledger:
    def __init__(self) -> None:
        self._records: list = []

    def _seal(self, partial):
        """Compute the record's hash over its canonical bytes + prev_hash, return
        the sealed frozen record. The partial carries hash='' as a placeholder
        that is excluded from canonical bytes anyway."""
        prev = self.head
        partial = dataclasses.replace(partial, prev_hash=prev, hash="")
        h = entry_hash(partial, prev)
        return dataclasses.replace(partial, hash=h)

    def append_decision(self, *, authority_tier: int, action_id: str, payload: str) -> DecisionEntry:
        rec = DecisionEntry(
            seq=self.count,
            authority_tier=authority_tier,
            action_id=action_id,
            payload=payload,
            prev_hash=GENESIS_PREV_HASH,
            hash="",
        )
        sealed = self._seal(rec)
        self._records.append(sealed)
        return sealed

    def append_veto(self, *, authority_tier: int, vetoes_action_id: str, reason: str) -> VetoRecord:
        rec = VetoRecord(
            seq=self.count,
            authority_tier=authority_tier,
            vetoes_action_id=vetoes_action_id,
            reason=reason,
            prev_hash=GENESIS_PREV_HASH,
            hash="",
        )
        sealed = self._seal(rec)
        self._records.append(sealed)
        return sealed

    def append_demote(self, *, from_tier: int, to_tier: int, drift_signal_id: str) -> DemoteRecord:
        rec = DemoteRecord(
            seq=self.count,
            from_tier=from_tier,
            to_tier=to_tier,
            drift_signal_id=drift_signal_id,
            prev_hash=GENESIS_PREV_HASH,
            hash="",
        )
        sealed = self._seal(rec)
        self._records.append(sealed)
        return sealed

    @property
    def head(self) -> str:
        if not self._records:
            return GENESIS_PREV_HASH
        return self._records[-1].hash

    @property
    def count(self) -> int:
        return len(self._records)

    @property
    def records(self) -> tuple:
        return tuple(self._records)

    def head_anchor(self) -> tuple:
        """(head, count) checkpoint — the EXTERNAL ANCHOR for truncation/fork.
        Held OUTSIDE the chain on purpose: an anchor stored as an interior record
        would itself be subject to truncation."""
        return (self.head, self.count)
