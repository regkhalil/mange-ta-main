"""
Google Drive uploader module for preprocessing outputs.

This module handles uploading preprocessed data files to Google Drive
using OAuth 2.0 authentication with token caching for CI/CD automation.

Authentication Flow:
1. First run: Interactive login (browser or console) creates token.json
2. Subsequent runs: Automatic token refresh using token.json
3. CI/CD: Copy token.json to CI/CD environment as a secret
4. Cloud deployment: Use environment variables (Hugging Face Spaces)

The token.json file contains a refresh token that allows indefinite
re-authentication without requiring interactive login.
"""

import json
import logging
import os

# Import secrets manager for cloud deployments
import sys
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.secrets import get_google_credentials_json, get_google_folder_id, get_google_token_json

logger = logging.getLogger(__name__)

# Credentials file location
CREDENTIALS_DIR = Path.cwd() / "credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"
FOLDER_ID_FILE = CREDENTIALS_DIR / "folder_id.txt"

# Google Drive API scopes - using drive.file for app-specific access
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Credentials file location
CREDENTIALS_DIR = Path.cwd() / "credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"
FOLDER_ID_FILE = CREDENTIALS_DIR / "folder_id.txt"


def get_oauth_credentials() -> Optional[Credentials]:
    """
    Gets valid OAuth credentials from token.json, environment variables, or initiates auth flow.

    This function:
    1. Tries to load from environment variables (cloud deployments)
    2. Loads existing token.json if available (local/CI/CD)
    3. Refreshes expired tokens automatically
    4. Initiates OAuth flow only if no valid token exists
    5. Saves token.json for future use (including refresh token)

    For CI/CD:
    - Run locally once to generate token.json
    - Copy token.json to CI/CD as a secret
    - All subsequent runs use the cached token

    For Cloud Deployments (Hugging Face, etc.):
    - Set GOOGLE_TOKEN and GOOGLE_CREDENTIALS environment variables
    - No file-based authentication needed

    Returns:
        Valid credentials or None if authentication fails
    """
    creds = None

    # Step 1: Try to load from environment variables (for cloud deployments)
    token_json = get_google_token_json()
    if token_json:
        try:
            creds = Credentials.from_authorized_user_info(token_json, SCOPES)
            logger.info("Loaded credentials from environment variables")

            # Refresh if expired
            if creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired token from environment...")
                    creds.refresh(Request())
                    logger.info("✓ Token refreshed successfully")
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    creds = None

            if creds and creds.valid:
                return creds
        except Exception as e:
            logger.warning(f"Failed to load credentials from environment: {e}")

    # Step 2: Try to load existing token from file
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            logger.info("Loaded existing credentials from token.json")
        except Exception as e:
            logger.warning(f"Failed to load token.json: {e}")
            creds = None

    # Step 3: Refresh if expired, or get new token if none exists
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired token...")
                creds.refresh(Request())
                logger.info("✓ Token refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                logger.error("You may need to re-authenticate (delete token.json and run again)")
                return None
        else:
            # Step 4: Try to get credentials from environment for initial setup
            creds_json = get_google_credentials_json()
            if creds_json:
                try:
                    logger.info("Using credentials from environment variables")
                    # Create a temporary credentials file
                    temp_creds_path = Path("/tmp/google_credentials.json")
                    temp_creds_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(temp_creds_path, "w") as f:
                        json.dump(creds_json, f)

                    flow = InstalledAppFlow.from_client_secrets_file(str(temp_creds_path), SCOPES)

                    # Try to run without browser (for cloud environments)
                    try:
                        creds = flow.run_console()
                    except Exception:
                        logger.warning("Console authentication not available in cloud environment")
                        return None

                    # Clean up temp file
                    temp_creds_path.unlink()

                    if creds:
                        return creds
                except Exception as e:
                    logger.warning(f"Failed to authenticate with environment credentials: {e}")

            # Step 5: No valid token - need to authenticate with local file
            if not CREDENTIALS_PATH.exists():
                logger.error(f"Credentials file not found at {CREDENTIALS_PATH}")
                logger.error("Please download OAuth 2.0 credentials from Google Cloud Console")
                logger.error("See GDRIVE_SETUP.md for instructions")
                return None

            try:
                logger.info("=" * 70)
                logger.info("FIRST-TIME AUTHENTICATION REQUIRED")
                logger.info("=" * 70)
                logger.info("This is a one-time process. The token will be saved for future use.")
                logger.info("")

                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)

                # Try browser-based auth first
                try:
                    logger.info("Attempting to open browser for authentication...")
                    creds = flow.run_local_server(port=0)
                    logger.info("✓ Authentication successful!")
                except Exception as browser_error:
                    # If browser fails, likely running in headless/remote environment
                    logger.warning(f"Browser authentication failed: {browser_error}")
                    logger.info("\nFor remote/headless environments:")
                    logger.info("=" * 70)
                    logger.info("Run this command on a machine with a browser:")
                    logger.info("  python preprocessing/gdrive_uploader.py")
                    logger.info("")
                    logger.info("Then copy the generated token.json file to this machine:")
                    logger.info(f"  {TOKEN_PATH}")
                    logger.info("=" * 70)
                    raise
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                logger.error("\nTroubleshooting:")
                logger.error("1. Ensure credentials.json is in the credentials/ folder")
                logger.error("2. Check that Google Drive API is enabled in Google Cloud Console")
                logger.error("3. Verify OAuth consent screen is configured")
                return None

        # Step 6: Save the credentials for future use
        if creds:
            try:
                CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
                with open(TOKEN_PATH, "w") as token:
                    token.write(creds.to_json())
                logger.info(f"✓ Token saved to {TOKEN_PATH}")
                logger.info("This token can be reused in CI/CD environments")
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

    return creds


