# Makefile for mange-ta-main project

.PHONY: preprocess clean help install test lint lint-check format format-check fix

# Default target
help:
	@echo "Available targets:"
	@echo "  preprocess    - Run the recipe preprocessing pipeline"
	@echo "  fix           - Run both linting and formatting (lint + format)"
	@echo "  lint          - Run ruff linter and fix issues"
	@echo "  lint-check    - Run ruff linter without fixing (check only)"
	@echo "  format        - Format code with ruff"
	@echo "  format-check  - Check code formatting without fixing"
	@echo "  clean         - Clean generated files (data, logs, __pycache__)"
	@echo "  install       - Install project dependencies"
	@echo "  test          - Run tests (if available)"
	@echo "  help          - Show this help message"

# Run preprocessing pipeline
preprocess:
	uv run python src/preprocessing/preprocess.py

# Code quality - combined linting and formatting
fix: lint format
	@echo "Code linting and formatting completed"

# Linting and formatting
lint:
	uv run ruff check --fix .

lint-check:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

# Install dependencies
install:
	uv sync

# Clean generated files
clean:
	rm -rf data/*
	rm -rf logs/*

# Run tests (placeholder for future tests)
test:
	@echo "No tests configured yet"
	# uv run pytest tests/

# Development setup
dev-setup: install
	@echo "Development environment ready"