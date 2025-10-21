"""
Recipe preprocessing module for feature extraction and similarity computation.

This module handles loading recipe data from local files or Kaggle, preprocessing
the data for machine learning, and creating feature vectors for recipe similarity analysis.
"""

import logging
import os
import pickle
from typing import Any, Dict, List, Tuple

import kagglehub
import pandas as pd
import scipy.sparse
from kagglehub import KaggleDatasetAdapter
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

# Set up logger for this module
logger = logging.getLogger(__name__)


def load_recipe_data(file_path: str = "RAW_recipes.csv", local_data_dir: str = "data") -> pd.DataFrame:
    """
    Load recipe data from local file or download from Kaggle if not available.

    Args:
        file_path (str): Name of the CSV file to load
        local_data_dir (str): Local directory to store/load data

    Returns:
        pd.DataFrame: Recipe data with all original columns
    """
    local_file_path = os.path.join(local_data_dir, file_path)

    if os.path.exists(local_file_path):
        logger.info(f"Loading existing file from {local_file_path}")
        df = pd.read_csv(local_file_path)
        logger.info(f"Loaded {len(df)} recipes")
    else:
        logger.info("File not found locally. Downloading from Kaggle...")
        os.makedirs(local_data_dir, exist_ok=True)

        try:
            df = kagglehub.dataset_load(
                KaggleDatasetAdapter.PANDAS,
                "shuyangli94/food-com-recipes-and-user-interactions",
                file_path,
            )
            df.to_csv(local_file_path, index=False)
            logger.info(f"Downloaded and saved {len(df)} recipes")
        except Exception as e:
            logger.error(f"Failed to download data from Kaggle: {str(e)}")
            raise

    return df


def preprocess_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert list-formatted strings to space-separated strings for vectorization.

    Args:
        df (pd.DataFrame): Raw recipe dataframe

    Returns:
        pd.DataFrame: Dataframe with additional string columns for ingredients, tags, and name
    """
    logger.info("Processing text features")
    df_processed = df.copy()

    # Convert list of ingredients to a string for each recipe
    df_processed["ingredients_str"] = df_processed["ingredients"].apply(
        lambda x: " ".join(eval(x)) if isinstance(x, str) else ""
    )

    # Convert list of tags to a string for each recipe
    df_processed["tags_str"] = df_processed["tags"].apply(lambda x: " ".join(eval(x)) if isinstance(x, str) else "")

    # Convert name to string (already is, but for consistency)
    df_processed["name_str"] = df_processed["name"].astype(str)

    logger.info("Text features processed")
    return df_processed


def create_feature_vectors(
    df: pd.DataFrame, name_weight: float = 5.0, ease_weight: float = 5.0
) -> Tuple[csr_matrix, Dict[str, Any]]:
    """
    Create combined feature vectors from recipe text and numerical features.

    Args:
        df (pd.DataFrame): Preprocessed recipe dataframe
        name_weight (float): Weight multiplier for recipe name features
        ease_weight (float): Weight multiplier for ease features (steps, time)

    Returns:
        Tuple[csr_matrix, Dict]: Combined feature matrix and vectorizer objects
    """
    logger.info("Creating feature vectors")

    # Vectorize ingredients
    ingredient_vectorizer = CountVectorizer()
    ingredient_matrix = ingredient_vectorizer.fit_transform(df["ingredients_str"])

    # Vectorize tags
    tag_vectorizer = CountVectorizer()
    tag_matrix = tag_vectorizer.fit_transform(df["tags_str"])

    # Vectorize name with weight
    name_vectorizer = CountVectorizer()
    name_matrix = name_vectorizer.fit_transform(df["name_str"])
    name_matrix_weighted = name_matrix.multiply(name_weight)

    # Process ease features (steps and time)
    ease_features = df[["n_steps", "minutes"]].fillna(0)
    scaler = MinMaxScaler()
    ease_matrix = scaler.fit_transform(ease_features)
    ease_sparse = csr_matrix(ease_matrix * ease_weight)

    # Combine all features
    combined_features = scipy.sparse.hstack([name_matrix_weighted, ingredient_matrix, tag_matrix, ease_sparse])

    logger.info(f"Feature vectors created with shape: {combined_features.shape}")

    # Store vectorizers for potential future use
    vectorizers = {
        "ingredient_vectorizer": ingredient_vectorizer,
        "tag_vectorizer": tag_vectorizer,
        "name_vectorizer": name_vectorizer,
        "scaler": scaler,
    }

    return combined_features, vectorizers


def create_id_mappings(df: pd.DataFrame) -> Tuple[Dict[Any, int], Dict[int, Any]]:
    """
    Create bidirectional mappings between recipe IDs and DataFrame indices.

    Args:
        df (pd.DataFrame): Recipe dataframe with 'id' column

    Returns:
        Tuple[Dict, Dict]: (id_to_index, index_to_id) mapping dictionaries
    """
    id_to_index = {rid: idx for idx, rid in enumerate(df["id"])}
    index_to_id = {idx: rid for idx, rid in enumerate(df["id"])}
    logger.info(f"Created ID mappings for {len(id_to_index)} recipes")

    return id_to_index, index_to_id


def get_top_similar(
    recipe_id: Any,
    combined_features: csr_matrix,
    id_to_index: Dict[Any, int],
    index_to_id: Dict[int, Any],
    top_n: int = 5,
) -> List[Any]:
    """
    Find the most similar recipes to a given recipe using cosine similarity.

    Args:
        recipe_id: ID of the query recipe
        combined_features (csr_matrix): Combined feature matrix for all recipes
        id_to_index (Dict): Mapping from recipe ID to matrix index
        index_to_id (Dict): Mapping from matrix index to recipe ID
        top_n (int): Number of similar recipes to return

    Returns:
        List: Recipe IDs of the most similar recipes
    """
    try:
        recipe_idx = id_to_index[recipe_id]
        query_vec = combined_features[recipe_idx].reshape(1, -1)
        sim_scores = cosine_similarity(query_vec, combined_features)[0]
        top_indices = sim_scores.argsort()[::-1][1 : top_n + 1]  # Exclude self (index 0)

        similar_recipe_ids = [index_to_id[idx] for idx in top_indices]
        logger.info(f"Found {len(similar_recipe_ids)} similar recipes for recipe {recipe_id}")

        return similar_recipe_ids
    except KeyError as e:
        logger.error(f"Recipe ID {recipe_id} not found: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error finding similar recipes: {str(e)}")
        raise


def save_preprocessed_data(
    combined_features: csr_matrix,
    id_to_index: Dict[Any, int],
    index_to_id: Dict[int, Any],
    vectorizers: Dict[str, Any],
    output_path: str,
) -> None:
    """
    Save preprocessed features and mappings to disk for fast reuse.

    Args:
        combined_features (csr_matrix): Combined feature matrix
        id_to_index (Dict): Recipe ID to index mapping
        index_to_id (Dict): Index to recipe ID mapping
        vectorizers (Dict): Fitted vectorizer objects
        output_path (str): Path to save the preprocessed data
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            pickle.dump(
                {
                    "combined_features": combined_features,
                    "id_to_index": id_to_index,
                    "index_to_id": index_to_id,
                    "vectorizers": vectorizers,
                },
                f,
            )

        file_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
        logger.info(f"Saved preprocessed data ({file_size:.1f} MB) to {output_path}")

    except Exception as e:
        logger.error(f"Failed to save preprocessed data: {str(e)}")
        raise
