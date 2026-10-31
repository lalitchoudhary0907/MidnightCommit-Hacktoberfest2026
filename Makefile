.PHONY: install test lint clean

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} +