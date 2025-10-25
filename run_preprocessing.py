"""
Script pour exécuter le preprocessing sur nos données existantes.
"""

import logging
from pathlib import Path

import pandas as pd

from preprocessing import nutrition_scoring, prepare_vege_recipes

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Pipeline de preprocessing adapté à notre structure de données."""

    # Chemins
    data_dir = Path(__file__).parent.parent / "Donnees"
    raw_recipes_path = data_dir / "RAW_recipes.csv"
    output_path = data_dir / "preprocessed_recipes.csv"

    logger.info(f"Chargement des données depuis {raw_recipes_path}")

    # Charger TOUTES les données
    df = pd.read_csv(raw_recipes_path)
    logger.info(f"Chargé {len(df)} recettes")
    logger.info(f"Colonnes: {df.columns.tolist()}")

    # 1. Classification végétarienne
    logger.info("Classification végétarienne...")
    df = prepare_vege_recipes.prepare_vegetarian_classification(df)
    logger.info(f"Végétarien: {df['is_vegetarian'].sum()} / {len(df)}")

    # 2. Scores nutritionnels
    logger.info("Calcul des scores nutritionnels...")
    df = nutrition_scoring.score_nutrition(df)
    logger.info(f"Scores nutritionnels calculés pour {df['nutrition_score'].notna().sum()} recettes")

    # 2.5 Matrice de similarité pour recommandations
    logger.info("Création de la matrice de similarité...")
    try:
        from preprocessing import prepare_similarity_matrix

        similarity_matrix_path = data_dir / "similarity_matrix.pkl"
        prepare_similarity_matrix.run_similarity_matrix_prep(df, str(data_dir), str(similarity_matrix_path))
        logger.info(f"Matrice de similarité sauvegardée dans {similarity_matrix_path}")
    except Exception as e:
        logger.warning(f"Impossible de créer la matrice de similarité: {e}")

    # 3. Sélectionner les colonnes pertinentes
    logger.info("Sélection des colonnes finales...")
    columns_to_keep = [
        "name",
        "id",
        "minutes",
        "n_steps",
        "steps",
        "ingredients",
        "n_ingredients",
        "nutrition_score",
        "nutrition_grade",
        "is_vegetarian",
    ]

    # Vérifier quelles colonnes existent
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    df_preprocessed = df[existing_columns]

    # 4. Sauvegarder
    logger.info(f"Sauvegarde des données preprocessées dans {output_path}")
    df_preprocessed.to_csv(output_path, index=False)

    logger.info("✅ Preprocessing terminé avec succès!")
    logger.info(f"Fichier créé: {output_path}")
    logger.info(f"Nombre de recettes: {len(df_preprocessed)}")
    logger.info(f"Colonnes: {df_preprocessed.columns.tolist()}")

    # Statistiques
    print("\n" + "=" * 60)
    print("STATISTIQUES:")
    print("=" * 60)
    print(f"Total recettes: {len(df_preprocessed)}")
    veg_count = df_preprocessed["is_vegetarian"].sum()
    veg_pct = df_preprocessed["is_vegetarian"].mean() * 100
    print(f"Végétariennes: {veg_count} ({veg_pct:.1f}%)")
    if "nutrition_grade" in df_preprocessed.columns:
        print("\nDistribution des grades nutritionnels:")
        print(df_preprocessed["nutrition_grade"].value_counts().sort_index())
    print("=" * 60)


if __name__ == "__main__":
    main()
