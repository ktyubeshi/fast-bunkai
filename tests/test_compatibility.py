from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, List, Tuple

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


EDGE_CASE_TEXTS = [
    "",
    "   ",
    "\n\n\n",
    "。。。",
    "👍👍👍",
    "A.B.C",
    "おはよう🌞ございます！！",
    "終端記号...\n\n次の段落。",
    "😀\ufe0f test .",
    "First sentence終わり\nSecond sentence続き。",
]


PIPELINE_FOCUSED_TEXTS = [
    "顔文字(ノ´∀`*)ありがとう。すぐ返信するね。",
    "速報🚀✨Python3.13が来た！Rustも追随予定！",
    "彼は『やるって』と笑っていた。明日も来るらしい。",
    "バージョンv1.2.3を配布中。サーバーは127.0.0.1です。",
    "得点は12.5点だったが、No.10の選手が逆転した。",
    "引用文? という質問に困った。フォーラムで議論しよう。",
    "Twitter風投稿: Python🐍で書いてRust🦀で最適化するよ！ #dev #fast",
    "改行テスト\n\nここで強制的に区切る。さらに続く。",
]


def _load_fixture_texts() -> List[str]:
    data_dir = Path(__file__).parent / "data" / "texts"
    if not data_dir.is_dir():
        return []
    return [path.read_text(encoding="utf-8") for path in sorted(data_dir.glob("*.txt"))]


FILE_TEXTS: Tuple[str, ...] = tuple(_load_fixture_texts())


ALL_TEXTS: Tuple[str, ...] = tuple(
    SAMPLE_TEXTS + EDGE_CASE_TEXTS + PIPELINE_FOCUSED_TEXTS + list(FILE_TEXTS)
)


def collect_sentence_boundaries(ann) -> List[int]:
    return sorted({span.end_index for span in ann.get_final_layer()})


def collect_morph_surfaces(ann) -> List[str]:
    if "MorphAnnotatorJanome" not in ann.available_layers():
        return []
    surfaces: List[str] = []
    seen = set()
    for span in ann.get_annotation_layer("MorphAnnotatorJanome"):
        token = span.args.get("token") if span.args else None  # type: ignore[assignment]
        if token is None:
            continue
        surface = getattr(token, "word_surface", None)
        if not surface:
            continue
        key = (span.start_index, span.end_index, surface)
        if key in seen:
            continue
        seen.add(key)
        surfaces.append(surface)
    return surfaces


@pytest.mark.parametrize("text", ALL_TEXTS)
def test_sentence_splitting_matches_bunkai(text: str) -> None:
    fast = FastBunkai()
    ref = Bunkai()

    assert list(fast(text)) == list(ref(text))
    assert fast.find_eos(text) == ref.find_eos(text)

    fast_ann = fast.eos(text)
    ref_ann = ref.eos(text)

    assert sorted(fast_ann.available_layers()) == sorted(ref_ann.available_layers())
    assert collect_sentence_boundaries(fast_ann) == collect_sentence_boundaries(ref_ann)
    assert collect_morph_surfaces(fast_ann) == collect_morph_surfaces(ref_ann)


def _sequential_reference(texts: Iterable[str]) -> List[List[str]]:
    ref = Bunkai()
    return [list(ref(text)) for text in texts]


def test_multithread_consistency() -> None:
    texts = list(ALL_TEXTS) * 5
    fast = FastBunkai()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda t: list(fast(t)), texts))

    assert results == _sequential_reference(texts)


@pytest.mark.asyncio
async def test_asyncio_consistency() -> None:
    texts = list(ALL_TEXTS) * 3
    fast = FastBunkai()

    loop = asyncio.get_running_loop()

    async def run(text: str) -> List[str]:
        return await loop.run_in_executor(None, lambda: list(fast(text)))

    results = await asyncio.gather(*(run(text) for text in texts))
    assert results == _sequential_reference(texts)
