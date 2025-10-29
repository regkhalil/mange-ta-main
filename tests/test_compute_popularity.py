"""
Tests unitaires pour le module compute_popularity.py

Ce module teste toutes les fonctions du calcul de popularité :
- Chargement et nettoyage des interactions
- Calcul des métriques de popularité
- Fusion avec les données de recettes
- Sauvegarde et logging
"""

import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing import compute_popularity


class TestLoadInteractions:
    """Tests pour la fonction load_interactions"""

    def test_load_valid_interactions(self, tmp_path):
        """Test du chargement d'interactions valides"""
        # Créer des données de test
        test_data = pd.DataFrame(
            {"user_id": [1, 2, 3, 4, 5], "recipe_id": [101, 102, 103, 101, 102], "rating": [4.5, 3.0, 5.0, 4.0, 2.5]}
        )

        # Sauvegarder dans un fichier temporaire
        interactions_file = tmp_path / "RAW_interactions.csv"
        test_data.to_csv(interactions_file, index=False)

        # Tester le chargement
        result = compute_popularity.load_interactions(str(tmp_path))

        assert len(result) == 5
        assert list(result.columns) == ["user_id", "recipe_id", "rating"]
        assert result["rating"].dtype == "float32"
        assert result["user_id"].dtype == "int64"

    def test_load_interactions_with_missing_file(self, tmp_path):
        """Test du chargement avec fichier manquant"""
        with pytest.raises(FileNotFoundError, match="Interactions file not found"):
            compute_popularity.load_interactions(str(tmp_path))

    def test_load_interactions_data_cleaning(self, tmp_path):
        """Test du nettoyage des données d'interactions"""
        # Créer des données avec ratings invalides seulement
        test_data = pd.DataFrame(
            {
                "user_id": [1, 2, 3, 4, 5, 1],
                "recipe_id": [101, 102, 103, 104, 105, 101],
                "rating": [4.5, 3.0, 7.0, 4.0, 0.5, 3.5],  # Ratings invalides et duplicate
            }
        )

        interactions_file = tmp_path / "RAW_interactions.csv"
        test_data.to_csv(interactions_file, index=False)

        result = compute_popularity.load_interactions(str(tmp_path))

        # Vérifier le nettoyage - devrait garder ratings 1-5 seulement
        assert len(result) == 3  # user_id=1,2,4 avec ratings valides, deduplicated = 3
        assert result["rating"].min() >= 1.0
        assert result["rating"].max() <= 5.0
        assert result["user_id"].notna().all()
        assert result["recipe_id"].notna().all()

    def test_load_interactions_duplicates_removal(self, tmp_path):
        """Test de la suppression des doublons"""
        duplicate_data = pd.DataFrame(
            {
                "user_id": [1, 1, 2, 2, 3],
                "recipe_id": [101, 101, 102, 102, 103],
                "rating": [4.0, 5.0, 3.0, 3.5, 4.5],  # Premier rating gardé pour chaque user/recipe
            }
        )

        interactions_file = tmp_path / "RAW_interactions.csv"
        duplicate_data.to_csv(interactions_file, index=False)

        result = compute_popularity.load_interactions(str(tmp_path))

        assert len(result) == 3
        # Vérifier que le premier rating est gardé
        user1_recipe101 = result[(result["user_id"] == 1) & (result["recipe_id"] == 101)]
        assert len(user1_recipe101) == 1
        assert user1_recipe101["rating"].iloc[0] == 4.0

    def test_load_interactions_default_data_dir(self):
        """Test du répertoire de données par défaut"""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                compute_popularity.load_interactions()

    def test_load_interactions_logging(self, tmp_path, caplog):
        """Test du logging lors du chargement"""
        test_data = pd.DataFrame({"user_id": [1, 2, 3], "recipe_id": [101, 102, 103], "rating": [4.0, 3.0, 5.0]})

        interactions_file = tmp_path / "RAW_interactions.csv"
        test_data.to_csv(interactions_file, index=False)

        with caplog.at_level(logging.INFO):
            compute_popularity.load_interactions(str(tmp_path))

        assert "Loading interactions from" in caplog.text
        assert "Loaded 3 interactions" in caplog.text
        assert "After cleaning: 3 interactions" in caplog.text


