.PHONY: install test lint format clean

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check body_of_secrets tests
	mypy body_of_secrets || true

format:
	ruff format body_of_secrets tests

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
