# fast-bunkai

Rust + Python hybrid rewrite of [megagonlabs/bunkai](https://github.com/megagonlabs/bunkai) that keeps the public API compatible while delivering significant speedups.

## Overview

- **Drop-in replacement**: exposes the same `FastBunkai` interface as the original `bunkai.Bunkai`. Compatibility tests cover Japanese / English examples, emoji-heavy texts, and custom corpora, matching pure Python bunkai outputs 100% for documented cases.
- **Rust-powered core**: segmentation pipeline (facemark, emoji, dot exceptions, indirect quote rules, etc.) is implemented in Rust via PyO3, releasing the GIL during heavy work while Python layers maintain Janome annotations for parity.
- **Speed**: on typical Japanese / English corpora, `uv run python scripts/benchmark.py --repeats 3 --jp-loops 100 --en-loops 100 --custom-loops 10` shows ≈24x faster end-to-end sentence splitting compared to the pure Python implementation.
- **CLI compatible**: bundled `fast-bunkai` command mirrors bunkai’s CLI (including `--ma` morphological mode and placeholder handling) and can be invoked quickly via `uvx`.

## Quick Start

### Install

```bash
uv pip install fast-bunkai
```

### Python Usage

```python
from fast_bunkai import FastBunkai

splitter = FastBunkai()
text = "宿を予約しました♪!まだ2ヶ月も先だけど。早すぎかな(笑)楽しみです★"
for sentence in splitter(text):
    print(sentence)
```

### CLI Usage

```bash
echo -e '宿を予約しました♪!まだ2ヶ月も先だけど。早すぎかな(笑)楽しみです★\n2文書目です。' \
  | uvx fast-bunkai
```

- `fast-bunkai --ma` outputs morphological annotations like the original bunkai.
- Placeholder `▁` represents line breaks and output sentence boundaries are marked with `│`.

### Benchmarks

To reproduce the bundled benchmarks (≈24x faster in our environment):

```bash
uv run python scripts/benchmark.py --repeats 3 --jp-loops 100 --en-loops 100 --custom-loops 10
```

This script runs correctness checks against `bunkai` before timing, then prints mean/stdev timings for each corpus.

## Development

```bash
uv sync --reinstall
uv run python scripts/generate_emoji_data.py  # regenerate emoji table if dependencies change
uv run tox -e pytests,lint,typecheck,rust-fmt,rust-clippy
```

## Acknowledgements

Huge thanks to the [megagonlabs/bunkai](https://github.com/megagonlabs/bunkai) authors for the original implementation and reference tests. FastBunkai builds on their work to offer a faster, drop-in alternative.

## License

Apache License 2.0

## Author

Yuichi Tateno ([@hotchpotch](https://github.com/hotchpotch))
