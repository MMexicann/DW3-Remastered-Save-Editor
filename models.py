"""Editable document state and field evidence, independent of the GUI."""
from dataclasses import dataclass
from pathlib import Path

class SaveError(ValueError):
    pass

@dataclass
class SaveDocument:
    source: Path | None
    encrypted: bytes
    plaintext: bytes
    parsed: dict

    @property
    def properties(self):
        return {entry['name']:entry for entry in self.parsed['properties']}

    def records(self,name):
        return self.properties[name]['value']['records']

def fields(record):
    result={p['name']:p for p in record}
    if len(result)!=len(record):
        raise SaveError('Duplicate record property names are unsupported.')
    return result

@dataclass(frozen=True)
class Change:
    category: str
    index: int
    field: str
    value: object  # Scalars, validated growth/weapon arrays, or None for unequip.

@dataclass(frozen=True)
class Patch:
    offset: int
    before: bytes
    after: bytes
    reason: str
