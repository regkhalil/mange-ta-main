"""
Main preprocessing script for recipe similarity analysis.

This script orchestrates the preprocessing pipeline by calling functions
from prepare_similarity_matrix module to load, process, and save recipe data.

Usage:
    python preprocess.py              # Normal preprocessing (local only)
    python preprocess.py --deploy     # Preprocessing + upload to Google Drive
"""

import argparse
import logging
import os

import gdrive_uploader
import nutrition_scoring
import prepare_similarity_matrix
import prepare_vege_recipes
import preprocess_utils
from compute_popularity import compute_popularity_metrics, load_interactions
from recipe_descriptions_hybrid import enhance_recipe_descriptions
from text_cleaner import clean_recipe_data

logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Preprocess recipe data for the Mangetamain application.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python preprocess.py              # Run preprocessing locally
  python preprocess.py --deploy     # Run preprocessing and upload to Google Drive
        """,
    )

    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Upload preprocessed files to Google Drive (appDataFolder) after processing",
    )

    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory for data files (default: data)",
    )

    parser.add_argument(
        "--logs-dir",
        default="logs",
        help="Directory for log files (default: logs)",
    )

    return parser.parse_args()


def main() -> None:
    """
    Main preprocessing pipeline that loads, processes, and saves recipe data.
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Configuration
    dataset_filename = "RAW_recipes.csv"
    local_data_dir = args.data_dir
    logs_dir = args.logs_dir

    # Setup logging
    preprocess_utils.setup_logging(logs_dir)

    logger.info("=" * 70)
    logger.info("Starting preprocessing pipeline")
    logger.info("=" * 70)
    logger.info(f"Data directory: {local_data_dir}")
    logger.info(f"Logs directory: {logs_dir}")
    logger.info(f"Deploy mode: {'ENABLED' if args.deploy else 'DISABLED'}")
    logger.info("=" * 70)

    # Load data
    df = preprocess_utils.load_recipe_data(os.path.join(local_data_dir, dataset_filename), local_data_dir)

    # Add vegetarian classification
    df = prepare_vege_recipes.prepare_vegetarian_classification(df)

    # Run similarity matrix preparation
    prepare_similarity_matrix.run_similarity_matrix_prep(
        df, local_data_dir, os.path.join(local_data_dir, "similarity_matrix.pkl")
    )

    # Prepare nutrition score (Weighted Balance Score - improved algorithm)
    logger.info("Computing nutrition scores and grades...")
    df_with_nutriscore = nutrition_scoring.score_nutrition(df)

    # Text Enhancement: Enhance descriptions and clean all text
    logger.info("Enhancing recipe descriptions with metadata and ingredients...")
    df_enhanced = enhance_recipe_descriptions(
        df_with_nutriscore,
        original_desc_col="description",
        time_col="minutes",
        tags_col="tags",
        ingredients_col="ingredients",
        output_col="description_enhanced",
    )

    # Replace original description with enhanced version and drop the temp column
    df_enhanced["description"] = df_enhanced["description_enhanced"]
    df_enhanced = df_enhanced.drop(columns=["description_enhanced"])

    logger.info("Cleaning all text columns with proper capitalization...")
    df_cleaned = clean_recipe_data(
        df_enhanced, clean_name=True, clean_description=True, clean_steps=True, clean_tags=True, clean_ingredients=True
    )

    # Compute popularity metrics from interactions
    logger.info("Computing popularity metrics from user interactions...")
    try:
        interactions_df = load_interactions(local_data_dir)
        popularity_df = compute_popularity_metrics(interactions_df)

        # Merge popularity data with recipes (left join to keep all recipes)
        logger.info("Merging popularity data with recipes...")
        df_with_popularity = df_cleaned.merge(popularity_df.rename(columns={"recipe_id": "id"}), on="id", how="left")

        # Fill missing values for recipes without interactions
        df_with_popularity["review_count"] = df_with_popularity["review_count"].fillna(0).astype("int32")
        df_with_popularity["average_rating"] = df_with_popularity["average_rating"].fillna(3.0).astype("float32")
        df_with_popularity["popularity_score"] = df_with_popularity["popularity_score"].fillna(0.0).astype("float32")

        recipes_with_reviews = df_with_popularity[df_with_popularity["review_count"] > 0]
        logger.info(f"Enhanced {len(df_with_popularity):,} recipes with popularity data")
        logger.info(
            f"Recipes with reviews: {len(recipes_with_reviews):,} ({len(recipes_with_reviews) / len(df_with_popularity) * 100:.1f}%)"
        )
        logger.info(
            f"Recipes without reviews (using defaults): {len(df_with_popularity) - len(recipes_with_reviews):,}"
        )

        df_final = df_with_popularity

    except Exception as e:
        logger.warning(f"Failed to compute popularity metrics: {e}")
        logger.warning("Continuing without popularity data - columns will be added with default values")

        # Add default popularity columns if computation fails
        df_cleaned["review_count"] = 0
        df_cleaned["average_rating"] = 3.0
        df_cleaned["popularity_score"] = 0.0
        df_final = df_cleaned

    # Remove unneeded columns and store the final dataframe in a csv
    logger.info("Selecting relevant columns for the final preprocessed DataFrame.")

    # Only select the cleaned columns and other needed columns including popularity metrics
    # Drop original unmodified columns (name, description, steps, tags, ingredients)
    # Note: We keep both 'nutrition' (full array) and 'calories' (extracted) because:
    #   - 'nutrition': Complete nutritional data [calories, fat, sugar, sodium, protein, sat_fat, carbs]
    #                  Kept for future use and detailed nutrition displays
    #   - 'calories': Extracted first value from nutrition array for direct access
    #                 Avoids parsing the array on every recipe card display (~12 per page)
    #                 Trade-off: ~100KB extra disk space for significantly faster runtime performance
    #
    # Individual nutrient columns (total_fat_pdv, sugar_pdv, etc.) are extracted for analytics performance
    # Complexity and time category columns are precomputed for Streamlit dashboard speed
    df_preprocessed = df_final[
        [
            "name_cleaned",
            "id",
            "minutes",
            "tags_cleaned",
            "n_steps",
            "steps_cleaned",
            "description_cleaned",
            "ingredients_cleaned",
            "n_ingredients",
            "nutrition",
            "nutrition_score",
            "nutrition_grade",
            "is_vegetarian",
            "calories",
            "total_fat_pdv",
            "sugar_pdv",
            "sodium_pdv",
            "protein_pdv",
            "saturated_fat_pdv",
            "carbs_pdv",
            "complexity_index",
            "complexity_category",
            "time_category",
            "review_count",
            "average_rating",
            "popularity_score",
        ]
    ].copy()

    # Rename cleaned columns back to standard names for the app
    df_preprocessed.columns = [
        "name",
        "id",
        "minutes",
        "tags",
        "n_steps",
        "steps",
        "description",
        "ingredients",
        "n_ingredients",
        "nutrition",
        "nutrition_score",
        "nutrition_grade",
        "is_vegetarian",
        "calories",
        "total_fat_pdv",
        "sugar_pdv",
        "sodium_pdv",
        "protein_pdv",
        "saturated_fat_pdv",
        "carbs_pdv",
        "complexity_index",
        "complexity_category",
        "time_category",
        "review_count",
        "average_rating",
        "popularity_score",
    ]

    logger.info(f"Final DataFrame shape: {df_preprocessed.shape}")
    logger.info(f"Final columns: {df_preprocessed.columns.tolist()}")
    output_csv_path = os.path.join(local_data_dir, "preprocessed_recipes.csv")
    logger.info(f"Saving preprocessed DataFrame to {output_csv_path}.")
    df_preprocessed.to_csv(output_csv_path, index=False)
    logger.info("Preprocessing complete. Data saved successfully.")

    # Upload to Google Drive if --deploy flag is set
    if args.deploy:
        logger.info("\n" + "=" * 70)
        logger.info("Deploy mode enabled - uploading to Google Drive")
        logger.info("=" * 70)

        # Step 1: Delete all existing files from Google Drive
        logger.info("Step 1: Cleaning up previous deployment files...")
        delete_success = gdrive_uploader.delete_all_files_in_folder()

        if not delete_success:
            logger.warning("Warning: Some files could not be deleted from Google Drive")
            logger.info("Continuing with upload...")

        # Step 2: Upload only the essential files (preprocessed_recipes.csv and similarity_matrix.pkl)
        logger.info("\nStep 2: Uploading essential preprocessing files...")
        upload_success = gdrive_uploader.upload_preprocessed_recipes_only(local_data_dir)

        if upload_success:
            logger.info("\n✓ Deployment successful - essential files uploaded to Google Drive")
        else:
            logger.error("\n✗ Deployment failed - could not upload essential files")
            exit(1)
    else:
        logger.info("\nDeploy mode disabled - files saved locally only")
        logger.info("To upload to Google Drive, run with --deploy flag")


if __name__ == "__main__":
    main()
