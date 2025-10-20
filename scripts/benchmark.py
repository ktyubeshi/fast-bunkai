#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path
from typing import Iterable, List, Literal

from bunkai import Bunkai

from fast_bunkai import FastBunkai

JAPANESE_PASSAGES = [
    (
        "本日は晴天なり。スタッフ? と話し込み。合宿免許? の若者さん達でしょうか。"
        "価格は3.5万円です。顔文字(*^_^*)だよ。おすすめ度No.1のホテルです。"
        "メールはtest@example.comです。やったー(嬉)！わーい…！"
        "スタッフ? と話し込み\n次の行でも議論は続いた。\n"
    ),
    (
        "この文章はFastBunkaiの評価用に作成されたダミーテキストです。"
        "ROOM No.411でした。おすすめ度No.1のホテルです。"
        "スタッフ? と話し込み。メールはsample@example.jpです。"
        "その後、彼らは階段を降りた。\n"
    ),
]

ENGLISH_PASSAGES = [
    (
        "Today the weather is perfect. The staff? kept talking. Could they be young people from the camp-license course?"
        " The price was 3.5 million yen. Emoji (*^_^*) is everywhere. The hotel ranked No.1 in recommendations."
        " Email us at contact@example.com. Hooray (excited)! Yay...! The conversation moved to the next line.\n"
    ),
    (
        "This paragraph exists solely to benchmark FastBunkai. Room No.411 was assigned."
        ' The guide said, "Staff? kept talking." The mailing list is hello@example.org.'
        " Later on, they climbed down the staircase and paused for a break.\n"
    ),
]


def load_external_texts() -> List[str]:
    data_dir = Path(__file__).resolve().parents[1] / "tests" / "data" / "texts"
    if not data_dir.is_dir():
        return []
    return [path.read_text(encoding="utf-8") for path in sorted(data_dir.glob("*.txt"))]


Mode = Literal["sentences", "boundaries"]


def ensure_correctness(
    reference: Bunkai, candidate: FastBunkai, texts: Iterable[str], mode: Mode
) -> None:
    for text in texts:
        if mode == "sentences":
            ref = list(reference(text))
            cand = list(candidate(text))
            if ref != cand:
                raise AssertionError(f"Mismatch for {text!r}: {cand} != {ref}")
            continue

        ref = reference.find_eos(text)
        cand = candidate.find_eos(text)
        if list(ref) != list(cand):
            raise AssertionError(f"Mismatch for {text!r}: {cand} != {ref}")


def measure(splitter, texts: List[str], repeats: int, mode: Mode) -> List[float]:
    timings: List[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        for text in texts:
            if mode == "sentences":
                list(splitter(text))
            else:
                splitter.find_eos(text)
        timings.append(time.perf_counter() - start)
    return timings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare fast-bunkai against bunkai for speed and correctness."
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Number of benchmark repetitions (default: 3).",
    )
    parser.add_argument(
        "--jp-loops", type=int, default=100, help="繰り返して使う日本語テキストのループ回数。"
    )
    parser.add_argument(
        "--en-loops", type=int, default=100, help="繰り返して使う英語テキストのループ回数。"
    )
    parser.add_argument(
        "--custom-loops",
        type=int,
        default=10,
        help="tests/data/texts 内の追加テキストを何度ループするか (該当ファイルがある場合のみ)。",
    )
    parser.add_argument(
        "--mode",
        choices=("sentences", "boundaries"),
        default="sentences",
        help="fast-bunkai の測定対象。sentences: 文章列を生成、boundaries: find_eos で境界のみ取得。",
    )
    args = parser.parse_args()

    bunkai_ref = Bunkai()
    fast = FastBunkai()

    external_texts = load_external_texts()

    sample_texts = list(JAPANESE_PASSAGES + ENGLISH_PASSAGES + external_texts)
    ensure_correctness(bunkai_ref, fast, sample_texts, args.mode)  # type: ignore[arg-type]

    corpora = {
        "Japanese": JAPANESE_PASSAGES * args.jp_loops,
        "English": ENGLISH_PASSAGES * args.en_loops,
    }

    if external_texts:
        corpora["Custom"] = external_texts * max(args.custom_loops, 1)

    def pretty(label: str, samples: List[float]) -> str:
        mean = statistics.mean(samples)
        stdev = statistics.stdev(samples) if len(samples) > 1 else 0.0
        return f"{label}: mean={mean * 1000:.2f} ms, stdev={stdev * 1000:.2f} ms"

    for name, texts in corpora.items():
        ref_timings = measure(bunkai_ref, texts, args.repeats, args.mode)  # type: ignore[arg-type]
        fast_timings = measure(fast, texts, args.repeats, args.mode)

        print(f"\n{name} corpus ({len(texts)} docs):")
        label = "  bunkai"
        if args.mode == "boundaries":
            label += " (find_eos)"
        print(pretty(label, ref_timings))

        fast_label = "  fast-bunkai"
        if args.mode == "boundaries":
            fast_label += " (find_eos)"
        print(pretty(fast_label, fast_timings))

        ratio = statistics.mean(ref_timings) / statistics.mean(fast_timings)
        print(f"  Speedup: {ratio:.2f}x")


if __name__ == "__main__":
    main()
