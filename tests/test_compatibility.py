from __future__ import annotations

import pytest

from bunkai import Bunkai

from fast_bunkai import FastBunkai


SAMPLE_TEXTS = [
    "こんにちは。ありがとう。",
    "スタッフ? と話し込み。",
    "No.1のホテルです。",
    "価格は3.5万円です。",
    "メールはtest@example.comです。",
    "顔文字(*^_^*)だよ。",
    "***(*^_^*)だよ。",
    "やったー(嬉)！",
    "わーい…！",
    "ROOM No.411でした。",
    "合宿免許? の若者さん達でしょうか",
    "スタッフ? と話し込み\n次の行です。",
]


def collect_sentence_boundaries(ann) -> list[int]:
    return sorted({span.end_index for span in ann.get_final_layer()})


def collect_morph_surfaces(ann) -> list[str]:
    surfaces: list[str] = []
    for span in ann.get_annotation_layer("MorphAnnotatorJanome"):
        token = span.args.get("token") if span.args else None  # type: ignore[assignment]
        if token is None:
            continue
        # span objects coming from flatten() may carry the same rule name; guard against duplicates.
        if getattr(token, "word_surface", None):
            surfaces.append(token.word_surface)
    return surfaces


@pytest.mark.parametrize("text", SAMPLE_TEXTS)
def test_sentence_splitting_matches_bunkai(text: str) -> None:
    fast = FastBunkai()
    ref = Bunkai()

    assert list(fast(text)) == list(ref(text))
    assert fast.find_eos(text) == ref.find_eos(text)

    fast_ann = fast.eos(text)
    ref_ann = ref.eos(text)

    assert collect_sentence_boundaries(fast_ann) == collect_sentence_boundaries(ref_ann)
    assert collect_morph_surfaces(fast_ann) == collect_morph_surfaces(ref_ann)

    assert "MorphAnnotatorJanome" in fast_ann.available_layers()
