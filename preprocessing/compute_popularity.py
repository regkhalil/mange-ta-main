"""
Compute popularity metrics from user interactions and add them to preprocessed recipes.

This script reads the RAW_interactions.csv file, calculates popularity metrics
(average_rating, review_count, popularity_score) for each recipe, and adds
these columns to the preprocessed_recipes.csv file.

Usage:
    python compute_popularity.py
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Add parent directory to path to import from services
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_interactions(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load and clean the interactions data.

    Args:
        data_dir: Path to data directory (default: ../data)

    Returns:
        Clean interactions DataFrame
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    else:
        data_dir = Path(data_dir)

    interactions_path = data_dir / "RAW_interactions.csv"

    if not interactions_path.exists():
        raise FileNotFoundError(f"Interactions file not found: {interactions_path}")

    logger.info(f"Loading interactions from {interactions_path}")

    # Load interactions with appropriate dtypes
    interactions_df = pd.read_csv(
        interactions_path, dtype={"user_id": "int64", "recipe_id": "int64", "rating": "float32"}
    )

    logger.info(f"Loaded {len(interactions_df):,} interactions")

    # Clean the data
    initial_count = len(interactions_df)

    # Remove rows with missing recipe_id or user_id
    interactions_df = interactions_df.dropna(subset=["recipe_id", "user_id"])

    # Filter valid ratings (1-5 scale)
    interactions_df = interactions_df[(interactions_df["rating"] >= 1) & (interactions_df["rating"] <= 5)]

    # Remove duplicates (same user rating same recipe multiple times - keep first)
    interactions_df = interactions_df.drop_duplicates(subset=["user_id", "recipe_id"], keep="first")

    final_count = len(interactions_df)
    logger.info(f"After cleaning: {final_count:,} interactions ({initial_count - final_count:,} removed)")

    return interactions_df


def compute_popularity_metrics(interactions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute popularity metrics for each recipe.

    Args:
        interactions_df: Clean interactions DataFrame

    Returns:
        DataFrame with recipe_id and popularity metrics
    """
    logger.info("Computing popularity metrics...")

    # Group by recipe and compute metrics
    popularity_metrics = interactions_df.groupby("recipe_id").agg({"rating": ["mean", "count"]}).reset_index()

    # Flatten column names
    popularity_metrics.columns = ["recipe_id", "average_rating", "review_count"]

    # Handle empty DataFrame case
    if len(popularity_metrics) == 0:
        # Create empty DataFrame with correct column types
        popularity_metrics["popularity_score"] = pd.Series([], dtype="float64")
        return popularity_metrics

    # Round average rating to 2 decimal places
    popularity_metrics["average_rating"] = popularity_metrics["average_rating"].round(2)

    # Compute popularity score
    # Formula: weighted combination of average rating and review count
    # Normalize review count using log transformation to reduce skewness
    max_reviews = popularity_metrics["review_count"].max()
    normalized_review_count = np.log1p(popularity_metrics["review_count"]) / np.log1p(max_reviews)

    # Normalize average rating (already on 1-5 scale, convert to 0-1)
    normalized_rating = (popularity_metrics["average_rating"] - 1) / 4

    # Popularity score: 70% rating weight, 30% review count weight
    # This gives more importance to quality (rating) while still considering popularity (review count)
    popularity_metrics["popularity_score"] = (0.7 * normalized_rating + 0.3 * normalized_review_count).round(3)

    logger.info(f"Computed metrics for {len(popularity_metrics):,} recipes")
    logger.info(
        f"Average rating range: {popularity_metrics['average_rating'].min():.2f} - {popularity_metrics['average_rating'].max():.2f}"
    )
    logger.info(
        f"Review count range: {popularity_metrics['review_count'].min()} - {popularity_metrics['review_count'].max()}"
    )
    logger.info(
        f"Popularity score range: {popularity_metrics['popularity_score'].min():.3f} - {popularity_metrics['popularity_score'].max():.3f}"
    )

    return popularity_metrics


