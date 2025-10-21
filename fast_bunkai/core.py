from __future__ import annotations

import threading
import warnings
from typing import TYPE_CHECKING, Any, Iterator, List, Optional, Sequence, cast

if TYPE_CHECKING:
    from ._fast_bunkai import SegmentResult

from janome.tokenizer import Tokenizer

from . import _fast_bunkai
from .annotations import Annotations, SpanAnnotation, TokenResult


def _char_len(text: str) -> int:
    return len(text)


class FastBunkaiSentenceBoundaryDisambiguation:
    _LARGE_TEXT_THRESHOLD_BYTES = 10 * 1024 * 1024

    def __init__(self) -> None:
        self._tokenizer_factory = Tokenizer
        self._tokenizer_local = threading.local()

    def __call__(self, text: str) -> Iterator[str]:
        boundaries = self.find_eos(text)
        start = 0
        for end in boundaries:
            yield text[start:end]
            start = end
        if start < _char_len(text):
            yield text[start:]

    def find_eos(self, text: str) -> List[int]:
        self._warn_large_text(text)
        return cast(List[int], _fast_bunkai.segment_boundaries(text))

    def eos(
        self,
        text: str,
        *,
        include_layers: Optional[Sequence[str]] = None,
        include_morph: Optional[bool] = None,
    ) -> Annotations:
        want_layers = set(include_layers) if include_layers is not None else None
        if include_morph is None:
            need_morph_layer = want_layers is None or "MorphAnnotatorJanome" in want_layers
        else:
            need_morph_layer = include_morph

        need_segment = (
            want_layers is None
            or any(layer_name != "MorphAnnotatorJanome" for layer_name in want_layers)
        )

        if not need_segment:
            # Ensure large text warning parity when we skip the Rust segment call.
            self._warn_large_text(text)

        result = self._segment(text) if need_segment else None
        annotations = Annotations()

        if result is not None:
            for layer in result["layers"]:
                name = layer["name"]
                if want_layers is not None and name not in want_layers:
                    continue
                spans = [
                    SpanAnnotation(
                        rule_name=span["rule_name"],
                        start_index=span["start"],
                        end_index=span["end"],
                        split_string_type=span["split_type"],
                        split_string_value=span["split_value"],
                        args=None,
                    )
                    for span in layer["spans"]
                ]
                annotations.add_annotation_layer(name, spans)
                if name == "BasicRule" and need_morph_layer:

                    def morph_factory() -> List[SpanAnnotation]:
                        return self._build_morph_layer(text)

                    annotations.add_lazy_annotation_layer("MorphAnnotatorJanome", morph_factory)
        elif need_morph_layer:

            def morph_only_factory() -> List[SpanAnnotation]:
                return self._build_morph_layer(text)

            annotations.add_lazy_annotation_layer("MorphAnnotatorJanome", morph_only_factory)

        return annotations

    def _segment(self, text: str) -> "SegmentResult":
        self._warn_large_text(text)
        return _fast_bunkai.segment(text)

    def _build_morph_layer(self, text: str) -> List[SpanAnnotation]:
        tokenizer = self._get_tokenizer()
        spans: List[SpanAnnotation] = []
        start_index = 0
        tokens: Sequence[Any] = cast(Sequence[Any], tokenizer.tokenize(text))
        for token in tokens:
            surface = token.surface
            length = len(surface)
            token_result = TokenResult(
                node_obj=token,
                tuple_pos=tuple(token.part_of_speech.split(",")),
                word_stem=token.base_form,
                word_surface=surface,
            )
            spans.append(
                SpanAnnotation(
                    rule_name="MorphAnnotatorJanome",
                    start_index=start_index,
                    end_index=start_index + length,
                    split_string_type="janome",
                    split_string_value="token",
                    args={"token": token_result},
                )
            )
            start_index += length
        if start_index < _char_len(text) and text[start_index:] == "\n":
            token_result = TokenResult(
                node_obj=None,
                tuple_pos=("記号", "空白", "*", "*"),
                word_stem="\n",
                word_surface="\n",
            )
            spans.append(
                SpanAnnotation(
                    rule_name="MorphAnnotatorJanome",
                    start_index=start_index,
                    end_index=_char_len(text),
                    split_string_type="janome",
                    split_string_value="token",
                    args={"token": token_result},
                )
            )
        return spans

    def _warn_large_text(self, text: str) -> None:
        char_len = len(text)
        if char_len == 0:
            return
        if char_len * 2 < self._LARGE_TEXT_THRESHOLD_BYTES:
            return
        estimated_bytes = char_len if text.isascii() else char_len * 3
        if estimated_bytes < self._LARGE_TEXT_THRESHOLD_BYTES:
            return
        size_mib = estimated_bytes / (1024 * 1024)
        warnings.warn(
            (
                "fast-bunkai received approximately "
                f"{size_mib:.2f} MiB of text; segmentation may consume large memory "
                "due to intermediate annotations."
            ),
            ResourceWarning,
            stacklevel=4,
        )

    def _get_tokenizer(self) -> Tokenizer:
        tokenizer = getattr(self._tokenizer_local, "instance", None)
        if tokenizer is None:
            tokenizer = self._tokenizer_factory()
            self._tokenizer_local.instance = tokenizer
        return tokenizer


FastBunkai = FastBunkaiSentenceBoundaryDisambiguation