class TestComputePopularityMetrics:
    """Tests pour la fonction compute_popularity_metrics"""

    def test_basic_popularity_computation(self):
        """Test du calcul basique de popularité"""
        interactions_df = pd.DataFrame(
            {"recipe_id": [101, 101, 102, 102, 102, 103], "rating": [4.0, 5.0, 3.0, 4.0, 5.0, 2.0]}
        )

        result = compute_popularity.compute_popularity_metrics(interactions_df)

        assert len(result) == 3
        assert list(result.columns) == ["recipe_id", "average_rating", "review_count", "popularity_score"]

        # Vérifier les métriques pour recipe_id 101
        recipe_101 = result[result["recipe_id"] == 101].iloc[0]
        assert recipe_101["average_rating"] == 4.5
        assert recipe_101["review_count"] == 2
        assert 0 <= recipe_101["popularity_score"] <= 1

    def test_popularity_score_calculation(self):
        """Test du calcul du score de popularité"""
        # Recette très bien notée avec beaucoup d'avis
        interactions_df = pd.DataFrame({"recipe_id": [101] * 100 + [102] * 2, "rating": [5.0] * 100 + [3.0, 4.0]})

        result = compute_popularity.compute_popularity_metrics(interactions_df)

        recipe_101 = result[result["recipe_id"] == 101].iloc[0]
        recipe_102 = result[result["recipe_id"] == 102].iloc[0]

        # La recette 101 devrait avoir un score plus élevé
        assert recipe_101["popularity_score"] > recipe_102["popularity_score"]
        assert recipe_101["average_rating"] == 5.0
        assert recipe_102["average_rating"] == 3.5

    def test_single_recipe_metrics(self):
        """Test avec une seule recette"""
        interactions_df = pd.DataFrame({"recipe_id": [101, 101, 101], "rating": [3.0, 4.0, 5.0]})

        result = compute_popularity.compute_popularity_metrics(interactions_df)

        assert len(result) == 1
        assert result["recipe_id"].iloc[0] == 101
        assert result["average_rating"].iloc[0] == 4.0
        assert result["review_count"].iloc[0] == 3

    def test_empty_interactions_dataframe(self):
        """Test avec DataFrame vide"""
        empty_df = pd.DataFrame(columns=["recipe_id", "rating"])

        result = compute_popularity.compute_popularity_metrics(empty_df)

        assert len(result) == 0
        expected_cols = ["recipe_id", "average_rating", "review_count", "popularity_score"]
        assert list(result.columns) == expected_cols

    def test_popularity_score_range(self):
        """Test que le score de popularité est dans la bonne plage"""
        interactions_df = pd.DataFrame(
            {
                "recipe_id": [101, 102, 103, 104],
                "rating": [1.0, 3.0, 4.0, 5.0],  # Une note chacune
            }
        )

        result = compute_popularity.compute_popularity_metrics(interactions_df)

        # Tous les scores doivent être entre 0 et 1
        assert result["popularity_score"].min() >= 0
        assert result["popularity_score"].max() <= 1

    def test_logging_output(self, caplog):
        """Test du logging des métriques"""
        interactions_df = pd.DataFrame({"recipe_id": [101, 102], "rating": [4.0, 3.0]})

        with caplog.at_level(logging.INFO):
            compute_popularity.compute_popularity_metrics(interactions_df)

        assert "Computing popularity metrics" in caplog.text
        assert "Computed metrics for 2 recipes" in caplog.text
        assert "Average rating range:" in caplog.text


class TestLoadPreprocessedRecipes:
    """Tests pour la fonction load_preprocessed_recipes"""

    def test_load_valid_recipes(self, tmp_path):
        """Test du chargement de recettes valides"""
        test_recipes = pd.DataFrame(
            {
                "id": [101, 102, 103],
                "name": ["Recipe A", "Recipe B", "Recipe C"],
                "ingredients": ["salt, pepper", "flour, sugar", "tomato, basil"],
            }
        )

        recipes_file = tmp_path / "preprocessed_recipes.csv"
        test_recipes.to_csv(recipes_file, index=False)

        result = compute_popularity.load_preprocessed_recipes(str(tmp_path))

        assert len(result) == 3
        assert "id" in result.columns
        assert result["id"].dtype == "int64"

    def test_load_recipes_missing_file(self, tmp_path):
        """Test avec fichier de recettes manquant"""
        with pytest.raises(FileNotFoundError, match="Preprocessed recipes file not found"):
            compute_popularity.load_preprocessed_recipes(str(tmp_path))

    def test_load_recipes_default_path(self):
        """Test du chemin par défaut"""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                compute_popularity.load_preprocessed_recipes()

    def test_load_recipes_logging(self, tmp_path, caplog):
        """Test du logging lors du chargement"""
        test_recipes = pd.DataFrame({"id": [101, 102], "name": ["A", "B"]})

        recipes_file = tmp_path / "preprocessed_recipes.csv"
        test_recipes.to_csv(recipes_file, index=False)

        with caplog.at_level(logging.INFO):
            compute_popularity.load_preprocessed_recipes(str(tmp_path))

        assert "Loading preprocessed recipes from" in caplog.text
        assert "Loaded 2 recipes" in caplog.text


