PYTHON := python3
VERSION := $(shell $(PYTHON) -c "import importlib, pathlib, sys; tomllib = importlib.import_module('tomllib') if sys.version_info >= (3, 11) else importlib.import_module('tomli'); data = tomllib.loads(pathlib.Path('pyproject.toml').read_text()); print(data['project']['version'])")

.PHONY: release force-release

release:
	@git diff-index --quiet HEAD -- || (echo "Working tree has uncommitted changes" && exit 1)
	@if git rev-parse "v$(VERSION)" >/dev/null 2>&1; then \
		echo "Tag v$(VERSION) already exists locally"; exit 1; \
	fi
	@if git ls-remote --tags origin "v$(VERSION)" | grep -q .; then \
		echo "Tag v$(VERSION) already exists on origin"; exit 1; \
	fi
	@git tag -a v$(VERSION) -m "Release v$(VERSION)"
	@git push origin v$(VERSION)
	@echo "Released v$(VERSION)"

force-release:
	@git diff-index --quiet HEAD -- || (echo "Working tree has uncommitted changes" && exit 1)
	@git tag -a v$(VERSION) -f -m "Release v$(VERSION)"
	@git push origin +v$(VERSION)
	@echo "Force released v$(VERSION)"
