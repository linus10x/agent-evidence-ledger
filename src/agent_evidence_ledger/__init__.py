"""agent-evidence-ledger: a tamper-evident, append-only ledger of agent decisions.

verify() returns a structured verdict naming which of five forgery classes (edit,
delete, reorder, bypass, truncation) was detected and at which index. Record
integrity only; no PKI, no storage backend, no drift detector.
"""
from .records import (
    GENESIS_PREV_HASH,
    RecordKind,
    DecisionEntry,
    VetoRecord,
    DemoteRecord,
)
from .canonical import canonical, entry_hash
from .ledger import Ledger
from .verify import verify, LedgerVerdict, REG_CITE, FORGERY_CLASSES

__all__ = [
    "Ledger",
    "DecisionEntry",
    "VetoRecord",
    "DemoteRecord",
    "LedgerVerdict",
    "verify",
    "canonical",
    "entry_hash",
    "GENESIS_PREV_HASH",
    "REG_CITE",
    "FORGERY_CLASSES",
    "RecordKind",
]