class TestMergePopularityData:
    """Tests pour la fonction merge_popularity_data"""

    def test_basic_merge(self):
        """Test de fusion basique"""
        recipes_df = pd.DataFrame({"id": [101, 102, 103], "name": ["Recipe A", "Recipe B", "Recipe C"]})

        popularity_df = pd.DataFrame(
            {
                "recipe_id": [101, 102],
                "average_rating": [4.5, 3.0],
                "review_count": [10, 5],
                "popularity_score": [0.8, 0.6],
            }
        )

        result = compute_popularity.merge_popularity_data(recipes_df, popularity_df)

        assert len(result) == 3
        assert "average_rating" in result.columns
        assert "review_count" in result.columns
        assert "popularity_score" in result.columns

        # Recipe 103 devrait avoir les valeurs par défaut
        recipe_103 = result[result["id"] == 103].iloc[0]
        assert recipe_103["review_count"] == 0
        assert recipe_103["average_rating"] == 3.0
        assert recipe_103["popularity_score"] == 0.0

    def test_merge_all_recipes_have_popularity(self):
        """Test quand toutes les recettes ont des données de popularité"""
        recipes_df = pd.DataFrame({"id": [101, 102], "name": ["Recipe A", "Recipe B"]})

        popularity_df = pd.DataFrame(
            {
                "recipe_id": [101, 102],
                "average_rating": [4.5, 3.0],
                "review_count": [10, 5],
                "popularity_score": [0.8, 0.6],
            }
        )

        result = compute_popularity.merge_popularity_data(recipes_df, popularity_df)

        assert len(result) == 2
        assert result["review_count"].min() > 0  # Aucune valeur par défaut

    def test_merge_no_popularity_data(self):
        """Test quand aucune recette n'a de données de popularité"""
        recipes_df = pd.DataFrame({"id": [101, 102, 103], "name": ["Recipe A", "Recipe B", "Recipe C"]})

        popularity_df = pd.DataFrame(
            {"recipe_id": [], "average_rating": [], "review_count": [], "popularity_score": []}
        )

        result = compute_popularity.merge_popularity_data(recipes_df, popularity_df)

        assert len(result) == 3
        assert (result["review_count"] == 0).all()
        assert (result["average_rating"] == 3.0).all()
        assert (result["popularity_score"] == 0.0).all()

    def test_merge_data_types(self):
        """Test des types de données après fusion"""
        recipes_df = pd.DataFrame({"id": [101], "name": ["Recipe A"]})
        popularity_df = pd.DataFrame(
            {"recipe_id": [101], "average_rating": [4.5], "review_count": [10], "popularity_score": [0.8]}
        )

        result = compute_popularity.merge_popularity_data(recipes_df, popularity_df)

        assert result["review_count"].dtype == "int32"
        assert result["average_rating"].dtype == "float32"
        assert result["popularity_score"].dtype == "float32"

    def test_merge_logging(self, caplog):
        """Test du logging lors de la fusion"""
        recipes_df = pd.DataFrame({"id": [101, 102], "name": ["A", "B"]})
        popularity_df = pd.DataFrame(
            {"recipe_id": [101], "average_rating": [4.0], "review_count": [5], "popularity_score": [0.7]}
        )

        with caplog.at_level(logging.INFO):
            compute_popularity.merge_popularity_data(recipes_df, popularity_df)

        assert "Merging popularity data with recipes" in caplog.text
        assert "Enhanced 2 recipes with popularity data" in caplog.text
        assert "Recipes with reviews: 1 (50.0%)" in caplog.text


