"""
Data loading and preprocessing service for the Mangetamain application.

This module centralizes all CSV file reading operations from the data/ folder.
All loading functions use standardized paths and consistent parameters.
"""

import io
import logging
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Import secrets helper for cross-platform compatibility
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.secrets import get_google_folder_id, get_google_token_json, get_secret

# Setup logger
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT AND GOOGLE DRIVE CONFIGURATION
# ============================================================================

# Check if running in production mode
ENV = get_secret("STREAMLIT_ENV", "dev")
IS_PRODUCTION = ENV == "prod"


def _get_gdrive_service():
    """
    Gets an authenticated Google Drive API service.
    Uses credentials from environment variables.

    Only called in production mode.

    Returns:
        Google Drive API service or None if authentication fails
    """
    try:
        # Get token from environment variables
        token_data = get_google_token_json()

        if not token_data:
            error_msg = "Google Drive credentials not found in environment variables."
            logger.error(error_msg)
            st.error(error_msg)
            return None

        creds = Credentials.from_authorized_user_info(token_data)

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Google Drive token...")
            creds.refresh(Request())
            logger.info("Token refreshed successfully")

        if not creds or not creds.valid:
            error_msg = "Invalid or missing Google Drive credentials"
            logger.error(error_msg)
            st.error(error_msg)
            return None

        logger.info("Successfully authenticated with Google Drive")
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        error_msg = f"Failed to authenticate with Google Drive: {e}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def _download_file_from_gdrive(filename: str) -> Optional[bytes]:
    """
    Downloads a file from Google Drive by name.
    Uses folder ID from Streamlit secrets.

    Args:
        filename: Name of the file to download

    Returns:
        File content as bytes or None if download failed
    """
    try:
        from googleapiclient.http import MediaIoBaseDownload

        logger.info(f"Attempting to download {filename} from Google Drive...")

        service = _get_gdrive_service()
        if not service:
            return None

        # Get folder ID from environment variables
        folder_id = get_google_folder_id()

        if not folder_id:
            error_msg = "Google Drive folder_id not found in environment variables."
            logger.error(error_msg)
            st.error(error_msg)
            return None

        # Search for the file in the folder
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        files = results.get("files", [])

        if not files:
            error_msg = f"File not found in Google Drive: {filename}"
            logger.error(error_msg)
            st.error(error_msg)
            return None

        file_id = files[0]["id"]
        logger.info(f"Found {filename} in Google Drive (ID: {file_id})")

        # Download the file
        request = service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")

        file_buffer.seek(0)
        file_content = file_buffer.read()
        logger.info(f"Successfully downloaded {filename} ({len(file_content)} bytes)")
        return file_content

    except Exception as e:
        error_msg = f"Failed to download {filename} from Google Drive: {e}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return None


# ============================================================================
# CENTRALIZED CSV LOADING FUNCTIONS
# ============================================================================


def _get_data_dir(data_dir: Optional[str] = None) -> Path:
    """
    Returns the path to the data/ directory.

    Args:
        data_dir: Custom path or None to use the default path

    Returns:
        Path: Path to the data/ directory
    """
    if data_dir is None:
        return Path.cwd() / "data"
    return Path(data_dir)


