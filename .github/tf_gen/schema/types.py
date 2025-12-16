from __future__ import annotations

from enum import StrEnum



class NestingMode(StrEnum):
    single = "single"
    list = "list"
    set = "set"


class AttrType(StrEnum):
    string = "string"
    bool = "bool"
    number = "number"
    dynamic = "dynamic"

    @classmethod
    def from_schema(cls, value: str) -> AttrType:
        if value == "any":
            return cls.dynamic
        return cls(value)


class CollectionKind(StrEnum):
    list = "list"
    set = "set"
    map = "map"


class TfTypeKind(StrEnum):
    primitive = "primitive"
    collection = "collection"
    object = "object"
