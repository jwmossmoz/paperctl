.PHONY: help install dev test lint format clean build

help:
	@echo "Available commands:"
	@echo "  make install    Install package"
	@echo "  make dev        Install dev dependencies"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linters"
	@echo "  make format     Format code"
	@echo "  make clean      Clean build artifacts"
	@echo "  make build      Build package"

install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev]"

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run mypy src

format:
	uv run ruff format .
	uv run ruff check --fix .

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

build:
	uv build