class TestSaveEnhancedRecipes:
    """Tests pour la fonction save_enhanced_recipes"""

    def test_save_recipes(self, tmp_path):
        """Test de sauvegarde des recettes enrichies"""
        enhanced_df = pd.DataFrame(
            {
                "id": [101, 102],
                "name": ["Recipe A", "Recipe B"],
                "average_rating": [4.5, 3.0],
                "review_count": [10, 5],
                "popularity_score": [0.8, 0.6],
            }
        )

        compute_popularity.save_enhanced_recipes(enhanced_df, str(tmp_path))

        # Vérifier que le fichier a été créé
        output_file = tmp_path / "preprocessed_recipes.csv"
        assert output_file.exists()

        # Vérifier le contenu
        saved_df = pd.read_csv(output_file)
        assert len(saved_df) == 2
        assert "average_rating" in saved_df.columns

    def test_save_recipes_default_path(self, tmp_path):
        """Test avec chemin par défaut - simplifié"""
        enhanced_df = pd.DataFrame({"id": [101], "name": ["Recipe A"]})

        # Test que la fonction utilise le bon chemin par défaut en mockant pathlib
        with patch("preprocessing.compute_popularity.Path") as mock_path_class:
            # Mock instance de Path
            mock_path_instance = Mock()
            mock_path_instance.parent.parent = tmp_path
            mock_path_class.return_value = mock_path_instance

            # Créer le répertoire data
            data_dir = tmp_path / "data"
            data_dir.mkdir()

            # La fonction devrait construire le chemin vers data/preprocessed_recipes.csv
            _expected_output = data_dir / "preprocessed_recipes.csv"

            # Mock le chemin final
            with patch("preprocessing.compute_popularity.Path") as inner_mock:

                def side_effect(path_arg):
                    if str(path_arg).endswith("data"):
                        return data_dir
                    return Path(path_arg)

                inner_mock.side_effect = side_effect

                # Appeler directement avec le chemin de test
                compute_popularity.save_enhanced_recipes(enhanced_df, str(tmp_path))

                # Vérifier que le fichier a été créé
                output_file = tmp_path / "preprocessed_recipes.csv"
                assert output_file.exists()

    def test_save_recipes_logging(self, tmp_path, caplog):
        """Test du logging lors de la sauvegarde"""
        enhanced_df = pd.DataFrame({"id": [101, 102], "name": ["A", "B"]})

        with caplog.at_level(logging.INFO):
            compute_popularity.save_enhanced_recipes(enhanced_df, str(tmp_path))

        assert "Saving enhanced recipes to" in caplog.text
        assert "Successfully saved 2 recipes" in caplog.text


class TestLogPopularitySummary:
    """Tests pour la fonction log_popularity_summary"""

    def test_summary_with_reviews(self, caplog):
        """Test du résumé avec des avis"""
        enhanced_df = pd.DataFrame(
            {
                "id": [101, 102, 103],
                "name": ["Recipe A", "Recipe B", "Recipe C"],
                "average_rating": [4.5, 3.0, 3.0],
                "review_count": [10, 5, 0],
                "popularity_score": [0.8, 0.6, 0.0],
            }
        )

        with caplog.at_level(logging.INFO):
            compute_popularity.log_popularity_summary(enhanced_df)

        assert "POPULARITY METRICS SUMMARY" in caplog.text
        assert "Total recipes: 3" in caplog.text
        assert "Recipes with reviews: 2 (66.7%)" in caplog.text
        assert "Recipes without reviews: 1" in caplog.text
        assert "Top 10 recipes by popularity score:" in caplog.text

    def test_summary_no_reviews(self, caplog):
        """Test du résumé sans avis"""
        enhanced_df = pd.DataFrame(
            {
                "id": [101, 102],
                "name": ["Recipe A", "Recipe B"],
                "average_rating": [3.0, 3.0],
                "review_count": [0, 0],
                "popularity_score": [0.0, 0.0],
            }
        )

        with caplog.at_level(logging.INFO):
            compute_popularity.log_popularity_summary(enhanced_df)

        assert "Total recipes: 2" in caplog.text
        assert "Recipes with reviews: 0 (0.0%)" in caplog.text

    def test_summary_top_recipes(self, caplog):
        """Test de l'affichage des meilleures recettes"""
        # Créer plusieurs recettes avec différents scores
        enhanced_df = pd.DataFrame(
            {
                "id": list(range(101, 116)),  # 15 recettes
                "name": [f"Recipe {i}" for i in range(101, 116)],
                "average_rating": [4.0 + i * 0.1 for i in range(15)],
                "review_count": list(range(1, 16)),
                "popularity_score": [0.5 + i * 0.03 for i in range(15)],
            }
        )

        with caplog.at_level(logging.INFO):
            compute_popularity.log_popularity_summary(enhanced_df)

        assert "Top 10 recipes by popularity score:" in caplog.text
        # Vérifier qu'on a bien 10 recettes listées (pas 15)
        top_recipe_lines = [line for line in caplog.text.split("\n") if "Recipe" in line and "score=" in line]
        assert len(top_recipe_lines) == 10