def get_or_create_folder(service, folder_name: str = "mangetamain-data") -> Optional[str]:
    """
    Gets or creates a dedicated folder for the app's data.

    Checks environment variables first, then cached file, then searches/creates.

    Args:
        service: Authenticated Drive API service
        folder_name: Name of the folder to create

    Returns:
        Folder ID or None if operation failed
    """
    # Check if we have a folder ID from environment variables (for cloud deployments)
    env_folder_id = get_google_folder_id()
    if env_folder_id:
        try:
            # Verify the folder exists
            service.files().get(fileId=env_folder_id, fields="id,name").execute()
            logger.info(f"Using folder ID from environment: {env_folder_id}")
            return env_folder_id
        except HttpError as e:
            logger.warning(f"Environment folder ID is invalid: {e}")

    # Check if we have a cached folder ID (for local/CI-CD)
    if FOLDER_ID_FILE.exists():
        try:
            with open(FOLDER_ID_FILE, "r") as f:
                folder_id = f.read().strip()

            # Verify the folder still exists
            try:
                service.files().get(fileId=folder_id, fields="id,name").execute()
                logger.info(f"Using existing folder ID: {folder_id}")
                return folder_id
            except HttpError:
                logger.warning("Cached folder ID is invalid, will create new folder")
        except Exception as e:
            logger.warning(f"Failed to read cached folder ID: {e}")

    # Search for existing folder
    try:
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        folders = results.get("files", [])

        if folders:
            folder_id = folders[0]["id"]
            logger.info(f"Found existing folder: {folder_name} (ID: {folder_id})")
            # Cache the folder ID
            CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
            with open(FOLDER_ID_FILE, "w") as f:
                f.write(folder_id)
            return folder_id
    except HttpError as error:
        logger.warning(f"Error searching for folder: {error}")

    # Create new folder
    try:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=file_metadata, fields="id").execute()
        folder_id = folder.get("id")
        logger.info(f"Created new folder: {folder_name} (ID: {folder_id})")

        # Cache the folder ID
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        with open(FOLDER_ID_FILE, "w") as f:
            f.write(folder_id)

        return folder_id
    except HttpError as error:
        logger.error(f"Failed to create folder: {error}")
        return None


def find_file_in_folder(service, folder_id: str, file_name: str) -> Optional[str]:
    """
    Searches for a file by name in a specific folder.

    Args:
        service: Authenticated Drive API service
        folder_id: ID of the folder to search in
        file_name: Name of the file to search for

    Returns:
        File ID if found, None otherwise
    """
    try:
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        files = results.get("files", [])

        if files:
            logger.info(f"Found existing file: {file_name} (ID: {files[0].get('id')})")
            return files[0].get("id")

        return None

    except HttpError as error:
        logger.warning(f"Error searching for file: {error}")
        return None


