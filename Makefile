.PHONY: help build install install-dev test

help:
	@echo "Available commands:"
	@echo "  help            - Show this help message"
	@echo "  build           - Build Docker image"
	@echo "  install         - Install package"
	@echo "  install-dev     - Install package with dev dependencies"
	@echo "  install-uv      - Install package using uv"
	@echo "  install-dev-uv  - Install package with dev dependencies using uv"
	@echo "  test            - Run tests"
	@echo "  test-uv         - Run tests using uv"
	@echo "  relock          - Update lockfile using uv"

build:
	docker build -t stream:local .

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

install-uv:
	uv pip install -e .

install-dev-uv:
	uv pip install -e .[dev]

test:
	pytest

test-uv:
	uv run pytest

relock:
	uv lock