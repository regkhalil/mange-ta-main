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
from text_cleaner import clean_recipe_data
from recipe_descriptions_hybrid import enhance_recipe_descriptions

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


if __name__ == "__main__":
    main()