def upload_file_to_drive(file_path: str, file_name: Optional[str] = None, mime_type: str = "text/csv") -> Optional[str]:
    """
    Uploads a file to Google Drive using OAuth credentials.

    Args:
        file_path: Path to the file to upload
        file_name: Optional custom name for the file (defaults to original filename)
        mime_type: MIME type of the file (default: text/csv)

    Returns:
        File ID of the uploaded file, or None if upload failed
    """
    try:
        creds = get_oauth_credentials()
        if not creds:
            logger.error("Failed to get OAuth credentials")
            return None

        # Build Drive API service
        service = build("drive", "v3", credentials=creds)

        # Get or create the app folder
        folder_id = get_or_create_folder(service)
        if not folder_id:
            logger.error("Failed to get or create folder")
            return None

        # Prepare file metadata
        file_name = file_name or Path(file_path).name
        file_metadata = {"name": file_name, "parents": [folder_id]}

        # Get file size for progress reporting
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        # Create media upload with chunked resumable upload
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True, chunksize=10 * 1024 * 1024)

        # Check if file already exists in folder
        existing_file_id = find_file_in_folder(service, folder_id, file_name)

        if existing_file_id:
            # Update existing file
            logger.info(f"Updating existing file: {file_name} ({file_size_mb:.1f} MB)")
            request = service.files().update(fileId=existing_file_id, media_body=media, fields="id,name,size")
        else:
            # Upload new file
            logger.info(f"Uploading new file: {file_name} ({file_size_mb:.1f} MB)")
            request = service.files().create(body=file_metadata, media_body=media, fields="id,name,size")

        # Execute the upload with progress tracking
        response = None
        last_progress = 0
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                # Log progress every 10%
                if progress >= last_progress + 10:
                    logger.info(f"  Progress: {progress}%")
                    last_progress = progress

        file = response
        logger.info(f"✓ Completed: {file.get('name')} (ID: {file.get('id')}, Size: {file.get('size')} bytes)")

        return file.get("id")

    except HttpError as error:
        logger.error(f"HTTP error occurred: {error}")
        return None
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        return None


def upload_preprocessing_outputs(data_dir: str) -> bool:
    """
    Uploads all files from the data directory to Google Drive.

    Args:
        data_dir: Directory containing the files to upload

    Returns:
        True if all uploads succeeded, False otherwise
    """
    # Get all files in the data directory
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return False

    # Collect all files (excluding subdirectories)
    all_files = []
    for file_path in data_path.iterdir():
        if file_path.is_file():
            all_files.append(file_path)

    if not all_files:
        logger.warning(f"No files found in {data_dir}")
        return True

    # Determine MIME type based on file extension
    def get_mime_type(file_path: Path) -> str:
        ext = file_path.suffix.lower()
        mime_types = {
            ".csv": "text/csv",
            ".pkl": "application/octet-stream",
            ".json": "application/json",
            ".txt": "text/plain",
            ".parquet": "application/octet-stream",
        }
        return mime_types.get(ext, "application/octet-stream")

    success = True
    uploaded_files = []
    failed_files = []

    logger.info("=" * 70)
    logger.info("Starting upload to Google Drive")
    logger.info(f"Found {len(all_files)} files to upload from {data_dir}")
    logger.info("=" * 70)

    for file_path in sorted(all_files):
        file_name = file_path.name
        mime_type = get_mime_type(file_path)

        logger.info(f"\nUploading: {file_name}")
        file_id = upload_file_to_drive(str(file_path), file_name, mime_type)

        if file_id:
            uploaded_files.append(file_name)
            logger.info(f"✓ Successfully uploaded: {file_name}")
        else:
            success = False
            failed_files.append(file_name)
            logger.error(f"✗ Failed to upload: {file_name}")

    logger.info("\n" + "=" * 70)
    logger.info(f"Upload complete: {len(uploaded_files)}/{len(all_files)} files uploaded")
    logger.info("=" * 70)

    if uploaded_files:
        logger.info("\nSuccessfully uploaded files:")
        for file_name in uploaded_files:
            logger.info(f"  ✓ {file_name}")

    if failed_files:
        logger.info("\nFailed to upload:")
        for file_name in failed_files:
            logger.info(f"  ✗ {file_name}")

    return success


def list_drive_files(service=None) -> List[dict]:
    """
    Lists all files in the app's Google Drive folder.

    Args:
        service: Optional authenticated Drive API service

    Returns:
        List of file metadata dictionaries
    """
    try:
        if service is None:
            creds = get_oauth_credentials()
            if not creds:
                return []
            service = build("drive", "v3", credentials=creds)

        # Get the folder ID
        folder_id = get_or_create_folder(service)
        if not folder_id:
            return []

        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id, name, size, createdTime, modifiedTime)").execute()

        files = results.get("files", [])
        return files

    except HttpError as error:
        logger.error(f"Error listing files: {error}")
        return []
