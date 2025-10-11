from __future__ import annotations

import dataclasses
import itertools
from typing import Any, Dict, Iterable, Iterator, List, Optional


@dataclasses.dataclass
class SpanAnnotation:
    rule_name: Optional[str]
    start_index: int
    end_index: int
    split_string_type: Optional[str]
    split_string_value: Optional[str]
    args: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"{self.start_index}-{self.end_index}/{self.rule_name}/{self.split_string_value}"

    def __int__(self) -> int:
        return self.end_index


@dataclasses.dataclass
class TokenResult:
    node_obj: Any
    tuple_pos: tuple[str, ...]
    word_stem: str
    word_surface: str
    is_feature: bool = True
    is_surface: bool = False
    misc_info: Any = None

    def __str__(self) -> str:
        return self.word_surface


@dataclasses.dataclass
class Annotations:
    annotator_forward: Optional[str] = None
    name2spans: Dict[str, List[SpanAnnotation]] = dataclasses.field(default_factory=dict)
    name2order: Dict[str, int] = dataclasses.field(default_factory=dict)
    current_order: int = 0

    def add_annotation_layer(self, annotator_name: str, annotations: List[SpanAnnotation]) -> None:
        self.name2spans[annotator_name] = annotations
        self.name2order[annotator_name] = self.current_order
        self.annotator_forward = annotator_name
        self.current_order += 1

    def add_flatten_annotations(self, annotations: Iterable[SpanAnnotation]) -> None:
        grouped = itertools.groupby(
            sorted(annotations, key=lambda a: a.rule_name or ""),
            key=lambda a: a.rule_name or "",
        )
        self.name2spans = {name: list(group) for name, group in grouped}

    def flatten(self) -> Iterator[SpanAnnotation]:
        return itertools.chain.from_iterable(self.name2spans.values())

    def get_final_layer(self) -> List[SpanAnnotation]:
        if self.annotator_forward is None:
            return []
        return self.name2spans[self.annotator_forward]

    def get_annotation_layer(self, layer_name: str) -> Iterator[SpanAnnotation]:
        spans = {
            str(ann): ann
            for ann in itertools.chain.from_iterable(self.name2spans.values())
            if ann.rule_name is not None
        }
        for ann in spans.values():
            if ann.rule_name == layer_name:
                yield ann

    def available_layers(self) -> List[str]:
        return list(self.name2spans.keys())
