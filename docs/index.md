# Mange ta main

Mange ta main is a Streamlit-based analytics environment that helps culinary teams explore recipe data, evaluate nutritional balance, and surface personalized recommendations. The application couples interactive dashboards with a preprocessing pipeline so that health scoring, ingredient insights, and popularity trends stay in sync.

## Highlights

- **Interactive dashboards**: Navigate Streamlit pages for nutrition profiling, complexity analysis, and detailed recipe sheets.
- **Recommendation workflows**: Filter recipes or rely on the similarity engine to surface relevant dishes.
- **Data pipeline**: Reproducible preprocessing scripts clean, enrich, and cache datasets for fast iteration.
- **Extensible architecture**: Modular components and services make it easy to add new analytics panels or data sources.

Use the navigation to learn how to run the project locally or to dive into the Python APIs that power the experience.

## Architecture

- **Streamlit UI**: `app.py` orchestrates navigation; dedicated dashboards live under `pages/`.
- **Components**: `components/` aggregates reusable UI fragments and analytics visualisations.
- **Services**: `services/` centralises data loading, recommendation logic, and external integrations.
- **Utilities**: `utils/` exposes helpers for navigation, recipe formatting, and statistics.

## Data pipeline

- **Raw inputs**: CSV exports in `data/` blend recipe metadata, nutrition facts, and user interactions.
- **Preprocessing**: Scripts in `preprocessing/` clean ingredients, score nutrition, and build similarity matrices.
- **Automation**: `make preprocess` (part of `make dev`) executes the full pipeline.
- **Caching**: Generated artifacts and logs are persisted in `data/` and `logs/` for downstream reuse.

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
