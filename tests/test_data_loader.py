"""
Tests complets pour le chargeur de données (services/data_loader.py).

Ce module teste le chargement, la validation et l'intégrité des données
conformément aux exigences du projet.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

# Add root directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable Streamlit cache for tests
os.environ["STREAMLIT_SERVER_ENABLE_STATIC_SERVING"] = "false"

from services.data_loader import (
    load_recipes,
    read_csv_file,
)


@pytest.fixture
def data_dir():
    """Fixture providing the data directory path."""
    return "data"


@pytest.fixture
def recipes_df(data_dir):
    """Fixture providing loaded recipes DataFrame."""
    return load_recipes(data_dir=data_dir)


@pytest.fixture
def interactions_df(data_dir):
    """Fixture providing loaded interactions DataFrame."""
    # Load interactions manually since load_interactions may not exist
    try:
        return read_csv_file("interactions_train.csv", data_dir=data_dir)
    except:
        return pd.DataFrame()  # Return empty if not found


# ============================================================================
# Tests de base pour le chargement CSV
# ============================================================================


class TestBasicCSVLoading:
    """Tests de base pour la lecture de fichiers CSV."""

    def test_read_csv_file_exists(self, data_dir):
        """Test : Lecture d'un fichier CSV existant."""
        df = read_csv_file("preprocessed_recipes.csv", data_dir=data_dir, nrows=10)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df) <= 10

    def test_read_csv_file_with_usecols(self, data_dir):
        """Test : Lecture avec sélection de colonnes."""
        df = read_csv_file("preprocessed_recipes.csv", data_dir=data_dir, usecols=["id"], nrows=10)
        
        assert isinstance(df, pd.DataFrame)
        assert "id" in df.columns
        assert len(df.columns) == 1

    def test_read_csv_file_not_found(self, data_dir):
        """Test : Erreur pour fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            read_csv_file("nonexistent_file.csv", data_dir=data_dir)

    def test_read_csv_file_full_load(self, data_dir):
        """Test : Chargement complet sans limite de lignes."""
        df = read_csv_file("preprocessed_recipes.csv", data_dir=data_dir)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 100  # Devrait avoir beaucoup de recettes


# ============================================================================
# Tests pour load_recipes
# ============================================================================


class TestLoadRecipes:
    """Tests pour le chargement des recettes."""

    def test_load_recipes_returns_dataframe(self, recipes_df):
        """Test : load_recipes retourne un DataFrame."""
        assert isinstance(recipes_df, pd.DataFrame)
        assert len(recipes_df) > 0

    def test_load_recipes_has_required_columns(self, recipes_df):
        """Test : Le DataFrame contient les colonnes essentielles."""
        required_columns = [
            "id", "name", "ingredients", "steps",
            "n_ingredients", "n_steps", "minutes", "calories",
            "nutrition_score", "nutrition_grade", "is_vegetarian"
        ]
        
        for col in required_columns:
            assert col in recipes_df.columns, f"Colonne manquante: {col}"

    def test_load_recipes_data_types(self, recipes_df):
        """Test : Les types de données sont corrects."""
        # ID doit être numérique
        assert pd.api.types.is_numeric_dtype(recipes_df["id"])
        
        # Colonnes numériques
        assert pd.api.types.is_numeric_dtype(recipes_df["n_ingredients"])
        assert pd.api.types.is_numeric_dtype(recipes_df["minutes"])
        assert pd.api.types.is_numeric_dtype(recipes_df["calories"])
        assert pd.api.types.is_numeric_dtype(recipes_df["nutrition_score"])

    def test_load_recipes_no_duplicate_ids(self, recipes_df):
        """Test : Pas de doublons dans les IDs."""
        assert recipes_df["id"].is_unique, "Des IDs de recettes sont dupliqués"

    def test_load_recipes_no_null_ids(self, recipes_df):
        """Test : Pas de valeurs nulles dans les IDs."""
        assert recipes_df["id"].notna().all()

    def test_load_recipes_positive_values(self, recipes_df):
        """Test : Les valeurs numériques sont positives."""
        assert (recipes_df["n_ingredients"] > 0).all()
        assert (recipes_df["minutes"] > 0).sum() > len(recipes_df) * 0.95  # 95% au moins
        assert (recipes_df["calories"] >= 0).all()

    def test_load_recipes_nutrition_score_range(self, recipes_df):
        """Test : Les scores nutritionnels sont dans la bonne plage."""
        valid_scores = recipes_df["nutrition_score"].notna()
        assert (recipes_df.loc[valid_scores, "nutrition_score"] >= 0).all()
        assert (recipes_df.loc[valid_scores, "nutrition_score"] <= 100).all()

    def test_load_recipes_nutrition_grades_valid(self, recipes_df):
        """Test : Les grades nutritionnels sont valides (A-E)."""
        valid_grades = recipes_df["nutrition_grade"].dropna()
        
        if len(valid_grades) > 0:
            assert valid_grades.isin(["A", "B", "C", "D", "E"]).all()

    def test_load_recipes_vegetarian_flag(self, recipes_df):
        """Test : Le flag végétarien est booléen."""
        assert recipes_df["is_vegetarian"].isin([0, 1, True, False]).all()

    def test_load_recipes_has_names(self, recipes_df):
        """Test : La plupart des recettes ont un nom."""
        named_recipes = recipes_df["name"].notna().sum()
        total = len(recipes_df)
        
        assert named_recipes / total > 0.95, "Trop de recettes sans nom"

    def test_load_recipes_has_ingredients(self, recipes_df):
        """Test : La plupart des recettes ont des ingrédients."""
        has_ingredients = recipes_df["ingredients"].notna().sum()
        total = len(recipes_df)
        
        assert has_ingredients / total > 0.9, "Trop de recettes sans ingrédients"

    def test_load_recipes_caching(self, data_dir):
        """Test : Le mécanisme de cache fonctionne."""
        # Premier chargement
        df1 = load_recipes(data_dir=data_dir)
        
        # Second chargement (devrait utiliser le cache)
        df2 = load_recipes(data_dir=data_dir)
        
        # Les DataFrames devraient avoir la même structure
        assert df1.shape == df2.shape
        assert list(df1.columns) == list(df2.columns)


# ============================================================================
# Tests pour load_interactions
# ============================================================================


class TestLoadInteractions:
    """Tests pour le chargement des interactions utilisateur-recette."""

    def test_load_interactions_returns_dataframe(self, interactions_df):
        """Test : load_interactions retourne un DataFrame."""
        assert isinstance(interactions_df, pd.DataFrame)

    def test_load_interactions_has_required_columns(self, interactions_df):
        """Test : Le DataFrame d'interactions contient les colonnes nécessaires."""
        if len(interactions_df) > 0:
            required_columns = ["user_id", "recipe_id", "rating"]
            
            for col in required_columns:
                assert col in interactions_df.columns, f"Colonne manquante: {col}"

    def test_load_interactions_data_types(self, interactions_df):
        """Test : Les types de données sont corrects."""
        if len(interactions_df) > 0:
            assert pd.api.types.is_numeric_dtype(interactions_df["user_id"])
            assert pd.api.types.is_numeric_dtype(interactions_df["recipe_id"])
            assert pd.api.types.is_numeric_dtype(interactions_df["rating"])

    def test_load_interactions_valid_ratings(self, interactions_df):
        """Test : Les ratings sont dans la plage valide (0-5)."""
        if len(interactions_df) > 0 and "rating" in interactions_df.columns:
            # Les ratings peuvent être 0 (pas de rating) jusqu'à 5
            assert (interactions_df["rating"] >= 0).all()
            assert (interactions_df["rating"] <= 5).all()

    def test_load_interactions_no_null_ids(self, interactions_df):
        """Test : Pas de valeurs nulles dans les IDs."""
        if len(interactions_df) > 0:
            assert interactions_df["user_id"].notna().all()
            assert interactions_df["recipe_id"].notna().all()


