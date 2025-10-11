from __future__ import annotations

from typing import List, TypedDict

class SpanDict(TypedDict):
    rule_name: str
    start: int
    end: int
    split_type: str | None
    split_value: str | None

class LayerDict(TypedDict):
    name: str
    spans: List[SpanDict]

class SegmentResult(TypedDict):
    layers: List[LayerDict]
    final_boundaries: List[int]

def segment(text: str) -> SegmentResult: ...
