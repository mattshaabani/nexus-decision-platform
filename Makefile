.PHONY: setup install test lint typecheck quality-gate docker-up docker-down clean

# Conda environment name (must match environment.yml)
ENV_NAME := nexus

# Use conda run so targets work even if the env is not currently activated
CONDA_RUN := conda run -n $(ENV_NAME) --no-capture-output

setup:
	@echo "Creating / updating conda env '$(ENV_NAME)' from environment.yml ..."
	conda env create -f environment.yml 2>/dev/null || conda env update -f environment.yml --prune
	@echo ""
	@echo "✅ Conda environment ready."
	@echo "   Activate with:  conda activate $(ENV_NAME)"
	@echo "   Then run:       make test   /   make quality-gate"

install:
	$(CONDA_RUN) pip install -e ".[dev]"

test:
	$(CONDA_RUN) pytest

lint:
	$(CONDA_RUN) ruff check src tests scripts

typecheck:
	$(CONDA_RUN) mypy src

quality-gate:
	$(CONDA_RUN) python scripts/quality_gate.py

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	conda env remove -n $(ENV_NAME) -y 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build *.egg-info
