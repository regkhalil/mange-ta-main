"""
Main preprocessing script for recipe similarity analysis.

This script orchestrates the preprocessing pipeline by calling functions
from prepare_similarity_matrix module to load, process, and save recipe data.
"""

import os

import prepare_similarity_matrix
import prepare_vege_recipes
import preprocess_utils


def main() -> None:
    """
    Main preprocessing pipeline that loads, processes, and saves recipe data.
    """
    # Configuration
    dataset_filename = "RAW_recipes.csv"
    local_data_dir = "data"
    logs_dir = "logs"
    similarity_matrix_path = os.path.join(local_data_dir, "similarity_matrix.pkl")

    # Setup logging
    preprocess_utils.setup_logging(logs_dir)

    # Load data
    df = preprocess_utils.load_recipe_data(os.path.join(local_data_dir, dataset_filename), local_data_dir)

    # Add vegetarian classification
    df = prepare_vege_recipes.prepare_vegetarian_classification(df)

    # Run similarity matrix preparation
    prepare_similarity_matrix.run_similarity_matrix_prep(df, local_data_dir, similarity_matrix_path)

    # Prepare nutrition score
    # df_with_nutriscore = nutrition_scoring.score_nutrition(df)

    # TODO: rmeove unneened columns and store the final dataframe in a csv


if __name__ == "__main__":
    main()
