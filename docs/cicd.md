# Continuous Delivery and Deployment

Mange ta main leverages GitHub Actions to automate preprocessing, deployment to cloud platforms, and documentation publishing. This CI/CD setup ensures that changes to code or data are reliably propagated through the pipeline without manual intervention.

## Overview

The project uses three primary workflows:

1. **Preprocessing**: Automatically runs data preprocessing when changes are detected in preprocessing scripts
2. **Sync to Hugging Face**: Deploys the application to Hugging Face Spaces whenever the main branch is updated
3. **Documentation**: Builds and publishes API documentation to GitHub Pages

## Preprocessing Workflow

**Workflow file**: `.github/workflows/preprocess-and-deploy.yml`

### Trigger Conditions

This workflow runs when:

- Changes are pushed to the `main` branch in the `preprocessing/` directory
- The workflow file itself is modified
- Manually triggered via the Actions tab (workflow_dispatch)

### What It Does

1. **Environment Setup**: Installs Python 3.13, uv package manager, and make
2. **Dependency Installation**: Runs `make install` to set up all required packages
3. **Credentials Configuration**: Securely loads Google Drive credentials from GitHub Secrets
4. **Preprocessing Execution**: Runs `uv run preprocessing/preprocess.py --deploy` to:
   - Clean and transform raw recipe data
   - Extract nutrition information
   - Compute popularity scores
   - Generate similarity matrices
   - Upload processed datasets to Google Drive
5. **Artifact Upload**: Preserves preprocessing logs for 30 days for debugging and auditing

### Key Features

- **Automated Data Pipeline**: Ensures preprocessed data stays current with code changes
- **Cloud Storage Integration**: Deploys processed datasets to Google Drive for team access
- **Comprehensive Logging**: Captures detailed execution logs for troubleshooting

## Sync to Hugging Face

**Workflow file**: `.github/workflows/sync-to-huggingface.yml`

### Trigger Conditions

This workflow runs when:

- Any changes are pushed to the `main` branch
- The preprocessing workflow completes successfully
- Manually triggered via the Actions tab

### Smart Preprocessing Detection

The workflow includes intelligent logic to determine when it's safe to deploy:

```yaml
check-preprocessing:
  # Detects if preprocessing files changed
  # Waits for preprocessing completion if needed
  # Proceeds immediately if no preprocessing changes
```

If preprocessing scripts were modified, the sync waits for the preprocessing workflow to complete successfully before deploying. This ensures that the application on Hugging Face always runs with the latest processed data.

### Deployment Process

1. **Checkout Latest Code**: Pulls the most recent version of the main branch
2. **Sync with Remote**: Ensures local repository is up to date
3. **Push to Hugging Face**: Deploys code to the Hugging Face Spaces repository using a secure token

### Automatic Updates on Hugging Face

Once the code is pushed to the Hugging Face repository, **Hugging Face Spaces automatically detects the changes and redeploys the application**. This happens without any additional configuration:

- **Automatic Rebuild**: Hugging Face detects the new commit and triggers a rebuild
- **Zero Downtime**: The platform manages the deployment with minimal disruption
- **Build Logs**: Detailed logs are available in the Hugging Face Spaces dashboard
- **Environment**: Hugging Face reads `requirements.txt` or `pyproject.toml` to install dependencies

The live application is hosted at: `https://huggingface.co/spaces/regkhalil/mange-ta-main`

## Documentation Workflow

**Workflow file**: `.github/workflows/docs.yml`

### Trigger Conditions

This workflow runs when changes are pushed to:

- The `docs/` directory
- `mkdocs.yml` configuration file
- Python source files in `services/`, `components/`, `preprocessing/`, or `utils/` (since docstrings may have changed)
- Manually triggered via the Actions tab

### Build and Deploy Process

1. **Setup Environment**: Installs uv and syncs development dependencies
2. **Generate Documentation**: Runs `mkdocs build` to:
   - Convert Markdown files to HTML
   - Extract Python docstrings using mkdocstrings
   - Apply the Material for MkDocs theme
   - Generate search index
3. **Upload Artifact**: Packages the built site for GitHub Pages
4. **Deploy to GitHub Pages**: Publishes the documentation site

### GitHub Pages Configuration

- **URL**: Documentation is published to `https://regkhalil.github.io/mange-ta-main`
- **Permissions**: The workflow has `pages: write` permission to deploy
- **Concurrency Control**: Only one documentation deployment runs at a time
- **Environment**: Deployed to the `github-pages` environment

### What's Included

The documentation site includes:

- **Overview and Getting Started**: Project introduction and setup instructions
- **API Reference**: Auto-generated documentation from Python docstrings
- **Search Functionality**: Full-text search across all documentation
- **Source Links**: Direct links to the GitHub repository

### Automatic Updates

Every time relevant files are changed and pushed to main, the documentation is automatically rebuilt and deployed within minutes. The Material theme provides a modern, responsive interface optimized for technical documentation.

## Secrets Management

The workflows use GitHub Secrets to securely store sensitive credentials:

- `GOOGLE_CREDENTIALS`: Service account JSON for Google Drive API
- `GOOGLE_TOKEN`: OAuth token for Google Drive access
- `GOOGLE_FOLDER_ID`: Target folder ID for preprocessed data uploads
- `HF_TOKEN`: Hugging Face authentication token for repository access

These secrets are configured in the repository settings under **Settings > Secrets and variables > Actions**.

## Workflow Dependencies

The workflows are designed to work together:

```
main branch push
    │
    ├─> [preprocessing changes detected?]
    │       │
    │       ├─> YES: Run preprocessing workflow
    │       │           │
    │       │           └─> On success: Trigger Hugging Face sync
    │       │
    │       └─> NO: Immediately run Hugging Face sync
    │
    ├─> [documentation changes detected?]
    │       │
    │       └─> Build and deploy docs to GitHub Pages
    │
    └─> [code changes]
            │
            └─> Sync to Hugging Face (with preprocessing check)
```

This orchestration ensures that:

1. Data preprocessing completes before application deployment
2. Documentation stays synchronized with code changes
3. Manual triggers are available for emergency updates

## Monitoring and Debugging

### Viewing Workflow Runs

1. Navigate to the **Actions** tab in the GitHub repository
2. Select the workflow you want to inspect
3. Click on a specific run to view logs and artifacts

### Checking Deployment Status

- **Hugging Face**: Visit the Space's build logs at `https://huggingface.co/spaces/regkhalil/mange-ta-main`
- **GitHub Pages**: Check the deployment status in the Actions tab under the "Docs" workflow

### Accessing Logs

- **Preprocessing Logs**: Downloaded as artifacts from the workflow run (retained for 30 days)
- **Build Logs**: Available in the workflow run details on GitHub
- **Deployment Logs**: Visible in Hugging Face Spaces dashboard

## Manual Workflow Execution

All workflows support manual triggering:

1. Go to **Actions** tab
2. Select the workflow
3. Click **Run workflow**
4. Choose the branch (typically `main`)
5. Click **Run workflow** button

This is useful for:

- Reprocessing data after fixing a bug
- Forcing a redeploy without code changes
- Rebuilding documentation after configuration updates
