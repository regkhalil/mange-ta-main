"""
Data loading and preprocessing service for the Mangetamain application.

This module centralizes all CSV file reading operations from the data/ folder.
All loading functions use standardized paths and consistent parameters.
"""

import io
import logging
import os
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Setup logger
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT AND GOOGLE DRIVE CONFIGURATION
# ============================================================================

# Check if running in production mode
ENV = os.getenv("STREAMLIT_ENV", "dev")
IS_PRODUCTION = ENV == "prod"


def _get_gdrive_service():
    """
    Gets an authenticated Google Drive API service.
    Uses credentials from Streamlit secrets.

    Returns:
        Google Drive API service or None if authentication fails
    """
    try:
        import json

        # Get token from Streamlit secrets
        if "google" not in st.secrets or "token" not in st.secrets["google"]:
            error_msg = "Google Drive credentials not found in Streamlit secrets."
            logger.error(error_msg)
            st.error(error_msg)
            return None

        # Parse token from Streamlit secrets
        token_data = json.loads(st.secrets["google"]["token"])
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

        # Get folder ID from Streamlit secrets
        if "google" not in st.secrets or "folder_id" not in st.secrets["google"]:
            error_msg = "Google Drive folder_id not found in Streamlit secrets."
            logger.error(error_msg)
            st.error(error_msg)
            return None

        folder_id = st.secrets["google"]["folder_id"]

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


@st.cache_data
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


