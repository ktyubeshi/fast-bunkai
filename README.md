# fast-bunkai

fast-bunkai is a Python library for sentence boundary detection that mirrors the API of [megagonlabs/bunkai](https://github.com/megagonlabs/bunkai). You can drop it into existing bunkai-based projects and obtain the same results, while a Rust-powered core delivers much faster execution.

fast-bunkai は、日本語・英語の長い文章を自然な文単位に切り出すための Python ライブラリです。純粋 Python 実装である [megagonlabs/bunkai](https://github.com/megagonlabs/bunkai) と互換 API を提供しつつ、内部を Rust で最適化することで大幅な高速化を実現しています。

## Overview

- **Drop-in replacement**: exposes the same `FastBunkai` interface as the original `bunkai.Bunkai`. Compatibility tests cover Japanese / English examples, emoji-heavy texts, and custom corpora, matching pure Python bunkai outputs 100% for documented cases.
- **Rust-powered engine**: the segmentation pipeline (facemark, emoji, dot exceptions, indirect quote rules, etc.) runs in Rust via PyO3, releasing the GIL for heavy work while Python code preserves Janome-based annotations.
- **Speed**: GitHub Actions benchmarks (same command as below) observed ~40–300× faster segmentation depending on corpus size (see Benchmarks section).
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

`fast-bunkai` provides the same pipe-friendly command-line interface as bunkai.

```bash
echo -e '宿を予約しました♪!▁まだ2ヶ月も先だけど。▁早すぎかな(笑)楽しみです★\n2文書目です。▁改行を含みます。' \
  | uvx fast-bunkai
```

Output (sentence boundaries marked with `│`, newlines preserved via `▁`):

```
宿を予約しました♪!▁│まだ2ヶ月も先だけど。▁│早すぎかな(笑)│楽しみです★
2文書目です。▁│改行を含みます。
```

Morphological output is also available:

```bash
echo -e '形態素解析し▁ます。結果を 表示します！' | uvx fast-bunkai --ma
```

```
形態素	名詞,一般,*,*,*,*,形態素,ケイタイソ,ケイタイソ
解析	名詞,サ変接続,*,*,*,*,解析,カイセキ,カイセキ
し	動詞,自立,*,*,サ変・スル,連用形,する,シ,シ
▁
EOS
ます	助動詞,*,*,*,特殊・マス,基本形,ます,マス,マス
。	記号,句点,*,*,*,*,。,。,。
EOS
結果	名詞,副詞可能,*,*,*,*,結果,ケッカ,ケッカ
を	助詞,格助詞,一般,*,*,*,を,ヲ,ヲ
	記号,空白,*,*,*,*, ,*,*
表示	名詞,サ変接続,*,*,*,*,表示,ヒョウジ,ヒョージ
し	動詞,自立,*,*,サ変・スル,連用形,する,シ,シ
ます	助動詞,*,*,*,特殊・マス,基本形,ます,マス,マス
！	記号,一般,*,*,*,*,！,！,！
EOS
```

### Benchmarks

To reproduce the bundled benchmarks (correctness check + timing against pure Python bunkai):

```bash
uv run python scripts/benchmark.py --repeats 3 --jp-loops 100 --en-loops 100 --custom-loops 10
```

Recent GitHub Actions run (2025-10-11) produced the following averages:

| Corpus    | Docs | bunkai (mean) | fast-bunkai (mean) | Speedup |
|-----------|------|---------------|--------------------|---------|
| Japanese  | 200  | 547.04 ms     | 10.59 ms           | 51.65×  |
| English   | 200  | 407.15 ms     | 9.55 ms            | 42.62×  |
| Custom    | 20   | 2643.27 ms    | 8.81 ms            | 299.92× |

Actual numbers vary by hardware, but the Rust core consistently outperforms pure Python bunkai by an order of magnitude or more.

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