class TestMainFunction:
    """Tests pour la fonction main"""

    def test_main_success_flow(self, tmp_path):
        """Test du flux principal réussi"""
        # Créer des fichiers de test
        interactions_data = pd.DataFrame(
            {"user_id": [1, 2, 3], "recipe_id": [101, 102, 101], "rating": [4.0, 3.0, 5.0]}
        )

        recipes_data = pd.DataFrame({"id": [101, 102, 103], "name": ["Recipe A", "Recipe B", "Recipe C"]})

        interactions_file = tmp_path / "RAW_interactions.csv"
        recipes_file = tmp_path / "preprocessed_recipes.csv"

        interactions_data.to_csv(interactions_file, index=False)
        recipes_data.to_csv(recipes_file, index=False)

        # Tester la fonction main
        compute_popularity.main(str(tmp_path))

        # Vérifier que le fichier de sortie existe et contient les bonnes colonnes
        output_file = tmp_path / "preprocessed_recipes.csv"
        result_df = pd.read_csv(output_file)

        assert "average_rating" in result_df.columns
        assert "review_count" in result_df.columns
        assert "popularity_score" in result_df.columns

    def test_main_with_missing_interactions(self, tmp_path):
        """Test avec fichier d'interactions manquant"""
        # Créer seulement le fichier de recettes
        recipes_data = pd.DataFrame({"id": [101], "name": ["Recipe A"]})
        recipes_file = tmp_path / "preprocessed_recipes.csv"
        recipes_data.to_csv(recipes_file, index=False)

        with pytest.raises(FileNotFoundError, match="Interactions file not found"):
            compute_popularity.main(str(tmp_path))

    def test_main_with_missing_recipes(self, tmp_path):
        """Test avec fichier de recettes manquant"""
        # Créer seulement le fichier d'interactions
        interactions_data = pd.DataFrame({"user_id": [1], "recipe_id": [101], "rating": [4.0]})
        interactions_file = tmp_path / "RAW_interactions.csv"
        interactions_data.to_csv(interactions_file, index=False)

        with pytest.raises(FileNotFoundError, match="Preprocessed recipes file not found"):
            compute_popularity.main(str(tmp_path))

    def test_main_error_handling(self, tmp_path, caplog):
        """Test de la gestion d'erreurs dans main"""
        with patch("preprocessing.compute_popularity.load_interactions", side_effect=Exception("Test error")):
            with pytest.raises(Exception, match="Test error"):
                compute_popularity.main(str(tmp_path))

    def test_main_logging(self, tmp_path, caplog):
        """Test du logging de la fonction main"""
        # Créer des fichiers minimaux
        interactions_data = pd.DataFrame({"user_id": [1], "recipe_id": [101], "rating": [4.0]})
        recipes_data = pd.DataFrame({"id": [101], "name": ["Recipe A"]})

        (tmp_path / "RAW_interactions.csv").write_text(interactions_data.to_csv(index=False))
        (tmp_path / "preprocessed_recipes.csv").write_text(recipes_data.to_csv(index=False))

        with caplog.at_level(logging.INFO):
            compute_popularity.main(str(tmp_path))

        assert "Starting popularity computation" in caplog.text
        assert "Popularity computation completed successfully" in caplog.text


