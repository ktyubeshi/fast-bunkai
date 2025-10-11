# ⚡ fast-bunkai

[![CI](https://github.com/hotchpotch/fast-bunkai/actions/workflows/ci.yml/badge.svg)](https://github.com/hotchpotch/fast-bunkai/actions/workflows/ci.yml)
[![Publish](https://github.com/hotchpotch/fast-bunkai/actions/workflows/publish.yml/badge.svg)](https://github.com/hotchpotch/fast-bunkai/actions/workflows/publish.yml)
[![PyPI](https://img.shields.io/pypi/v/fast-bunkai.svg)](https://pypi.org/project/fast-bunkai/)

⚡ FastBunkai is a Rust-accelerated, drop-in compatible reimplementation of [megagonlabs/bunkai](https://github.com/megagonlabs/bunkai) for lightning-fast sentence boundary detection.

⚡ fast-bunkai は [megagonlabs/bunkai](https://github.com/megagonlabs/bunkai) と互換 API を持ち、Rust による最適化で桁違いの高速性を実現した文分割ライブラリです。

---

**目次｜Table of Contents**

- [✨ Highlights](#-highlights)
- [🚀 Quick Start](#-quick-start)
- [🧰 CLI Examples](#-cli-examples)
- [📊 Benchmarks](#-benchmarks)
- [🧠 Architecture Snapshot](#-architecture-snapshot)
- [🛠️ Development Workflow](#️-development-workflow)
- [🧪 Testing & Quality Gates](#-testing--quality-gates)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)
- [👤 Author](#-author)

## ✨ Highlights

- 🔁 **Drop-in replacement**: mirrors the `FastBunkai` / `Bunkai` APIs and annotations, including Janome-based morphological spans.
- 🦀 **Rust-powered core**: heavy annotators (facemark, emoji, dot exceptions, indirect quotes, etc.) run inside a PyO3 module that releases the Python GIL.
- ⚡ **Serious speed**: real-world workloads observe 40×–300× faster segmentation than pure Python bunkai (details below).
- 🧵 **Thread-safe by design**: no global mutable state; calling `FastBunkai` concurrently from threads or asyncio tasks is supported.
- 🛫 **CLI parity**: ships a `fast-bunkai` executable compatible with bunkai’s pipe-friendly interface and `--ma` morphological mode.

## 🚀 Quick Start

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

## 🧰 CLI Examples

Pipe-friendly segmentation (sentence boundaries marked with `│`, newlines visualised via `▁`):

```bash
echo -e '宿を予約しました♪!▁まだ2ヶ月も先だけど。▁早すぎかな(笑)楽しみです★\n2文書目です。▁改行を含みます。' \
  | uvx fast-bunkai
```

```
宿を予約しました♪!▁│まだ2ヶ月も先だけど。▁│早すぎかな(笑)│楽しみです★
2文書目です。▁│改行を含みます。
```

Morphological mode reproduces bunkai’s `--ma` output:

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

## 📊 Benchmarks

Reproduce the bundled benchmark suite (correctness check + timing vs. bunkai):

```bash
uv run python scripts/benchmark.py --repeats 3 --jp-loops 100 --en-loops 100 --custom-loops 10
```

Latest GitHub Actions run ([2025-10-11](https://github.com/hotchpotch/fast-bunkai/actions/workflows/ci.yml)) reported:

| Corpus   | Docs | bunkai (mean) | fast-bunkai (mean) | Speedup |
|----------|------|---------------|--------------------|---------|
| Japanese | 200  | 547.04 ms     | 10.59 ms           | 51.65×  |
| English  | 200  | 407.15 ms     | 9.55 ms            | 42.62×  |
| Custom   | 20   | 2643.27 ms    | 8.81 ms            | 299.92× |

Actual numbers vary by hardware, but the Rust core consistently outperforms pure Python bunkai by an order of magnitude or more.

## 🧠 Architecture Snapshot

- 🦀 **Rust core (`src/lib.rs`)**: facemark & emoji annotators, dot/number exceptions, indirect quote handling, and more. Uses PyO3 `abi3` bindings and releases the GIL with `py.allow_threads`.
- 😀 **Emoji metadata (`src/emoji_data.rs`)**: generated via `scripts/generate_emoji_data.py`, mapping Unicode codepoints to bunkai-compatible categories.
- 🐍 **Python layer (`fast_bunkai/`)**: wraps the Rust `segment` function, mirrors bunkai annotations with dataclasses, and builds Janome spans through `MorphAnnotatorJanome` for drop-in parity.

## 🛠️ Development Workflow

```bash
uv sync --reinstall
uv run python scripts/generate_emoji_data.py  # regenerate emoji table when emoji libs change
uv run tox -e pytests,lint,typecheck,rust-fmt,rust-clippy
```

For manual Rust checks:

```bash
cargo test face_mark_detection_matches_reference
cargo fmt --all
cargo clippy --all-targets -- -D warnings
```

## 🧪 Testing & Quality Gates

- ✅ **pytest** (`tests/test_compatibility.py`): ensures Japanese・English texts, emoji-heavy samples, and parallel execution match bunkai outputs.
- 🧹 **Ruff**: lint + format checks via `tox -e lint,format-check`.
- 🧠 **Pyright**: type-checks the Python API surface.
- 🧪 **Rust unit tests**: validate annotator logic remains in sync with reference behaviour.
- 📈 **Benchmarks**: `scripts/benchmark.py` validates speed + correctness; normally executed in CI to avoid long local runs.

## 🙏 Acknowledgements

FastBunkai stands on the shoulders of the [megagonlabs/bunkai](https://github.com/megagonlabs/bunkai) project—ありがとうございます！

## 📄 License

Apache License 2.0

## 👤 Author

Yuichi Tateno ([@hotchpotch](https://github.com/hotchpotch))
