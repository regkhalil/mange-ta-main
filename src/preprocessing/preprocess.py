"""
Main preprocessing script for recipe similarity analysis.

This script orchestrates the preprocessing pipeline by calling functions
from prepare_similarity_matrix module to load, process, and save recipe data.
"""

import logging
import os
from datetime import datetime

import prepare_similarity_matrix


def setup_logging(logs_dir: str = "logs") -> None:
    """
    Set up logging configuration with both file and console handlers.

    Args:
        logs_dir (str): Directory to store log files
    """
    # Create logs directory if it doesn't exist
    os.makedirs(logs_dir, exist_ok=True)

    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"preprocessing_{timestamp}.log")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(),  # Also log to console
        ],
    )

    print(f"Logging initialized. Log file: {log_filename}")


def run_similarity_matrix_prep(file_path: str, local_data_dir: str, similarity_matrix_path: str) -> None:
    """
    Run the complete similarity matrix preparation pipeline.

    Args:
        file_path (str): Name of the CSV file to load
        local_data_dir (str): Local directory to store/load data
        similarity_matrix_path (str): Path to save the similarity matrix
    """
    # Load data
    df = prepare_similarity_matrix.load_recipe_data(file_path, local_data_dir)

    # Preprocess text features
    df_processed = prepare_similarity_matrix.preprocess_text_features(df)

    # Create feature vectors
    combined_features, vectorizers = prepare_similarity_matrix.create_feature_vectors(df_processed)

    # Create ID mappings
    id_to_index, index_to_id = prepare_similarity_matrix.create_id_mappings(df_processed)

    # Save preprocessed data
    prepare_similarity_matrix.save_preprocessed_data(
        combined_features, id_to_index, index_to_id, vectorizers, similarity_matrix_path
    )


def main() -> None:
    """
    Main preprocessing pipeline that loads, processes, and saves recipe data.
    """
    # Configuration
    file_path = "RAW_recipes.csv"
    local_data_dir = "data"
    logs_dir = "logs"
    similarity_matrix_path = os.path.join(local_data_dir, "similarity_matrix.pkl")

    # Setup logging
    setup_logging(logs_dir)

    # Run similarity matrix preparation
    run_similarity_matrix_prep(file_path, local_data_dir, similarity_matrix_path)


if __name__ == "__main__":
    main()