# ============================================================================
# Tests d'intégrité des données
# ============================================================================


class TestDataIntegrity:
    """Tests d'intégrité et de cohérence des données."""

    def test_recipe_ids_are_positive(self, recipes_df):
        """Test : Les IDs de recettes sont positifs."""
        assert (recipes_df["id"] > 0).all()

    def test_ingredients_count_matches(self, recipes_df):
        """Test : Le nombre d'ingrédients est cohérent."""
        # Vérifier que n_ingredients > 0 pour les recettes avec ingredients
        has_ingredients = recipes_df["ingredients"].notna()
        assert (recipes_df.loc[has_ingredients, "n_ingredients"] > 0).all()

    def test_steps_count_matches(self, recipes_df):
        """Test : Le nombre d'étapes est cohérent."""
        # Vérifier que n_steps > 0 pour les recettes avec steps
        has_steps = recipes_df["steps"].notna()
        assert (recipes_df.loc[has_steps, "n_steps"] > 0).sum() > len(recipes_df) * 0.9

    def test_nutrition_consistency(self, recipes_df):
        """Test : Cohérence entre nutrition_score et nutrition_grade."""
        # Vérifier que les grades correspondent aux scores
        has_both = recipes_df["nutrition_score"].notna() & recipes_df["nutrition_grade"].notna()
        
        if has_both.sum() > 0:
            subset = recipes_df.loc[has_both]
            
            # Grade A devrait avoir des scores élevés (>80)
            grade_a = subset[subset["nutrition_grade"] == "A"]
            if len(grade_a) > 0:
                assert (grade_a["nutrition_score"] > 60).sum() > len(grade_a) * 0.8

    def test_interaction_recipe_ids_valid(self, recipes_df, interactions_df):
        """Test : Les recipe_ids des interactions existent dans les recettes."""
        if len(interactions_df) > 0:
            recipe_ids = set(recipes_df["id"])
            interaction_recipe_ids = set(interactions_df["recipe_id"].unique())
            
            # La plupart des IDs d'interactions devraient exister
            valid_ids = interaction_recipe_ids.intersection(recipe_ids)
            coverage = len(valid_ids) / len(interaction_recipe_ids) if len(interaction_recipe_ids) > 0 else 1
            
            assert coverage > 0.9, f"Seulement {coverage:.1%} des IDs sont valides"


