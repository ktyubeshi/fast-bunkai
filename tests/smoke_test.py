from importlib import import_module


def main() -> None:
    module = import_module("fast_bunkai")
    fast = module.FastBunkai()
    text = "スタッフ? と話し込み。"
    assert list(fast(text)) == ["スタッフ? と話し込み。"]


if __name__ == "__main__":
    main()