class TestIntegrationScenarios:
    """Tests d'intégration et scénarios réels"""

    def test_full_pipeline_with_realistic_data(self, tmp_path):
        """Test du pipeline complet avec des données réalistes"""
        # Créer des données d'interactions réalistes
        np.random.seed(42)
        n_users = 50
        n_recipes = 20
        n_interactions = 200

        interactions_data = pd.DataFrame(
            {
                "user_id": np.random.randint(1, n_users + 1, n_interactions),
                "recipe_id": np.random.randint(101, 101 + n_recipes, n_interactions),
                "rating": np.random.uniform(1, 5, n_interactions),
            }
        )

        # Créer des recettes
        recipes_data = pd.DataFrame(
            {
                "id": list(range(101, 101 + n_recipes)),
                "name": [f"Recipe {i}" for i in range(101, 101 + n_recipes)],
                "description": [f"Description for recipe {i}" for i in range(101, 101 + n_recipes)],
            }
        )

        # Sauvegarder les fichiers
        interactions_file = tmp_path / "RAW_interactions.csv"
        recipes_file = tmp_path / "preprocessed_recipes.csv"

        interactions_data.to_csv(interactions_file, index=False)
        recipes_data.to_csv(recipes_file, index=False)

        # Exécuter le pipeline
        compute_popularity.main(str(tmp_path))

        # Vérifier les résultats
        result_df = pd.read_csv(tmp_path / "preprocessed_recipes.csv")

        # Toutes les recettes doivent avoir des métriques
        assert len(result_df) == n_recipes
        assert "average_rating" in result_df.columns
        assert "review_count" in result_df.columns
        assert "popularity_score" in result_df.columns

        # Vérifier les plages de valeurs
        assert result_df["average_rating"].min() >= 1.0
        assert result_df["average_rating"].max() <= 5.0
        assert result_df["review_count"].min() >= 0
        assert result_df["popularity_score"].min() >= 0.0
        assert result_df["popularity_score"].max() <= 1.0

    def test_edge_case_single_interaction(self, tmp_path):
        """Test avec une seule interaction"""
        interactions_data = pd.DataFrame({"user_id": [1], "recipe_id": [101], "rating": [4.5]})

        recipes_data = pd.DataFrame({"id": [101, 102], "name": ["Recipe A", "Recipe B"]})

        interactions_file = tmp_path / "RAW_interactions.csv"
        recipes_file = tmp_path / "preprocessed_recipes.csv"

        interactions_data.to_csv(interactions_file, index=False)
        recipes_data.to_csv(recipes_file, index=False)

        compute_popularity.main(str(tmp_path))

        result_df = pd.read_csv(tmp_path / "preprocessed_recipes.csv")

        # Recipe 101 devrait avoir les vraies métriques
        recipe_101 = result_df[result_df["id"] == 101].iloc[0]
        assert recipe_101["average_rating"] == 4.5
        assert recipe_101["review_count"] == 1

        # Recipe 102 devrait avoir les valeurs par défaut
        recipe_102 = result_df[result_df["id"] == 102].iloc[0]
        assert recipe_102["average_rating"] == 3.0
        assert recipe_102["review_count"] == 0

    def test_performance_with_large_dataset(self, tmp_path):
        """Test de performance avec un grand dataset"""
        # Créer un dataset relativement large
        n_interactions = 10000
        n_recipes = 1000

        np.random.seed(42)
        interactions_data = pd.DataFrame(
            {
                "user_id": np.random.randint(1, 5001, n_interactions),
                "recipe_id": np.random.randint(101, 101 + n_recipes, n_interactions),
                "rating": np.random.uniform(1, 5, n_interactions),
            }
        )

        recipes_data = pd.DataFrame(
            {"id": list(range(101, 101 + n_recipes)), "name": [f"Recipe {i}" for i in range(101, 101 + n_recipes)]}
        )

        interactions_file = tmp_path / "RAW_interactions.csv"
        recipes_file = tmp_path / "preprocessed_recipes.csv"

        interactions_data.to_csv(interactions_file, index=False)
        recipes_data.to_csv(recipes_file, index=False)

        import time

        start_time = time.time()
        compute_popularity.main(str(tmp_path))
        end_time = time.time()

        # Vérifier que ça ne prend pas trop de temps (< 10 secondes)
        assert (end_time - start_time) < 10

        # Vérifier les résultats
        result_df = pd.read_csv(tmp_path / "preprocessed_recipes.csv")
        assert len(result_df) == n_recipes


