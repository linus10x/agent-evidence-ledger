"""The three frozen record types, the genesis sentinel, and the kind enum.

Each record's `hash` field is EXCLUDED from its own canonical serialization
(you cannot hash a value that contains its own hash). The `kind` discriminator
IS included in the canonical bytes so a veto and a decision with otherwise-equal
fields produce different hashes (a record-type swap cannot pass).
"""
import enum
from dataclasses import dataclass, field

# The fixed predecessor hash for seq 0 (sha256 hex width).
GENESIS_PREV_HASH: str = "0" * 64


class RecordKind(enum.Enum):
    DECISION = "decision"
    VETO = "veto"
    DEMOTE = "demote"


@dataclass(frozen=True)
class DecisionEntry:
    seq: int                 # ordinal, gap-free, +1 from genesis; bound INTO the hash
    authority_tier: int      # integer tier held at decision time; bound INTO the hash
    action_id: str           # id of the governed action this entry is a receipt for
    payload: str             # decision content; opaque DATA, never instructions
    prev_hash: str           # stored hash of the predecessor record
    hash: str                # stored hash of THIS record
    kind: RecordKind = field(default=RecordKind.DECISION)


@dataclass(frozen=True)
class VetoRecord:
    seq: int                 # ordinal position in the SAME chain (its ORDER)
    authority_tier: int      # tier of the higher authority issuing the veto
    vetoes_action_id: str    # the action_id this veto blocks/overrides
    reason: str              # opaque DATA
    prev_hash: str
    hash: str
    kind: RecordKind = field(default=RecordKind.VETO)


@dataclass(frozen=True)
class DemoteRecord:
    seq: int                 # ordinal position; proves WHEN demotion took effect
    from_tier: int           # authority tier before demotion
    to_tier: int             # the lower tier after demotion (to_tier < from_tier)
    drift_signal_id: str     # id of the EXTERNALLY-supplied drift signal
    prev_hash: str
    hash: str
    kind: RecordKind = field(default=RecordKind.DEMOTE)
