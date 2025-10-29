"""
Tests unitaires pour le module extract_nutrition.py

Ce module teste l'extraction des colonnes nutritionnelles individuelles
depuis le tableau de nutrition du dataset RAW.
"""

# Configuration du path pour les imports
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing import extract_nutrition


class TestExtractNutritionColumns:
    """Tests pour la fonction extract_nutrition_columns"""

    def test_basic_nutrition_extraction(self):
        """Test l'extraction basique des colonnes nutritionnelles"""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Recipe 1", "Recipe 2", "Recipe 3"],
                "nutrition": [
                    [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0],
                    [250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0],
                    [400.0, 20.0, 15.0, 600.0, 25.0, 8.0, 55.0],
                ],
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        # Vérifier que les nouvelles colonnes ont été ajoutées
        expected_columns = ["calories", "total_fat", "sugar", "sodium", "protein", "saturated_fat", "carbohydrates"]

        for col in expected_columns:
            assert col in result.columns

        # Vérifier les valeurs du premier enregistrement
        assert result["calories"].iloc[0] == 300.0
        assert result["total_fat"].iloc[0] == 15.0
        assert result["sugar"].iloc[0] == 10.0
        assert result["sodium"].iloc[0] == 500.0
        assert result["protein"].iloc[0] == 20.0
        assert result["saturated_fat"].iloc[0] == 5.0
        assert result["carbohydrates"].iloc[0] == 45.0

    def test_string_nutrition_arrays(self):
        """Test avec des arrays de nutrition sous forme de strings"""
        df = pd.DataFrame(
            {
                "id": [1, 2],
                "nutrition": [
                    "[300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0]",
                    "[250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0]",
                ],
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        assert result["calories"].iloc[0] == 300.0
        assert result["total_fat"].iloc[0] == 15.0
        assert result["protein"].iloc[1] == 18.0

    def test_mixed_format_nutrition_data(self):
        """Test avec des données de nutrition en formats mixtes"""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "nutrition": [
                    [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0],  # Liste
                    "[250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0]",  # String
                    (400.0, 20.0, 15.0, 600.0, 25.0, 8.0, 55.0),  # Tuple
                ],
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        # Tous les formats devraient être traités correctement
        assert result["calories"].iloc[0] == 300.0
        assert result["calories"].iloc[1] == 250.0
        assert result["calories"].iloc[2] == 400.0

    def test_malformed_nutrition_data(self):
        """Test avec des données de nutrition mal formées"""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "nutrition": [
                    [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0],  # Valide
                    "[300, 15, 10, 500, 20]",  # Trop court (5 éléments au lieu de 7)
                    "invalid_string",  # String invalide
                    None,  # Valeur nulle
                ],
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        # Premier enregistrement valide
        assert result["calories"].iloc[0] == 300.0

        # Enregistrements invalides devraient avoir des zéros
        assert result["calories"].iloc[1] == 0.0
        assert result["calories"].iloc[2] == 0.0
        assert result["calories"].iloc[3] == 0.0

        assert result["protein"].iloc[1] == 0.0
        assert result["protein"].iloc[2] == 0.0
        assert result["protein"].iloc[3] == 0.0

    def test_custom_nutrition_column_name(self):
        """Test avec un nom de colonne de nutrition personnalisé"""
        df = pd.DataFrame(
            {
                "id": [1, 2],
                "custom_nutrition": [
                    [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0],
                    [250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0],
                ],
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df, nutrition_col="custom_nutrition")

        assert result["calories"].iloc[0] == 300.0
        assert result["protein"].iloc[1] == 18.0

    def test_nutrition_data_with_nan_values(self):
        """Test avec des valeurs NaN dans les arrays de nutrition"""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "nutrition": [
                    [300.0, 15.0, np.nan, 500.0, 20.0, 5.0, 45.0],  # NaN dans l'array
                    [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],  # Tous NaN
                    [250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0],  # Valide
                ],
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        # Arrays avec NaN devraient être remplacés par des zéros
        assert result["calories"].iloc[0] == 0.0
        assert result["calories"].iloc[1] == 0.0

        # Array valide devrait être traité normalement
        assert result["calories"].iloc[2] == 250.0

    def test_extract_values_function_directly(self):
        """Test de la fonction interne extract_values"""
        # Test via l'application sur une série
        test_series = pd.Series(
            [
                [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0],
                "[250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0]",
                None,
                "invalid",
                [1, 2, 3],  # Trop court
            ]
        )

        df = pd.DataFrame({"nutrition": test_series})
        result = extract_nutrition.extract_nutrition_columns(df)

        # Premier: valide
        assert result["calories"].iloc[0] == 300.0
        # Deuxième: string valide
        assert result["calories"].iloc[1] == 250.0
        # Troisième: None -> 0
        assert result["calories"].iloc[2] == 0.0
        # Quatrième: invalid -> 0
        assert result["calories"].iloc[3] == 0.0
        # Cinquième: trop court -> 0
        assert result["calories"].iloc[4] == 0.0

    def test_large_dataset_performance(self):
        """Test de performance avec un grand dataset"""
        # Créer un grand DataFrame
        n_rows = 10000
        nutrition_data = []

        for i in range(n_rows):
            nutrition_data.append(
                [
                    float(200 + i % 300),  # calories
                    float(10 + i % 20),  # total_fat
                    float(5 + i % 15),  # sugar
                    float(400 + i % 600),  # sodium
                    float(15 + i % 25),  # protein
                    float(3 + i % 10),  # saturated_fat
                    float(30 + i % 50),  # carbohydrates
                ]
            )

        df = pd.DataFrame({"id": range(n_rows), "nutrition": nutrition_data})

        import time

        start_time = time.time()
        result = extract_nutrition.extract_nutrition_columns(df)
        end_time = time.time()

        # Vérifier que l'extraction s'est bien passée
        assert len(result) == n_rows
        assert "calories" in result.columns

        # Vérifier que ça s'exécute en temps raisonnable (< 5 secondes)
        execution_time = end_time - start_time
        assert execution_time < 5.0

    def test_data_types_of_extracted_columns(self):
        """Test les types de données des colonnes extraites"""
        df = pd.DataFrame(
            {"nutrition": [[300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0], [250.5, 12.3, 8.7, 400.2, 18.9, 4.1, 40.6]]}
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        # Toutes les colonnes nutritionnelles devraient être de type float
        nutrition_cols = ["calories", "total_fat", "sugar", "sodium", "protein", "saturated_fat", "carbohydrates"]

        for col in nutrition_cols:
            assert pd.api.types.is_float_dtype(result[col])

    def test_original_columns_preserved(self):
        """Test que les colonnes originales sont préservées"""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Recipe 1", "Recipe 2", "Recipe 3"],
                "description": ["Desc 1", "Desc 2", "Desc 3"],
                "nutrition": [
                    [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0],
                    [250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0],
                    [400.0, 20.0, 15.0, 600.0, 25.0, 8.0, 55.0],
                ],
            }
        )

        original_columns = set(df.columns)
        result = extract_nutrition.extract_nutrition_columns(df)

        # Toutes les colonnes originales devraient être présentes
        assert original_columns.issubset(set(result.columns))

        # Les valeurs originales devraient être inchangées
        pd.testing.assert_series_equal(df["id"], result["id"])
        pd.testing.assert_series_equal(df["name"], result["name"])

    def test_copy_behavior(self):
        """Test que la fonction ne modifie pas le DataFrame original"""
        df = pd.DataFrame(
            {
                "id": [1, 2],
                "nutrition": [[300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0], [250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0]],
            }
        )

        original_columns = list(df.columns)
        original_shape = df.shape

        _result = extract_nutrition.extract_nutrition_columns(df)

        # Le DataFrame original ne devrait pas être modifié
        assert list(df.columns) == original_columns
        assert df.shape == original_shape
        assert "calories" not in df.columns

    def test_empty_dataframe(self):
        """Test avec un DataFrame vide"""
        df = pd.DataFrame(columns=["nutrition"])

        result = extract_nutrition.extract_nutrition_columns(df)

        # Devrait créer les colonnes même avec un DataFrame vide
        expected_columns = [
            "nutrition",
            "calories",
            "total_fat",
            "sugar",
            "sodium",
            "protein",
            "saturated_fat",
            "carbohydrates",
        ]

        for col in expected_columns:
            assert col in result.columns

        assert len(result) == 0

    def test_nutrition_values_edge_cases(self):
        """Test avec des valeurs nutritionnelles extrêmes"""
        df = pd.DataFrame(
            {
                "nutrition": [
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Tous zéros
                    [9999.0, 999.0, 500.0, 5000.0, 200.0, 100.0, 800.0],  # Valeurs très élevées
                    [1.1, 0.1, 0.01, 1.5, 0.5, 0.05, 2.3],  # Valeurs très faibles
                    [-1.0, -2.0, -3.0, -4.0, -5.0, -6.0, -7.0],  # Valeurs négatives
                ]
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        # Toutes les valeurs devraient être extraites telles quelles
        assert result["calories"].iloc[0] == 0.0
        assert result["calories"].iloc[1] == 9999.0
        assert result["calories"].iloc[2] == 1.1
        assert result["calories"].iloc[3] == -1.0  # Même les valeurs négatives

    def test_logging_output(self, caplog):
        """Test que les bonnes informations de logging sont générées"""
        df = pd.DataFrame(
            {"nutrition": [[300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0], [250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0]]}
        )

        import logging

        with caplog.at_level(logging.INFO):
            _result = extract_nutrition.extract_nutrition_columns(df)

        # Vérifier que les messages de log appropriés ont été générés
        log_messages = [record.message for record in caplog.records]

        assert any("Extracting individual nutrition columns" in msg for msg in log_messages)
        assert any("Extracted nutrition columns" in msg for msg in log_messages)
        assert any("Sample values" in msg for msg in log_messages)


class TestRealWorldScenarios:
    """Tests avec des scénarios du monde réel"""

    def test_kaggle_food_dataset_format(self):
        """Test avec le format exact du dataset Kaggle Food.com"""
        # Simule le format exact du dataset
        df = pd.DataFrame(
            {
                "name": ["Chocolate Chip Cookies", "Pasta Carbonara", "Green Smoothie"],
                "id": [123456, 789012, 345678],
                "minutes": [45, 30, 5],
                "contributor_id": [111, 222, 333],
                "submitted": ["2010-01-01", "2011-02-15", "2012-03-30"],
                "tags": [
                    "['dessert', 'cookies', 'baking']",
                    "['pasta', 'italian', 'dinner']",
                    "['smoothie', 'healthy', 'breakfast']",
                ],
                "nutrition": [
                    [320.5, 16.2, 18.7, 285.3, 4.8, 7.9, 42.1],
                    [578.2, 28.4, 2.1, 892.5, 26.3, 12.1, 52.7],
                    [156.8, 0.9, 28.4, 42.1, 5.2, 0.2, 38.9],
                ],
                "n_steps": [8, 6, 3],
                "steps": [
                    "['Preheat oven', 'Mix ingredients', 'Bake']",
                    "['Boil water', 'Cook pasta', 'Make sauce']",
                    "['Add ingredients', 'Blend', 'Serve']",
                ],
                "description": [
                    "Classic chocolate chip cookies",
                    "Traditional Italian pasta dish",
                    "Healthy green smoothie",
                ],
                "ingredients": [
                    "['flour', 'sugar', 'chocolate chips']",
                    "['pasta', 'eggs', 'bacon', 'cheese']",
                    "['spinach', 'banana', 'apple juice']",
                ],
                "n_ingredients": [8, 6, 4],
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        # Vérifier que toutes les colonnes nutritionnelles sont ajoutées
        nutrition_cols = ["calories", "total_fat", "sugar", "sodium", "protein", "saturated_fat", "carbohydrates"]

        for col in nutrition_cols:
            assert col in result.columns

        # Vérifier quelques valeurs spécifiques
        assert abs(result["calories"].iloc[0] - 320.5) < 0.01
        assert abs(result["protein"].iloc[1] - 26.3) < 0.01
        assert abs(result["sugar"].iloc[2] - 28.4) < 0.01

        # Vérifier que toutes les colonnes originales sont préservées
        for col in df.columns:
            assert col in result.columns

    def test_inconsistent_nutrition_data_quality(self):
        """Test avec des données de qualité incohérente (réaliste)"""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "nutrition": [
                    [320.5, 16.2, 18.7, 285.3, 4.8, 7.9, 42.1],  # Parfait
                    "[578.2, 28.4, 2.1, 892.5, 26.3, 12.1, 52.7]",  # String OK
                    "['320', '16', '18', '285', '4', '7', '42']",  # String avec quotes
                    [156.8, 0.9, 28.4, 42.1, 5.2],  # Trop court
                    "malformed data",  # Complètement cassé
                ],
            }
        )

        result = extract_nutrition.extract_nutrition_columns(df)

        # Premier et deuxième devraient fonctionner
        assert result["calories"].iloc[0] == 320.5
        assert result["calories"].iloc[1] == 578.2

        # Troisième pourrait fonctionner ou pas selon l'implémentation
        # Quatrième et cinquième devraient être 0
        assert result["calories"].iloc[3] == 0.0
        assert result["calories"].iloc[4] == 0.0

    def test_statistics_and_summary(self):
        """Test des statistiques sur les données extraites"""
        # Créer des données avec des valeurs connues pour tester les statistiques
        nutrition_data = [
            [200, 10, 5, 300, 15, 3, 25],
            [400, 20, 15, 600, 30, 10, 50],
            [300, 15, 10, 450, 22, 6, 37],
            [250, 12, 8, 375, 18, 4, 31],
            [350, 18, 12, 525, 25, 8, 44],
        ]

        df = pd.DataFrame({"id": range(1, 6), "nutrition": nutrition_data})

        result = extract_nutrition.extract_nutrition_columns(df)

        # Vérifier les moyennes
        assert abs(result["calories"].mean() - 300.0) < 0.1
        assert abs(result["protein"].mean() - 22.0) < 0.1

        # Vérifier les min/max
        assert result["calories"].min() == 200
        assert result["calories"].max() == 400
        assert result["protein"].min() == 15
        assert result["protein"].max() == 30

    def test_memory_efficiency_large_dataset(self):
        """Test d'efficacité mémoire avec un grand dataset"""
        import os

        import psutil

        # Mesurer l'utilisation mémoire avant
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Créer un grand dataset
        n_rows = 50000
        nutrition_data = []
        for i in range(n_rows):
            nutrition_data.append(
                [
                    200 + (i % 300),
                    10 + (i % 20),
                    5 + (i % 15),
                    400 + (i % 600),
                    15 + (i % 25),
                    3 + (i % 10),
                    30 + (i % 50),
                ]
            )

        df = pd.DataFrame({"id": range(n_rows), "nutrition": nutrition_data})

        # Traiter les données
        result = extract_nutrition.extract_nutrition_columns(df)

        # Mesurer l'utilisation mémoire après
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        # Vérifier que les données sont correctes
        assert len(result) == n_rows
        assert "calories" in result.columns

        # L'augmentation de mémoire ne devrait pas être excessive
        # (difficile de définir une limite précise, mais < 500MB semble raisonnable)
        assert memory_increase < 500


@pytest.fixture
def sample_nutrition_df():
    """Fixture pour DataFrame avec données nutritionnelles d'exemple"""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Recipe A", "Recipe B", "Recipe C", "Recipe D", "Recipe E"],
            "nutrition": [
                [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0],
                [250.0, 12.0, 8.0, 400.0, 18.0, 4.0, 40.0],
                [400.0, 20.0, 15.0, 600.0, 25.0, 8.0, 55.0],
                [180.0, 8.0, 5.0, 200.0, 12.0, 2.0, 25.0],
                [520.0, 25.0, 20.0, 800.0, 30.0, 12.0, 65.0],
            ],
            "other_data": ["A", "B", "C", "D", "E"],
        }
    )


class TestIntegrationScenarios:
    """Tests d'intégration et scénarios complets"""

    def test_integration_with_preprocessing_pipeline(self, sample_nutrition_df):
        """Test d'intégration avec le pipeline de preprocessing complet"""
        # Simuler d'autres étapes de preprocessing
        df = sample_nutrition_df.copy()

        # Étape 1: extraction nutrition
        df = extract_nutrition.extract_nutrition_columns(df)

        # Vérifier que l'extraction fonctionne
        assert "calories" in df.columns
        assert "protein" in df.columns

        # Étape 2: simuler d'autres transformations qui pourraient suivre
        df["calories_per_protein"] = df["calories"] / df["protein"]
        df["high_protein"] = df["protein"] > 20

        # Vérifier que tout fonctionne ensemble
        assert "calories_per_protein" in df.columns
        assert df["high_protein"].sum() == 3  # 3 recettes avec >20g protéines

    def test_compatibility_with_pandas_operations(self, sample_nutrition_df):
        """Test de compatibilité avec les opérations pandas courantes"""
        result = extract_nutrition.extract_nutrition_columns(sample_nutrition_df)

        # Groupby operations
        grouped = result.groupby("other_data")["calories"].mean()
        assert len(grouped) == 5

        # Filtering operations
        high_cal = result[result["calories"] > 300]
        assert len(high_cal) == 3

        # Sorting operations
        sorted_df = result.sort_values("protein", ascending=False)
        assert sorted_df["protein"].iloc[0] == 30.0

        # Merging operations (simulé)
        other_df = pd.DataFrame({"id": [1, 2, 3], "category": ["A", "B", "C"]})
        merged = result.merge(other_df, on="id", how="left")
        assert "category" in merged.columns