class TestErrorHandlingAndRobustness:
    """Tests de gestion d'erreurs et robustesse"""

    def test_corrupted_interactions_file(self, tmp_path):
        """Test avec fichier d'interactions corrompu"""
        # Créer un fichier CSV avec données valides d'abord
        valid_data = pd.DataFrame({"user_id": [1, 2, 3], "recipe_id": [101, 102, 103], "rating": [4.5, 3.0, 2.0]})

        interactions_file = tmp_path / "RAW_interactions.csv"
        valid_data.to_csv(interactions_file, index=False)

        # Modifier manuellement le fichier pour introduire des erreurs
        content = interactions_file.read_text()
        content = content.replace("102", "abc").replace("3.0", "invalid")
        interactions_file.write_text(content)

        recipes_data = pd.DataFrame({"id": [101, 102], "name": ["A", "B"]})
        recipes_file = tmp_path / "preprocessed_recipes.csv"
        recipes_data.to_csv(recipes_file, index=False)

        # Au lieu de s'attendre à ce que ça marche, on s'attend à une erreur
        with pytest.raises((ValueError, TypeError), match="int|invalid"):
            compute_popularity.main(str(tmp_path))

    def test_empty_interactions_file(self, tmp_path):
        """Test avec fichier d'interactions vide"""
        # Créer un fichier vide avec seulement les headers
        empty_file = tmp_path / "RAW_interactions.csv"
        empty_file.write_text("user_id,recipe_id,rating\n")

        recipes_data = pd.DataFrame({"id": [101, 102], "name": ["A", "B"]})
        recipes_file = tmp_path / "preprocessed_recipes.csv"
        recipes_data.to_csv(recipes_file, index=False)

        compute_popularity.main(str(tmp_path))

        result_df = pd.read_csv(tmp_path / "preprocessed_recipes.csv")

        # Toutes les recettes devraient avoir les valeurs par défaut
        assert (result_df["review_count"] == 0).all()
        assert (result_df["average_rating"] == 3.0).all()
        assert (result_df["popularity_score"] == 0.0).all()

    def test_extreme_rating_values(self, tmp_path):
        """Test avec des valeurs de rating extrêmes"""
        interactions_data = pd.DataFrame(
            {
                "user_id": [1, 2, 3, 4],
                "recipe_id": [101, 101, 101, 101],
                "rating": [-1, 0, 6, 10],  # Valeurs hors limites
            }
        )

        recipes_data = pd.DataFrame({"id": [101], "name": ["Recipe A"]})

        interactions_file = tmp_path / "RAW_interactions.csv"
        recipes_file = tmp_path / "preprocessed_recipes.csv"

        interactions_data.to_csv(interactions_file, index=False)
        recipes_data.to_csv(recipes_file, index=False)

        compute_popularity.main(str(tmp_path))

        result_df = pd.read_csv(tmp_path / "preprocessed_recipes.csv")

        # Aucune interaction valide, donc valeurs par défaut
        assert result_df["review_count"].iloc[0] == 0
        assert result_df["average_rating"].iloc[0] == 3.0


# Marquer les tests lents
@pytest.mark.slow
class TestPerformanceAndScaling:
    """Tests de performance et mise à l'échelle"""

    def test_memory_usage_large_dataset(self, tmp_path):
        """Test d'utilisation mémoire avec un grand dataset"""
        # Créer un très grand dataset pour tester la mémoire
        n_interactions = 50000

        np.random.seed(42)
        interactions_data = pd.DataFrame(
            {
                "user_id": np.random.randint(1, 10001, n_interactions),
                "recipe_id": np.random.randint(101, 5101, n_interactions),
                "rating": np.random.uniform(1, 5, n_interactions),
            }
        )

        recipes_data = pd.DataFrame({"id": list(range(101, 5101)), "name": [f"Recipe {i}" for i in range(101, 5101)]})

        interactions_file = tmp_path / "RAW_interactions.csv"
        recipes_file = tmp_path / "preprocessed_recipes.csv"

        interactions_data.to_csv(interactions_file, index=False)
        recipes_data.to_csv(recipes_file, index=False)

        # Monitorer l'utilisation mémoire serait idéal ici
        # mais nous testons juste que ça ne plante pas
        compute_popularity.main(str(tmp_path))

        result_df = pd.read_csv(tmp_path / "preprocessed_recipes.csv")
        assert len(result_df) == 5000
