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

[📚 Read the documentation](https://regkhalil.github.io/mange-ta-main/)

Mange ta main is a Streamlit application built to explore recipe data through nutrition analytics, recommendations, and interactive dashboards. The app blends curated datasets with a preprocessing pipeline so culinary teams can evaluate recipe health profiles, complexity, and popularity in one place.

## Quick start

- Install [uv](https://docs.astral.sh/uv/) and ensure `make` is available.
- Run `uv sync` to install dependencies (also triggered automatically by `make dev`).
- Launch the full workflow with `make dev`; stop with `Ctrl+C` when finished.

## Highlights

- Nutrition insights, ingredient analysis, and time-based dashboards.
- Recommendation flows powered by a similarity matrix and search filters.
- Modular architecture with reusable components and services.

## Documentation

- Full guides, architecture, and API reference live at [regkhalil.github.io/mange-ta-main](https://regkhalil.github.io/mange-ta-main/).
- CI/CD publishes updates through `.github/workflows/docs.yml` whenever docs or docstrings change on `main`.
