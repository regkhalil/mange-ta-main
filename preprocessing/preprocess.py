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
from text_cleaner import clean_recipe_data
from recipe_descriptions_hybrid import enhance_recipe_descriptions

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

    # Prepare nutrition score
    df_with_nutriscore = nutrition_scoring.score_nutrition(df)

    # Text Enhancement: Enhance descriptions and clean all text
    logger.info("Enhancing recipe descriptions with metadata and ingredients...")
    df_enhanced = enhance_recipe_descriptions(
        df_with_nutriscore,
        original_desc_col='description',
        time_col='minutes',
        tags_col='tags',
        ingredients_col='ingredients',
        output_col='description_enhanced'
    )
    
    # Replace original description with enhanced version and drop the temp column
    df_enhanced['description'] = df_enhanced['description_enhanced']
    df_enhanced = df_enhanced.drop(columns=['description_enhanced'])
    
    logger.info("Cleaning all text columns with proper capitalization...")
    df_cleaned = clean_recipe_data(
        df_enhanced,
        clean_name=True,
        clean_description=True,
        clean_steps=True,
        clean_tags=True,
        clean_ingredients=True
    )

    # Remove unneeded columns and store the final dataframe in a csv
    logger.info("Selecting relevant columns for the final preprocessed DataFrame.")
    # Only select the cleaned columns and other needed columns
    # Drop original unmodified columns (name, description, steps, tags, ingredients)
    df_preprocessed = df_cleaned[
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

        success = gdrive_uploader.upload_preprocessing_outputs(local_data_dir)

        if success:
            logger.info("\n✓ Deployment successful - all files uploaded to Google Drive")
        else:
            logger.error("\n✗ Deployment failed - some files could not be uploaded")
            exit(1)
    else:
        logger.info("\nDeploy mode disabled - files saved locally only")
        logger.info("To upload to Google Drive, run with --deploy flag")


if __name__ == "__main__":
    main()