@st.cache_data(hash_funcs={list: lambda x: str(x)})
def read_csv_file(
    filename: str,
    data_dir: Optional[str] = None,
    usecols: Optional[List[str]] = None,
    dtype: Optional[dict] = None,
    nrows: Optional[int] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Centralized function to read any CSV file from the data/ folder.
    In production mode (ENV=prod), reads from Google Drive.
    In development mode, reads from local data/ directory.

    This function standardizes CSV reading with error handling
    and integrated Streamlit caching.

    Args:
        filename: Name of the CSV file (e.g., "preprocessed_recipes.csv")
        data_dir: Directory containing the data (default: "data/")
        usecols: List of columns to load (default: all)
        dtype: Dictionary of column types
        nrows: Maximum number of rows to read
        **kwargs: Additional arguments for pd.read_csv()

    Returns:
        pd.DataFrame: DataFrame containing the data

    Raises:
        FileNotFoundError: If the file does not exist
    """

    logger.info(f"Reading csv file {filename}")

    # Merge default parameters with kwargs
    read_params = {"low_memory": False, **kwargs}

    if usecols is not None:
        read_params["usecols"] = usecols
    if dtype is not None:
        read_params["dtype"] = dtype
    if nrows is not None:
        read_params["nrows"] = nrows

    # Production mode: read from Google Drive (required)
    if IS_PRODUCTION:
        file_content = _download_file_from_gdrive(filename)

        if file_content is None:
            raise FileNotFoundError(
                f"Failed to download {filename} from Google Drive. "
                "Ensure Google Drive credentials are configured correctly."
            )

        # Successfully downloaded from Google Drive
        # When reading from BytesIO, pandas sometimes auto-converts string representations
        # of lists to actual list objects. Use converters to force them to stay as strings.
        # Common columns that contain list-like strings
        list_columns = [
            "tags",
            "steps",
            "ingredients",
            "nutrition",
            "techniques",
            "ingredient_ids",
            "name_tokens",
            "ingredient_tokens",
            "steps_tokens",
            "items",
            "ratings",
        ]

        # Only apply converters to columns that aren't already specified in dtype
        if dtype:
            converters = {col: str for col in list_columns if col not in dtype}
        else:
            converters = {col: str for col in list_columns}

        # Add converters to read_params if not already specified
        if "converters" not in read_params:
            read_params["converters"] = converters

        df = pd.read_csv(io.BytesIO(file_content), **read_params)
        return df

    # Development mode: read from local file system
    data_path = _get_data_dir(data_dir)
    file_path = data_path / filename

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path, **read_params)
    return df



# ============================================================================
# EXISTING FUNCTIONS (UPDATED TO USE THE NEW CENTRALIZED FUNCTIONS)
# ============================================================================


@st.cache_data(show_spinner=False, hash_funcs={list: lambda x: str(x)})  # Disable default spinner, we manage manually
def load_recipes(data_dir: str = None) -> pd.DataFrame:
    """
    Loads and preprocesses recipe data from preprocessed_recipes.csv

    The file now includes popularity statistics (review_count, average_rating, popularity_score)
    calculated from RAW_interactions.csv.

    Returns:
        DataFrame with preprocessed columns including popularity statistics
    """

    # Load enriched preprocessed data with popularity statistics
    df = read_csv_file(
        "preprocessed_recipes.csv",
        data_dir=data_dir,
        dtype={
            "id": "int64",
            "minutes": "float32",
            "n_steps": "float32",
            "n_ingredients": "float32",
            "review_count": "int32",
            "average_rating": "float32",
            "popularity_score": "float32",
        },
    )

    # Verify that popularity columns exist
    # required_popularity_cols = ["review_count", "average_rating", "popularity_score"]

    return df

    # Note: nutrition_score, nutrition_grade, nutrition array, and calories
    # are already computed in preprocessing - no need to calculate here
    # Average rating can be added as a separate function when needed



def get_recipe_name(recipe_id: int, recipes_df: pd.DataFrame) -> str:
    """
    Retrieves the readable name of a recipe from its tokens.

    Args:
        recipe_id: Recipe ID
        recipes_df: Recipes DataFrame

    Returns:
        Recipe name (approximate based on tokens)
    """
    recipe = recipes_df[recipes_df["id"] == recipe_id]
    if recipe.empty:
        return f"Recipe #{recipe_id}"

    # Simplify for display
    return f"Recipe #{recipe_id}"


def get_recipe_details(recipe_id: int, recipes_df: pd.DataFrame) -> dict:
    """
    Retrieves all details of a recipe.

    Args:
        recipe_id: Recipe ID
        recipes_df: Recipes DataFrame

    Returns:
        Dictionary with recipe details
    """
    recipe = recipes_df[recipes_df["id"] == recipe_id].iloc[0]

    return {
        "id": recipe["id"],
        "name": get_recipe_name(recipe_id, recipes_df),
        "ingredients": len(recipe["ingredient_tokens"]),
        "steps": len(recipe["steps_tokens"]),
        "calories": recipe["calories"],
        "minutes": recipe["minutes"],
        "is_vegetarian": recipe["is_vegetarian"],
        "techniques": recipe["techniques"],
        "calorie_level": recipe["calorie_level"],
    }


def filter_recipes(
    recipes_df: pd.DataFrame,
    prep_range: tuple = (0, 180),
    ingredients_range: tuple = (1, 30),
    calories_range: tuple = (0, 1000),
    vegetarian_only: bool = False,
    nutrition_grades: list = None,
) -> pd.DataFrame:
    """
    Filters recipes according to specified criteria.

    Args:
        recipes_df: Recipes DataFrame
        prep_range: Tuple (min, max) for preparation time
        ingredients_range: Tuple (min, max) for number of ingredients
        calories_range: Tuple (min, max) for calories
        vegetarian_only: Filter only vegetarian recipes
        nutrition_grades: List of accepted nutritional grades (A, B, C, D, E)

    Returns:
        Filtered DataFrame
    """
    result = recipes_df.copy()

    # Determine time columns (try totalTime first, then minutes)
    time_col = "minutes"

    # Determine ingredient columns - always use n_ingredients now
    ing_col = "n_ingredients"

    # Determine calorie columns
    cal_col = "calories" if "calories" in recipes_df.columns else None

    # Filter by preparation time
    if time_col in result.columns:
        result = result[(result[time_col] >= prep_range[0]) & (result[time_col] <= prep_range[1])]

    # Filter by number of ingredients
    if ing_col in result.columns:
        result = result[(result[ing_col] >= ingredients_range[0]) & (result[ing_col] <= ingredients_range[1])]

    # Filter by calories (if column exists)
    if cal_col and cal_col in result.columns:
        result = result[(result[cal_col] >= calories_range[0]) & (result[cal_col] <= calories_range[1])]

    # Vegetarian filter
    if vegetarian_only:
        result = result[result["is_vegetarian"]]

    # Nutritional grades filter
    if nutrition_grades and len(nutrition_grades) > 0 and "nutrition_grade" in result.columns:
        result = result[result["nutrition_grade"].isin(nutrition_grades)]

    return result


def get_recipe_stats(recipes_df: pd.DataFrame) -> dict:
    """
    Calculates global statistics on recipes.

    Args:
        recipes_df: Recipes DataFrame

    Returns:
        Dictionary with statistics
    """
    return {
        "total_recipes": len(recipes_df),
        "avg_prep_time": recipes_df["minutes"].mean(),
        "median_prep_time": recipes_df["minutes"].median(),
        "avg_ingredients": recipes_df["n_ingredients"].mean(),
        "avg_calories": recipes_df["calories"].mean(),
        "vegetarian_count": recipes_df["is_vegetarian"].sum(),
        "vegetarian_percentage": (recipes_df["is_vegetarian"].sum() / len(recipes_df)) * 100,
    }