def load_preprocessed_recipes(data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load the preprocessed recipes DataFrame.

    Args:
        data_dir: Path to data directory (default: ../data)

    Returns:
        Preprocessed recipes DataFrame
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    else:
        data_dir = Path(data_dir)

    recipes_path = data_dir / "preprocessed_recipes.csv"

    if not recipes_path.exists():
        raise FileNotFoundError(f"Preprocessed recipes file not found: {recipes_path}")

    logger.info(f"Loading preprocessed recipes from {recipes_path}")

    # Load with basic dtypes (let pandas infer most)
    recipes_df = pd.read_csv(recipes_path, dtype={"id": "int64"}, low_memory=False)

    logger.info(f"Loaded {len(recipes_df):,} recipes")

    return recipes_df


def merge_popularity_data(recipes_df: pd.DataFrame, popularity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge popularity metrics with recipes data.

    Args:
        recipes_df: Preprocessed recipes DataFrame
        popularity_df: Popularity metrics DataFrame

    Returns:
        Enhanced recipes DataFrame with popularity metrics
    """
    logger.info("Merging popularity data with recipes...")

    # Rename recipe_id to id for merging
    popularity_df = popularity_df.rename(columns={"recipe_id": "id"})

    # Merge on recipe id (left join to keep all recipes)
    enhanced_df = recipes_df.merge(popularity_df, on="id", how="left")

    # Fill missing values for recipes without interactions
    # Use the same defaults as in data_loader.py
    enhanced_df["review_count"] = enhanced_df["review_count"].fillna(0).astype("int32")
    enhanced_df["average_rating"] = enhanced_df["average_rating"].fillna(3.0).astype("float32")
    enhanced_df["popularity_score"] = enhanced_df["popularity_score"].fillna(0.0).astype("float32")

    recipes_with_ratings = enhanced_df[enhanced_df["review_count"] > 0]

    logger.info(f"Enhanced {len(enhanced_df):,} recipes with popularity data")
    logger.info(
        f"Recipes with reviews: {len(recipes_with_ratings):,} ({len(recipes_with_ratings) / len(enhanced_df) * 100:.1f}%)"
    )
    logger.info(f"Recipes without reviews (using defaults): {len(enhanced_df) - len(recipes_with_ratings):,}")

    return enhanced_df


def save_enhanced_recipes(enhanced_df: pd.DataFrame, data_dir: Optional[str] = None) -> None:
    """
    Save the enhanced recipes DataFrame back to CSV.

    Args:
        enhanced_df: Enhanced recipes DataFrame
        data_dir: Path to data directory (default: ../data)
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    else:
        data_dir = Path(data_dir)

    output_path = data_dir / "preprocessed_recipes.csv"

    logger.info(f"Saving enhanced recipes to {output_path}")

    # Save with same format as original
    enhanced_df.to_csv(output_path, index=False)

    logger.info(f"Successfully saved {len(enhanced_df):,} recipes with popularity metrics")


def log_popularity_summary(enhanced_df: pd.DataFrame) -> None:
    """
    Log summary statistics of the popularity metrics.

    Args:
        enhanced_df: Enhanced recipes DataFrame
    """
    logger.info("=" * 60)
    logger.info("POPULARITY METRICS SUMMARY")
    logger.info("=" * 60)

    # Basic stats
    recipes_with_reviews = enhanced_df[enhanced_df["review_count"] > 0]

    logger.info(f"Total recipes: {len(enhanced_df):,}")
    logger.info(
        f"Recipes with reviews: {len(recipes_with_reviews):,} ({len(recipes_with_reviews) / len(enhanced_df) * 100:.1f}%)"
    )
    logger.info(f"Recipes without reviews: {len(enhanced_df) - len(recipes_with_reviews):,}")

    if len(recipes_with_reviews) > 0:
        logger.info("For recipes with reviews:")
        logger.info(
            f"  Average rating: {recipes_with_reviews['average_rating'].mean():.2f} (std: {recipes_with_reviews['average_rating'].std():.2f})"
        )
        logger.info(
            f"  Average review count: {recipes_with_reviews['review_count'].mean():.1f} (std: {recipes_with_reviews['review_count'].std():.1f})"
        )
        logger.info(
            f"  Average popularity score: {recipes_with_reviews['popularity_score'].mean():.3f} (std: {recipes_with_reviews['popularity_score'].std():.3f})"
        )

        # Top recipes by popularity score
        logger.info("Top 10 recipes by popularity score:")
        top_recipes = recipes_with_reviews.nlargest(10, "popularity_score")
        for i, (_, recipe) in enumerate(top_recipes.iterrows(), 1):
            logger.info(
                f"  {i:2d}. Recipe {recipe['id']:>6d}: rating={recipe['average_rating']:.2f}, reviews={recipe['review_count']:>4d}, score={recipe['popularity_score']:.3f}"
            )

    logger.info("=" * 60)


def main(data_dir: Optional[str] = None):
    """
    Main function to compute and add popularity metrics.

    Args:
        data_dir: Path to data directory (default: ../data)
    """
    try:
        logger.info("Starting popularity computation...")

        # Step 1: Load and clean interactions
        interactions_df = load_interactions(data_dir)

        # Step 2: Compute popularity metrics
        popularity_df = compute_popularity_metrics(interactions_df)

        # Step 3: Load preprocessed recipes
        recipes_df = load_preprocessed_recipes(data_dir)

        # Step 4: Merge popularity data
        enhanced_df = merge_popularity_data(recipes_df, popularity_df)

        # Step 5: Save enhanced recipes
        save_enhanced_recipes(enhanced_df, data_dir)

        # Step 6: Log summary
        log_popularity_summary(enhanced_df)

        logger.info("Popularity computation completed successfully!")

    except Exception as e:
        logger.error(f"Error during popularity computation: {e}")
        raise


if __name__ == "__main__":
    # Allow running this script standalone for testing
    import argparse

    parser = argparse.ArgumentParser(description="Compute popularity metrics for recipes")
    parser.add_argument("--data-dir", type=str, help="Path to data directory (default: ../data)")

    args = parser.parse_args()

    # Run the complete pipeline when called directly
    main(args.data_dir)
