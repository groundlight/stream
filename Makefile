.PHONY: build install install-dev test

build:
	docker build -t stream:local .

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

test:
	pytest

relock:
	uv lock