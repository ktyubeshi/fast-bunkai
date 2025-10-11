import subprocess
import sys


def run_cli(args: list[str], text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "fast_bunkai.cli", *args],
        input=text,
        text=True,
        capture_output=True,
        check=True,
    )


def test_cli_sentence_segmentation() -> None:
    result = run_cli([], "こんにちは。ありがとう。\n")
    assert result.stdout == "こんにちは。│ありがとう。\n"


def test_cli_morphological_output_contains_eos() -> None:
    result = run_cli(["--ma"], "テストです。\n")
    stdout = result.stdout
    assert "テスト" in stdout
    assert "EOS" in stdout


def test_cli_linebreak_placeholder() -> None:
    text = "改行を▁含む文章です。\n"
    result = run_cli([], text)
    assert result.stdout == "改行を▁│含む文章です。\n"
