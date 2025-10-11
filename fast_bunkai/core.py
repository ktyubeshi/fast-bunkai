from __future__ import annotations

import threading
import warnings
from typing import TYPE_CHECKING, Any, Iterator, List, Sequence, cast

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
        result = self._segment(text)
        boundaries = result["final_boundaries"]
        start = 0
        for end in boundaries:
            yield text[start:end]
            start = end
        if start < _char_len(text):
            yield text[start:]

    def find_eos(self, text: str) -> List[int]:
        result = self._segment(text)
        return result["final_boundaries"]

    def eos(self, text: str) -> Annotations:
        result = self._segment(text)
        annotations = Annotations()

        for layer in result["layers"]:
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
            annotations.add_annotation_layer(layer["name"], spans)
            if layer["name"] == "BasicRule":
                morph_spans = self._build_morph_layer(text)
                combined: List[SpanAnnotation] = morph_spans + list(annotations.flatten())
                annotations.add_annotation_layer("MorphAnnotatorJanome", combined)

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
        if len(text) * 4 < self._LARGE_TEXT_THRESHOLD_BYTES:
            return
        text_bytes = len(text.encode("utf-8"))
        if text_bytes < self._LARGE_TEXT_THRESHOLD_BYTES:
            return
        size_mib = text_bytes / (1024 * 1024)
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
