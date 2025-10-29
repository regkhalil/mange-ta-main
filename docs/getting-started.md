# Getting Started

Follow these steps to work on the project locally and preview the documentation that is generated from Python docstrings.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) for Python dependency management.
- `make` for the provided automation commands.

## Install dependencies

Use `uv` to install runtime and development dependencies:

```bash
uv sync
```

## Run the Streamlit app

Launch the full development workflow—install, preprocess, and start Streamlit—with:

```bash
make dev
```

Stop the server at any time with `Ctrl+C`.

## Work on the documentation

Serve the MkDocs site with live reload while you edit docstrings or markdown pages:

```bash
make docs-serve
```

Build the static site (outputs to the `site/` directory) for deployment checks:

```bash
make docs-build
```

MkDocs uses `mkdocstrings` to render API sections directly from the project's Python docstrings. Update docstrings in the codebase and refresh the browser to see changes immediately.
