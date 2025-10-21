from __future__ import annotations

import dataclasses
import itertools
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional


@dataclasses.dataclass(slots=True)
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


@dataclasses.dataclass(slots=True)
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


@dataclasses.dataclass(slots=True)
class Annotations:
    annotator_forward: Optional[str] = None
    name2spans: Dict[str, List[SpanAnnotation]] = dataclasses.field(default_factory=dict)
    name2order: Dict[str, int] = dataclasses.field(default_factory=dict)
    lazy_factories: Dict[str, Callable[[], List[SpanAnnotation]]] = dataclasses.field(
        default_factory=dict
    )
    lazy_order: Dict[str, int] = dataclasses.field(default_factory=dict)
    current_order: int = 0

    def add_annotation_layer(self, annotator_name: str, annotations: List[SpanAnnotation]) -> None:
        if annotator_name in self.lazy_factories:
            self._materialize_layer(annotator_name)
        self.name2spans[annotator_name] = annotations
        self.name2order[annotator_name] = self.current_order
        self.annotator_forward = annotator_name
        self.current_order += 1

    def add_lazy_annotation_layer(
        self, annotator_name: str, factory: Callable[[], List[SpanAnnotation]]
    ) -> None:
        self.lazy_factories[annotator_name] = factory
        self.lazy_order[annotator_name] = self.current_order
        self.annotator_forward = annotator_name
        self.current_order += 1

    def add_flatten_annotations(self, annotations: Iterable[SpanAnnotation]) -> None:
        grouped = itertools.groupby(
            sorted(annotations, key=lambda a: a.rule_name or ""),
            key=lambda a: a.rule_name or "",
        )
        self.name2spans = {name: list(group) for name, group in grouped}

    def flatten(self) -> Iterator[SpanAnnotation]:
        self._materialize_all_layers()
        return itertools.chain.from_iterable(self.name2spans.values())

    def get_final_layer(self) -> List[SpanAnnotation]:
        if self.annotator_forward is None:
            return []
        self._materialize_layer(self.annotator_forward)
        return self.name2spans[self.annotator_forward]

    def get_annotation_layer(self, layer_name: str) -> Iterator[SpanAnnotation]:
        self._materialize_layer(layer_name)
        spans = {
            str(ann): ann
            for ann in itertools.chain.from_iterable(self.name2spans.values())
            if ann.rule_name is not None
        }
        for ann in spans.values():
            if ann.rule_name == layer_name:
                yield ann

    def available_layers(self) -> List[str]:
        combined_orders = {**self.name2order, **self.lazy_order}
        return [
            name for name, _ in sorted(combined_orders.items(), key=lambda item: item[1])
        ]

    def _materialize_layer(self, layer_name: str) -> None:
        if layer_name not in self.lazy_factories:
            return
        factory = self.lazy_factories.pop(layer_name)
        order = self.lazy_order.pop(layer_name)
        spans = factory()
        self.name2spans[layer_name] = spans
        self.name2order[layer_name] = order

    def _materialize_all_layers(self) -> None:
        if not self.lazy_factories:
            return
        for name in sorted(self.lazy_factories.keys(), key=lambda n: self.lazy_order[n]):
            self._materialize_layer(name)
