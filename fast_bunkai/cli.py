from __future__ import annotations

import argparse
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterator

from fast_bunkai import FastBunkai

METACHAR_SENTENCE_BOUNDARY = "│"
METACHAR_LINE_BREAK = "▁"


def _version() -> str:
    try:
        return metadata.version("fast-bunkai")
    except metadata.PackageNotFoundError:
        return "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sentence boundary detection compatible with bunkai CLI",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("-"),
        help="Input file path (default: stdin)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("-"),
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--ma",
        action="store_true",
        help="Print morphological analysis result like bunkai --ma",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Print version information",
    )
    return parser.parse_args()


def _open_reader(path: Path):
    if str(path) in {"-", "/dev/stdin"}:
        return sys.stdin
    return path.open("r", encoding="utf-8")


def _open_writer(path: Path):
    if str(path) in {"-", "/dev/stdout"}:
        return sys.stdout
    return path.open("w", encoding="utf-8")


def _morph_output(text: str, splitter: FastBunkai) -> Iterator[str]:
    eos_candidates = splitter.find_eos(text)
    if eos_candidates:
        end_indices = [eos_candidates[0]]
        last_idx = eos_candidates[0]
        for idx in eos_candidates[1:]:
            if idx != last_idx:
                end_indices.append(idx)
                last_idx = idx
    else:
        end_indices = []
    annotations = splitter.eos(
        text,
        include_layers=("MorphAnnotatorJanome",),
        include_morph=True,
    )
    spans = [
        span
        for span in annotations.get_annotation_layer("MorphAnnotatorJanome")
        if span.rule_name == "MorphAnnotatorJanome"
    ]
    spans.sort(key=lambda span: (span.start_index, span.end_index))

    seen = set()
    position = 0
    eos_cursor = 0
    eos_len = len(end_indices)
    for span in spans:
        token = span.args.get("token") if span.args else None
        if token is None:
            continue
        token_id = id(token)
        if token_id in seen:
            continue
        seen.add(token_id)

        prev_position = position
        if token.node_obj is None or token.word_surface == "\n":
            yield METACHAR_LINE_BREAK + "\n"
            position += 1
        else:
            node = token.node_obj
            part_of_speech = getattr(node, "part_of_speech", ",".join(token.tuple_pos))
            infl_type = getattr(node, "infl_type", "*")
            infl_form = getattr(node, "infl_form", "*")
            base_form = getattr(node, "base_form", token.word_stem or token.word_surface)
            reading = getattr(node, "reading", "*")
            phonetic = getattr(node, "phonetic", "*")
            yield (
                f"{token.word_surface}\t"
                f"{part_of_speech},{infl_type},{infl_form},{base_form},{reading},{phonetic}\n"
            )
            position += len(token.word_surface)

        while eos_cursor < eos_len and end_indices[eos_cursor] <= position:
            if end_indices[eos_cursor] > prev_position:
                yield "EOS\n"
            eos_cursor += 1


def _sentence_output(text: str, splitter: FastBunkai) -> Iterator[str]:
    sentences = list(splitter(text))
    for idx, sentence in enumerate(sentences):
        if idx:
            yield METACHAR_SENTENCE_BOUNDARY
        yield sentence.replace("\n", METACHAR_LINE_BREAK)
    yield "\n"


def _process_line(
    splitter: FastBunkai,
    line: str,
    ma: bool,
    warned: bool,
) -> tuple[bool, Iterator[str]]:
    raw = line[:-1] if line.endswith("\n") else line

    if METACHAR_SENTENCE_BOUNDARY in raw:
        raw = raw.replace(METACHAR_SENTENCE_BOUNDARY, "")
        if not warned:
            sys.stderr.write(
                "\033[91m"
                "[Warning] All │ characters will be removed from input to avoid ambiguity\n"
                "\033[0m"
            )
            warned = True

    text = raw.replace(METACHAR_LINE_BREAK, "\n")

    if ma:
        return warned, _morph_output(text, splitter)
    return warned, _sentence_output(text, splitter)


def main() -> None:
    args = parse_args()

    if args.version:
        print(f"fast-bunkai {_version()}")
        return

    splitter = FastBunkai()
    warned = False

    reader_obj = _open_reader(args.input)
    writer_obj = _open_writer(args.output)

    try:
        for line in reader_obj:
            warned, iterator = _process_line(splitter, line, args.ma, warned)
            for chunk in iterator:
                writer_obj.write(chunk)
    finally:
        if reader_obj is not sys.stdin:
            reader_obj.close()
        if writer_obj is not sys.stdout:
            writer_obj.close()


if __name__ == "__main__":
    main()
