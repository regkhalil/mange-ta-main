import logging
import os
import subprocess
import zipfile
from datetime import datetime

import pandas as pd

# Set up logger for this module
logger = logging.getLogger(__name__)


def load_recipe_data(file_path: str = "data/RAW_recipes.csv", local_data_dir: str = "data") -> pd.DataFrame:
    """
    Load recipe data from local file or download from Kaggle if not available.

    Args:
        file_path (str): Name of the CSV file to load
        local_data_dir (str): Local directory to store/load data

    Returns:
        pd.DataFrame: Recipe data with all original columns
    """
    logger = logging.getLogger(__name__)

    if os.path.exists(file_path):
        logger.info(f"Loading existing file from {file_path}")
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} recipes")
    else:
        logger.info("File not found locally. Downloading from Kaggle...")
        os.makedirs(local_data_dir, exist_ok=True)

        try:
            # Download using curl command
            logger.info("Downloading kaggle dataset using curl")
            zip_file_path = os.path.join(local_data_dir, "food-com-recipes-and-user-interactions.zip")

            # Use curl to download the dataset
            curl_command = [
                "curl",
                "-L",
                "-o",
                zip_file_path,
                "https://www.kaggle.com/api/v1/datasets/download/shuyangli94/food-com-recipes-and-user-interactions",
            ]

            subprocess.run(curl_command, capture_output=True, text=True, check=True)
            logger.info(f"Downloaded dataset to {zip_file_path}")

            # Extract the zip file
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(local_data_dir)
                logger.info(f"Extracted dataset to {local_data_dir}")

            # Remove the zip file after extraction
            os.remove(zip_file_path)
            logger.info("Removed zip file after extraction")

            # Load the CSV file
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} recipes from downloaded data")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download data using curl: {e}")
            logger.error(f"curl stderr: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Failed to process downloaded data: {str(e)}")
            raise

    return df


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
        force=True  # Force reconfiguration
    )
    
    # Explicitly set root logger level
    logging.getLogger().setLevel(logging.INFO)

    print(f"Logging initialized. Log file: {log_filename}")
