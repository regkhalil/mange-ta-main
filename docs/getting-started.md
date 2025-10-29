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

## Additional make targets

- `make start`: Run the Streamlit app without reinstalling or preprocessing.
- `make preprocess`: Execute the preprocessing pipeline only.
- `make docs-build` / `make docs-serve`: Build or serve MkDocs documentation.
- `make clean`: Remove generated data, logs, and caches.

## Testing & quality

- `make test`: Execute the pytest suite under `uv`.
- `make lint`: Run Ruff with autofix mode.
- `make format`: Apply Ruff formatting.
- `make fix`: Combine linting and formatting in one step before committing.

## Documentation delivery

- `.github/workflows/docs.yml` builds the MkDocs site with `uv` and deploys it to GitHub Pages on every push to `main` that touches the docs or Python modules with docstrings.
- The published site lives at <https://regkhalil.github.io/mange-ta-main/>; re-run the workflow manually from the Actions tab if you need an ad-hoc rebuild.
