"""
Main preprocessing script for recipe similarity analysis.

This script orchestrates the preprocessing pipeline by calling functions
from prepare_similarity_matrix module to load, process, and save recipe data.
"""

import logging
import os

import nutrition_scoring
import prepare_similarity_matrix
import prepare_vege_recipes
import preprocess_utils

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main preprocessing pipeline that loads, processes, and saves recipe data.
    """
    # Configuration
    dataset_filename = "RAW_recipes.csv"
    local_data_dir = "data"
    logs_dir = "logs"

    # Setup logging
    preprocess_utils.setup_logging(logs_dir)

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

    # Remove unneeded columns and store the final dataframe in a csv
    logger.info("Selecting relevant columns for the final preprocessed DataFrame.")
    df_preprocessed = df_with_nutriscore[
        [
            "name",
            "id",
            "minutes",
            "n_steps",
            "steps",
            "description",
            "ingredients",
            "n_ingredients",
            "nutrition_score",
            "nutrition_grade",
            "is_vegetarian",
        ]
    ]
    output_csv_path = os.path.join(local_data_dir, "preprocessed_recipes.csv")
    logger.info(f"Saving preprocessed DataFrame to {output_csv_path}.")
    df_preprocessed.to_csv(output_csv_path, index=False)
    logger.info("Preprocessing complete. Data saved successfully.")


if __name__ == "__main__":
    main()
