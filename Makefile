.PHONY: setup install build-db clean-db serve test lint clean help

VENV        := venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
PYTEST      := $(VENV)/bin/pytest
RUFF        := $(VENV)/bin/ruff
DOCS_PATH   ?= assets

help:
	@echo "Available targets:"
	@echo "  setup      - Create virtualenv and install dependencies"
	@echo "  build-db   - Index HR text files from DOCS_PATH (default: assets/)"
	@echo "  clean-db   - Remove the ChromaDB index (run before rebuild to avoid conflicts)"
	@echo "  serve      - Start the web server (landing page + chat)"
	@echo "  test       - Run unit tests with coverage"
	@echo "  lint       - Run ruff linter"
	@echo "  clean      - Remove venv, ChromaDB index, and cache files"

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	@echo ""
	@echo "Setup complete. Copy .env.example to .env and configure your API keys:"
	@echo "  cp .env.example .env"

build-db:
	$(PYTHON) -m src.cli build-db $(DOCS_PATH)

clean-db:
	rm -rf data/chromadb
	@echo "ChromaDB index removed."

serve:
	$(PYTHON) -m src.cli serve

test:
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint:
	$(RUFF) check src/ tests/

clean:
	rm -rf $(VENV) data/chromadb __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
