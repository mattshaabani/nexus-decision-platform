.PHONY: setup install test lint typecheck quality-gate docker-up docker-down clean

PYTHON := python3.12
VENV := .venv
BIN := $(VENV)/bin

setup: $(VENV)/bin/activate

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"
	@echo "\n✅ Environment ready. Activate with: source .venv/bin/activate"

install:
	$(BIN)/pip install -e ".[dev]"

test:
	$(BIN)/pytest

lint:
	$(BIN)/ruff check src tests scripts
	typecheck:
	typecheck:
	$(BIN)/mypy src

quality-gate:
	$(BIN)/python scripts/quality_gate.py

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build *.egg-info
