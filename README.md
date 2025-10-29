---
title: Mange Ta Main
emoji: 📊
colorFrom: pink
colorTo: indigo
sdk: streamlit
sdk_version: 1.50.0
python_version: 3.13
app_file: app.py
pinned: false
---

# Mange ta main

Mange ta main is a Streamlit application that helps users explore recipes through nutrition analytics, recommendation workflows, and interactive dashboards. The app couples curated datasets with a preprocessing pipeline and a modular UI so culinary teams can evaluate recipe health profiles, complexity, and popularity in one place.

## Overview

- **Nutrition insights**: Grade distributions, nutrient correlations, and macro balance dashboards.
- **Recipe discovery**: Search and recommendation flows tailored to dietary goals.
- **Interactive analytics**: Complexity, ingredient health, and time-to-prepare visualizations.
- **Data-first design**: Preprocessing steps clean, enrich, and cache data for fast loading.

## Architecture

- **Streamlit front-end**: `app.py` wires core navigation; Streamlit pages under `pages/` host specialty dashboards.
- **Component modules**: `components/` contains reusable UI blocks and analytics presenters.
- **Services layer**: `services/` manages data loading, recommender logic, and external APIs.
- **Utilities**: `utils/` centralizes navigation helpers, recipe formatting, and statistics helpers.

## Data pipeline

- **Raw inputs**: CSV datasets in `data/` combine recipe metadata, nutrition facts, and user interactions.
- **Preprocessing scripts**: `preprocessing/` modules clean ingredients, score nutrition, and build similarity matrices.
- **Automation**: `make preprocess` (part of `make dev`) runs the full pipeline via `preprocessing/preprocess.py`.
- **Caching**: Generated artifacts and logs are stored in `data/` and `logs/` for reuse by the app.

## Project structure

```
app.py               # Streamlit entrypoint
components/          # UI widgets and analytics modules
data/                # Raw and processed CSV datasets
pages/               # Streamlit multipage dashboards
preprocessing/       # Data cleaning and feature engineering scripts
services/            # Data access, recommendation, and external integrations
utils/               # Shared helpers (navigation, recipes, stats)
tests/               # Pytest-based checks for data loading logic
```

## Local development

- **Requirements**: Install `uv` (Python package manager) and ensure `make` is available.
- **Install dependencies**: Run `uv sync` (also triggered automatically by `make dev`).
- **Start the app**: Execute `make dev` to install, preprocess, and launch Streamlit.
- **Stop the app**: Use `Ctrl+C` in the running terminal when you are done.

The `make dev` workflow installs dependencies, prepares datasets, and serves the Streamlit UI for rapid iteration.

## Make targets

- `make dev`: Install dependencies, preprocess data, and launch the app.
- `make start`: Run the Streamlit app without reinstalling or preprocessing.
- `make preprocess`: Execute the preprocessing pipeline only.
- `make test`: Launch the pytest suite in `tests/`.
- `make lint` / `make format`: Apply Ruff linting and formatting fixes.
- `make clean`: Remove generated data, logs, and caches.

## Testing and quality

- **Unit tests**: Pytest suites live in `tests/`; run `make test` to execute them under `uv`.
- **Linting**: `make lint` checks code style and applies autofixes using Ruff.
- **Formatting**: `make format` enforces consistent formatting across Python files.
- **Continuous refinement**: Combine linting and formatting with `make fix` before committing changes.
