#!/usr/bin/env python3
"""
Helper script to list files in Google Drive appDataFolder.

This script helps you verify what files have been uploaded to Google Drive
by the preprocessing script with --deploy flag.

Usage:
    python list_gdrive_files.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import gdrive_uploader
sys.path.insert(0, str(Path(__file__).parent))

from gdrive_uploader import get_service_account_credentials, list_drive_files
from googleapiclient.discovery import build


def main():
    """List all files in the app's Google Drive folder."""
    print("=" * 70)
    print("Google Drive - File List")
    print("=" * 70)

    # Get credentials
    creds = get_service_account_credentials()
    if not creds:
        print("\n✗ Failed to authenticate with Google Drive")
        print("Please ensure service-account.json is set up correctly.")
        print("See GDRIVE_SETUP.md for instructions.")
        return 1

    # Build service
    service = build("drive", "v3", credentials=creds)

    # List files
    files = list_drive_files(service)

    if not files:
        print("\nNo files found in Google Drive folder.")
        print("Run preprocessing with --deploy flag to upload files.")
        return 0

    print(f"\nFound {len(files)} file(s):\n")

    # Display file information
    for idx, file in enumerate(files, 1):
        print(f"{idx}. {file['name']}")
        print(f"   ID: {file['id']}")
        if "size" in file:
            size_mb = int(file["size"]) / (1024 * 1024)
            print(f"   Size: {size_mb:.2f} MB")
        if "createdTime" in file:
            print(f"   Created: {file['createdTime']}")
        if "modifiedTime" in file:
            print(f"   Modified: {file['modifiedTime']}")
        print()

    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