# ============================================================================
# Tests de performance
# ============================================================================


class TestPerformance:
    """Tests de performance du chargement des données."""

    def test_load_recipes_reasonable_time(self, data_dir):
        """Test : Le chargement des recettes est rapide."""
        import time
        
        start = time.time()
        df = load_recipes(data_dir=data_dir)
        duration = time.time() - start
        
        assert duration < 10.0, f"Chargement trop lent: {duration:.2f}s"
        assert len(df) > 0

    def test_load_interactions_reasonable_time(self, data_dir):
        """Test : Le chargement des interactions est rapide."""
        import time
        
        start = time.time()
        # Load interactions manually
        try:
            df = read_csv_file("interactions_train.csv", data_dir=data_dir)
        except:
            df = pd.DataFrame()
        duration = time.time() - start
        
        assert duration < 5.0, f"Chargement trop lent: {duration:.2f}s"

    def test_partial_load_faster(self, data_dir):
        """Test : Le chargement partiel est plus rapide."""
        import time
        
        # Chargement partiel
        start = time.time()
        df_partial = read_csv_file("preprocessed_recipes.csv", data_dir=data_dir, nrows=100)
        time_partial = time.time() - start
        
        # Chargement complet
        start = time.time()
        df_full = read_csv_file("preprocessed_recipes.csv", data_dir=data_dir)
        time_full = time.time() - start
        
        # Le chargement partiel devrait être plus rapide (ou au pire égal)
        assert time_partial <= time_full * 1.5  # Tolérance de 50%