@st.cache_data
def read_preprocessed_recipes(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the preprocessed_recipes.csv file with optimized data types.

    Args:
        data_dir: Directory containing the data

    Returns:
        pd.DataFrame: Preprocessed recipes
    """
    return read_csv_file(
        "preprocessed_recipes.csv",
        data_dir=data_dir,
        dtype={
            "id": "int64",
            "minutes": "float32",
            "n_steps": "float32",
            "n_ingredients": "float32",
        },
    )


@st.cache_data
def read_raw_recipes(
    data_dir: Optional[str] = None, usecols: Optional[List[str]] = None, nrows: Optional[int] = None
) -> pd.DataFrame:
    """
    Loads the RAW_recipes.csv file.

    Args:
        data_dir: Directory containing the data
        usecols: Specific columns to load (e.g., ["id", "description"])
        nrows: Maximum number of rows to read

    Returns:
        pd.DataFrame: Raw recipes
    """
    return read_csv_file("RAW_recipes.csv", data_dir=data_dir, usecols=usecols, nrows=nrows)


@st.cache_data
def read_pp_recipes(data_dir: Optional[str] = None, nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Loads the PP_recipes.csv file.

    Args:
        data_dir: Directory containing the data
        nrows: Maximum number of rows to read

    Returns:
        pd.DataFrame: Preprocessed recipes (PP format)
    """
    return read_csv_file("PP_recipes.csv", data_dir=data_dir, nrows=nrows)


@st.cache_data
def read_pp_users(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the PP_users.csv file.

    Args:
        data_dir: Directory containing the data

    Returns:
        pd.DataFrame: User profiles
    """
    return read_csv_file("PP_users.csv", data_dir=data_dir)


@st.cache_data
def read_raw_interactions(data_dir: Optional[str] = None, usecols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Loads the RAW_interactions.csv file.

    Args:
        data_dir: Directory containing the data
        usecols: Specific columns to load (e.g., ["recipe_id", "rating"])

    Returns:
        pd.DataFrame: User-recipe interactions
    """
    dtype_dict = (
        {"recipe_id": "int64", "rating": "float32"}
        if usecols is None or set(usecols) & {"recipe_id", "rating"}
        else None
    )

    return read_csv_file("RAW_interactions.csv", data_dir=data_dir, usecols=usecols, dtype=dtype_dict)


@st.cache_data
def read_interactions_split(split: str = "train", data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Loads a split interactions file (train/validation/test).

    Args:
        split: Type of split ("train", "validation", or "test")
        data_dir: Directory containing the data

    Returns:
        pd.DataFrame: Interactions from the specified split
    """
    valid_splits = ["train", "validation", "test"]
    if split not in valid_splits:
        raise ValueError(f"split must be in {valid_splits}, got: {split}")

    return read_csv_file(f"interactions_{split}.csv", data_dir=data_dir)


# ============================================================================
# EXISTING FUNCTIONS (UPDATED TO USE THE NEW CENTRALIZED FUNCTIONS)
# ============================================================================


@st.cache_data(show_spinner=False)  # Disable default spinner, we manage manually
def load_recipes(data_dir: str = None) -> pd.DataFrame:
    """
    Loads and preprocesses recipe data from PP_recipes.csv and RAW_recipes.csv.
    Merges both to have features AND searchable texts.

    Returns:
        DataFrame with preprocessed columns for the application
    """
    data_dir_path = _get_data_dir(data_dir)

    # Check if preprocessed file exists
    preprocessed_path = data_dir_path / "preprocessed_recipes.csv"

    if preprocessed_path.exists():
        # Load enriched preprocessed data (uses read_preprocessed_recipes)
        # Note: This already includes description, nutrition, tags, etc. from preprocessing
        df = read_preprocessed_recipes(data_dir=data_dir)

        # Create derived columns for UI (if they don't exist)
        if "ingredientCount" not in df.columns and "n_ingredients" in df.columns:
            df["ingredientCount"] = df["n_ingredients"]

        if "stepsCount" not in df.columns and "n_steps" in df.columns:
            df["stepsCount"] = df["n_steps"]

        if "totalTime" not in df.columns and "minutes" in df.columns:
            df["totalTime"] = df["minutes"].clip(5, 300)  # Limit between 5 and 300 minutes

        # Create alias for compatibility
        if "isVegetarian" not in df.columns:
            if "is_vegetarian" in df.columns:
                df["isVegetarian"] = df["is_vegetarian"]
            else:
                df["isVegetarian"] = False

        # Note: nutrition_score, nutrition_grade, nutrition array, and calories
        # are already computed in preprocessing - no need to calculate here
        # Average rating can be added as a separate function when needed

    else:
        # Fallback: load from PP_recipes and RAW_recipes
        df = read_pp_recipes(data_dir=data_dir, nrows=10000)
        raw_df = read_raw_recipes(data_dir=data_dir)
        raw_df = raw_df[["id", "name", "ingredients", "steps"]]
        df = df.merge(raw_df, on="id", how="left")

        df["name_tokens"] = df["name_tokens"].apply(eval)
        df["ingredient_tokens"] = df["ingredient_tokens"].apply(eval)
        df["steps_tokens"] = df["steps_tokens"].apply(eval)
        df["techniques"] = df["techniques"].apply(eval)
        df["ingredient_ids"] = df["ingredient_ids"].apply(eval)

        df["ingredientCount"] = df["ingredient_tokens"].apply(len)
        df["stepsCount"] = df["steps_tokens"].apply(len)

        calorie_mapping = {0: 200, 1: 400, 2: 600, 3: 800}
        df["calories"] = df["calorie_level"].map(calorie_mapping)
        df["totalTime"] = df["stepsCount"] * 5 + df["techniques"].apply(lambda x: sum(x)) * 2
        df["totalTime"] = df["totalTime"].clip(5, 180)

        if "nutrition_score" not in df.columns:
            df["nutrition_score"] = np.nan
        if "nutrition_grade" not in df.columns:
            df["nutrition_grade"] = None
        if "is_vegetarian" not in df.columns:
            df["is_vegetarian"] = df["ingredient_ids"].apply(lambda ids: all(id not in [389, 7655] for id in ids))

        df["isVegetarian"] = df.get("is_vegetarian", False)

    return df


@st.cache_data
def load_users(data_dir: str = None) -> pd.DataFrame:
    """
    Loads user data from PP_users.csv.

    Returns:
        DataFrame with user profiles
    """
    # Use centralized function
    df = read_pp_users(data_dir=data_dir)

    # Convert list columns
    df["techniques"] = df["techniques"].apply(eval)
    df["items"] = df["items"].apply(eval)
    df["ratings"] = df["ratings"].apply(eval)

    return df


@st.cache_data
def load_interactions(data_dir: str = None, split: str = "train") -> pd.DataFrame:
    """
    Loads user-recipe interactions.

    Args:
        data_dir: Directory containing the data
        split: 'train', 'validation', or 'test'

    Returns:
        DataFrame of interactions
    """
    # Use centralized function
    df = read_interactions_split(split=split, data_dir=data_dir)
    return df


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
        "totalTime": recipe["totalTime"],
        "isVegetarian": recipe["isVegetarian"],
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
    time_col = "totalTime" if "totalTime" in recipes_df.columns else "minutes"

    # Determine ingredient columns
    ing_col = "ingredientCount" if "ingredientCount" in recipes_df.columns else "n_ingredients"

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
        if "isVegetarian" in result.columns:
            result = result[result["isVegetarian"]]
        elif "is_vegetarian" in result.columns:
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
        "avg_prep_time": recipes_df["totalTime"].mean(),
        "median_prep_time": recipes_df["totalTime"].median(),
        "avg_ingredients": recipes_df["ingredientCount"].mean(),
        "avg_calories": recipes_df["calories"].mean(),
        "vegetarian_count": recipes_df["isVegetarian"].sum(),
        "vegetarian_percentage": (recipes_df["isVegetarian"].sum() / len(recipes_df)) * 100,
    }
