# Makefile for mange-ta-main project

.PHONY: preprocess clean help install test

# Default target
help:
	@echo "Available targets:"
	@echo "  preprocess    - Run the recipe preprocessing pipeline"
	@echo "  clean         - Clean generated files (data, logs, __pycache__)"
	@echo "  install       - Install project dependencies"
	@echo "  test          - Run tests (if available)"
	@echo "  help          - Show this help message"

# Run preprocessing pipeline
preprocess:
	uv run python src/preprocessing/preprocess.py

# Install dependencies
install:
	uv sync

# Clean generated files
clean:
	rm -rf data/*.pkl
	rm -rf logs/*.log

# Run tests (placeholder for future tests)
test:
	@echo "No tests configured yet"
	# uv run pytest tests/

# Development setup
dev-setup: install
	@echo "Development environment ready"