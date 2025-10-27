"""
Test suite for centralized CSV data loading.

This module tests all the new centralized CSV loading functions
in services/data_loader.py using pytest.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

# Add root directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable Streamlit cache for tests
os.environ["STREAMLIT_SERVER_ENABLE_STATIC_SERVING"] = "false"

from services.data_loader import (
    load_interactions,
    load_recipes,
    load_users,
    read_csv_file,
    read_interactions_split,
    read_pp_recipes,
    read_pp_users,
    read_preprocessed_recipes,
    read_raw_interactions,
    read_raw_recipes,
)


# Test fixtures
@pytest.fixture
def data_dir():
    """Fixture providing the data directory path."""
    return "data"


@pytest.fixture
def recipes_df(data_dir):
    """Fixture providing loaded recipes DataFrame."""
    return load_recipes(data_dir=data_dir)


@pytest.fixture
def users_df(data_dir):
    """Fixture providing loaded users DataFrame."""
    return load_users(data_dir=data_dir)


@pytest.fixture
def interactions_df(data_dir):
    """Fixture providing loaded interactions DataFrame."""
    return load_interactions(data_dir=data_dir, split="train")


# ============================================================================
# Tests for centralized CSV reading functions
# ============================================================================


class TestCentralizedCSVFunctions:
    """Test suite for centralized CSV loading functions."""

    def test_read_csv_file_generic(self, data_dir):
        """Test generic CSV file reading."""
        df = read_csv_file("preprocessed_recipes.csv", data_dir=data_dir, nrows=10)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df) <= 10

    def test_read_csv_file_with_usecols(self, data_dir):
        """Test CSV reading with specific columns."""
        df = read_csv_file("preprocessed_recipes.csv", data_dir=data_dir, usecols=["id"], nrows=10)
        assert isinstance(df, pd.DataFrame)
        assert "id" in df.columns
        assert len(df.columns) == 1

    def test_read_csv_file_not_found(self, data_dir):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            read_csv_file("nonexistent_file.csv", data_dir=data_dir)

    def test_read_preprocessed_recipes(self, data_dir):
        """Test loading preprocessed recipes."""
        df = read_preprocessed_recipes(data_dir=data_dir)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "id" in df.columns

    def test_read_raw_recipes(self, data_dir):
        """Test loading raw recipes."""
        df = read_raw_recipes(data_dir=data_dir, usecols=["id", "description"], nrows=100)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df) <= 100
        assert "id" in df.columns
        assert "description" in df.columns

    def test_read_pp_recipes(self, data_dir):
        """Test loading PP recipes."""
        df = read_pp_recipes(data_dir=data_dir, nrows=100)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df) <= 100
        assert "id" in df.columns

    def test_read_pp_users(self, data_dir):
        """Test loading user profiles."""
        df = read_pp_users(data_dir=data_dir)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        # User column can be named 'u', 'user_id', or 'id'
        assert any(
            col in df.columns for col in ["u", "user_id", "id"]
        ), f"No user ID column found. Available columns: {list(df.columns)}"

    def test_read_raw_interactions(self, data_dir):
        """Test loading raw interactions."""
        df = read_raw_interactions(data_dir=data_dir, usecols=["recipe_id", "rating"])
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "recipe_id" in df.columns
        assert "rating" in df.columns

    @pytest.mark.parametrize("split", ["train", "validation", "test"])
    def test_read_interactions_split(self, data_dir, split):
        """Test loading split interaction files."""
        df = read_interactions_split(split=split, data_dir=data_dir)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_read_interactions_split_invalid(self, data_dir):
        """Test that ValueError is raised for invalid split."""
        with pytest.raises(ValueError, match="split must be in"):
            read_interactions_split(split="invalid", data_dir=data_dir)


# ============================================================================
# Tests for high-level loading functions
# ============================================================================


class TestLoadingFunctions:
    """Test suite for high-level data loading functions."""

    def test_load_recipes(self, recipes_df):
        """Test complete recipe loading."""
        assert isinstance(recipes_df, pd.DataFrame)
        assert len(recipes_df) > 0

    def test_load_recipes_has_required_columns(self, recipes_df):
        """Test that loaded recipes have all required columns."""
        required_columns = ["id", "ingredientCount", "stepsCount", "totalTime", "calories", "isVegetarian"]
        for col in required_columns:
            assert col in recipes_df.columns, f"Missing required column: {col}"

    def test_load_recipes_data_types(self, recipes_df):
        """Test that loaded recipes have correct data types."""
        assert pd.api.types.is_integer_dtype(recipes_df["id"]) or pd.api.types.is_float_dtype(recipes_df["id"])
        assert pd.api.types.is_numeric_dtype(recipes_df["ingredientCount"])
        assert pd.api.types.is_numeric_dtype(recipes_df["totalTime"])
        assert pd.api.types.is_numeric_dtype(recipes_df["calories"])

    def test_load_recipes_has_nutrition_grade(self, recipes_df):
        """Test that recipes have nutrition grade."""
        assert "nutrition_grade" in recipes_df.columns

    def test_load_users(self, users_df):
        """Test user data loading."""
        assert isinstance(users_df, pd.DataFrame)
        assert len(users_df) > 0

    def test_load_interactions(self, interactions_df):
        """Test interactions loading."""
        assert isinstance(interactions_df, pd.DataFrame)
        assert len(interactions_df) > 0

    @pytest.mark.parametrize("split", ["train", "validation", "test"])
    def test_load_interactions_all_splits(self, data_dir, split):
        """Test loading interactions for all splits."""
        df = load_interactions(data_dir=data_dir, split=split)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


# ============================================================================
# Data consistency and validation tests
# ============================================================================


class TestDataConsistency:
    """Test suite for data consistency and validation."""

    def test_recipes_no_duplicates(self, recipes_df):
        """Test that there are no duplicate recipe IDs."""
        assert recipes_df["id"].is_unique, "Found duplicate recipe IDs"

    def test_recipes_valid_values(self, recipes_df):
        """Test that recipes have valid value ranges."""
        # Test that numeric columns don't have negative values where inappropriate
        assert (recipes_df["ingredientCount"] > 0).all(), "Found recipes with 0 or negative ingredients"
        assert (recipes_df["totalTime"] > 0).all(), "Found recipes with 0 or negative time"
        assert (recipes_df["calories"] >= 0).all(), "Found recipes with negative calories"

    def test_recipes_statistics(self, recipes_df):
        """Test recipe statistics are reasonable."""
        avg_ingredients = recipes_df["ingredientCount"].mean()
        avg_time = recipes_df["totalTime"].mean()
        avg_calories = recipes_df["calories"].mean()

        # Sanity checks
        assert 1 < avg_ingredients < 100, f"Unexpected average ingredients: {avg_ingredients}"
        assert 1 < avg_time < 500, f"Unexpected average time: {avg_time}"
        assert 10 < avg_calories < 5000, f"Unexpected average calories: {avg_calories}"

    def test_vegetarian_column_type(self, recipes_df):
        """Test that vegetarian column is boolean."""
        assert recipes_df["isVegetarian"].dtype == bool or recipes_df["isVegetarian"].dtype == "object"

    def test_nutrition_grade_values(self, recipes_df):
        """Test that nutrition grades are valid."""
        if "nutrition_grade" in recipes_df.columns:
            valid_grades = ["A", "B", "C", "D", "E"]
            unique_grades = recipes_df["nutrition_grade"].dropna().unique()
            for grade in unique_grades:
                assert grade in valid_grades, f"Invalid nutrition grade: {grade}"

    def test_average_rating_range(self, recipes_df):
        """Test that average ratings are in valid range."""
        if "average_rating" in recipes_df.columns:
            ratings = recipes_df["average_rating"].dropna()
            if len(ratings) > 0:
                assert (ratings >= 0).all() and (ratings <= 5).all(), "Ratings outside valid range [0, 5]"

    def test_interactions_valid_ratings(self, interactions_df):
        """Test that interaction ratings are valid."""
        if "rating" in interactions_df.columns:
            ratings = interactions_df["rating"].dropna()
            # Most ratings should be in the 0-5 range
            valid_ratings = (ratings >= 0) & (ratings <= 5)
            assert valid_ratings.mean() > 0.9, "More than 10% of ratings are outside [0, 5] range"


# ============================================================================
# Integration tests
# ============================================================================


class TestIntegration:
    """Integration tests to verify data relationships."""

    def test_recipes_and_interactions_consistency(self, recipes_df, interactions_df):
        """Test that interactions reference existing recipes."""
        if "recipe_id" in interactions_df.columns:
            recipe_ids = set(recipes_df["id"])
            interaction_recipe_ids = set(interactions_df["recipe_id"].unique())

            # Check if most interaction recipes exist in recipes
            existing_count = sum(1 for rid in interaction_recipe_ids if rid in recipe_ids)
            coverage = existing_count / len(interaction_recipe_ids) if len(interaction_recipe_ids) > 0 else 0

            assert coverage > 0.5, f"Only {coverage * 100:.1f}% of interaction recipes found in recipes dataset"