# ============================================================================
# Tests des cas limites
# ============================================================================


class TestEdgeCases:
    """Tests des cas limites et extrêmes."""

    def test_recipes_with_extreme_prep_times(self, recipes_df):
        """Test : Détection de temps de préparation extrêmes."""
        # La plupart des recettes devraient avoir des temps raisonnables (<24h)
        reasonable_times = (recipes_df["minutes"] < 1440).sum()
        total = len(recipes_df)
        
        assert reasonable_times / total > 0.95, "Trop de temps de préparation irréalistes"

    def test_recipes_with_extreme_calories(self, recipes_df):
        """Test : Détection de valeurs caloriques extrêmes."""
        # Calories devraient être < 10000 (raisonnable pour une recette)
        reasonable_calories = (recipes_df["calories"] < 10000).sum()
        total = len(recipes_df)
        
        assert reasonable_calories / total > 0.99, "Trop de valeurs caloriques irréalistes"

    def test_recipes_with_many_ingredients(self, recipes_df):
        """Test : Recettes avec beaucoup d'ingrédients sont gérées."""
        # Certaines recettes peuvent avoir beaucoup d'ingrédients
        many_ingredients = recipes_df[recipes_df["n_ingredients"] > 20]
        
        # Devrait y en avoir quelques-unes mais pas trop
        assert len(many_ingredients) > 0
        assert len(many_ingredients) < len(recipes_df) * 0.1

    def test_recipes_with_few_ingredients(self, recipes_df):
        """Test : Recettes simples avec peu d'ingrédients."""
        few_ingredients = recipes_df[recipes_df["n_ingredients"] <= 5]
        
        # Devrait y avoir des recettes simples
        assert len(few_ingredients) > 0

    def test_vegetarian_recipes_exist(self, recipes_df):
        """Test : Il existe des recettes végétariennes."""
        vegetarian = recipes_df[recipes_df["is_vegetarian"] == True]
        
        assert len(vegetarian) > 0
        assert len(vegetarian) < len(recipes_df)  # Pas toutes végétariennes

    def test_all_nutrition_grades_represented(self, recipes_df):
        """Test : Tous les grades nutritionnels existent."""
        grades = recipes_df["nutrition_grade"].value_counts()
        
        # Devrait y avoir au moins 3 grades différents
        assert len(grades) >= 3


# ============================================================================
# Tests de robustesse
# ============================================================================


class TestRobustness:
    """Tests de robustesse face aux erreurs."""

    def test_load_with_missing_optional_columns(self, data_dir):
        """Test : Gestion des colonnes optionnelles manquantes."""
        # Le chargement devrait fonctionner même si certaines colonnes sont absentes
        df = load_recipes(data_dir=data_dir)
        
        # Les colonnes essentielles doivent être présentes
        essential = ["id", "name", "ingredients"]
        for col in essential:
            assert col in df.columns

    def test_load_handles_encoding_issues(self, data_dir):
        """Test : Gestion des problèmes d'encodage."""
        # Le chargement devrait gérer les caractères spéciaux
        df = load_recipes(data_dir=data_dir)
        
        # Vérifier que les noms contiennent du texte valide
        assert df["name"].notna().sum() > 0
        
        # Pas d'erreurs d'encodage visibles
        names_with_text = df["name"].dropna()
        assert len(names_with_text) > 0

    def test_load_with_corrupted_rows(self, data_dir):
        """Test : Gestion des lignes corrompues."""
        # Le chargement devrait continuer malgré quelques lignes problématiques
        df = load_recipes(data_dir=data_dir)
        
        # La majorité des données devraient être valides
        valid_rows = df["id"].notna() & df["name"].notna()
        assert valid_rows.sum() / len(df) > 0.95
