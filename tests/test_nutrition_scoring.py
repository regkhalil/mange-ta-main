"""
Tests unitaires pour le module nutrition_scoring.py

Ce module teste le système complet de scoring nutritionnel :
- Parsing des données nutritionnelles
- Scoring individuel des nutriments
- Algorithme de scoring équilibré
- Normalisation des scores
- Attribution des grades
- Fonction principale score_nutrition
"""

import ast
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

# Configuration du path pour les imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing import nutrition_scoring


class TestParseNutritionEntry:
    """Tests pour la fonction parse_nutrition_entry"""

    def test_valid_list_input(self):
        """Test avec une liste valide en entrée"""
        nutrition_list = [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0]
        result = nutrition_scoring.parse_nutrition_entry(nutrition_list)
        
        assert result == nutrition_list
        assert len(result) == 7

    def test_valid_tuple_input(self):
        """Test avec un tuple valide en entrée"""
        nutrition_tuple = (300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0)
        result = nutrition_scoring.parse_nutrition_entry(nutrition_tuple)
        
        assert result == list(nutrition_tuple)
        assert len(result) == 7

    def test_valid_string_input(self):
        """Test avec une string valide en entrée"""
        nutrition_string = "[300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0]"
        result = nutrition_scoring.parse_nutrition_entry(nutrition_string)
        
        assert result == [300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0]
        assert len(result) == 7

    def test_invalid_string_input(self):
        """Test avec une string invalide"""
        invalid_strings = [
            "invalid_string",
            "[1, 2, 3",  # Pas fermé
            "not a list",
            "[a, b, c, d, e, f, g]"  # Pas des nombres
        ]
        
        for invalid in invalid_strings:
            result = nutrition_scoring.parse_nutrition_entry(invalid)
            assert result is None

    def test_wrong_length_input(self):
        """Test avec une liste de mauvaise longueur"""
        wrong_lengths = [
            [1, 2, 3],  # Trop court
            [1, 2, 3, 4, 5, 6, 7, 8, 9],  # Trop long
            []  # Vide
        ]
        
        for wrong_length in wrong_lengths:
            result = nutrition_scoring.parse_nutrition_entry(wrong_length)
            assert result is None

    def test_none_and_nan_input(self):
        """Test avec None et NaN"""
        assert nutrition_scoring.parse_nutrition_entry(None) is None
        assert nutrition_scoring.parse_nutrition_entry(pd.NA) is None
        assert nutrition_scoring.parse_nutrition_entry(np.nan) is None

    def test_list_with_nan_values(self):
        """Test avec une liste contenant des NaN"""
        nutrition_with_nan = [300.0, np.nan, 10.0, 500.0, 20.0, 5.0, 45.0]
        result = nutrition_scoring.parse_nutrition_entry(nutrition_with_nan)
        
        assert result is None  # Devrait rejeter les listes avec NaN


class TestScoreNutrientInRange:
    """Tests pour la fonction score_nutrient_in_range"""

    def test_calories_scoring(self):
        """Test du scoring des calories"""
        # Dans la plage optimale (150-600 kcal)
        assert nutrition_scoring.score_nutrient_in_range(300, "calories") == 10.0
        assert nutrition_scoring.score_nutrient_in_range(150, "calories") == 10.0
        assert nutrition_scoring.score_nutrient_in_range(600, "calories") == 10.0
        
        # Au-dessus de l'optimal mais acceptable (600-800)
        score_700 = nutrition_scoring.score_nutrient_in_range(700, "calories")
        assert 5.0 <= score_700 < 10.0
        
        # En dessous de l'optimal
        score_100 = nutrition_scoring.score_nutrient_in_range(100, "calories")
        assert 0.0 <= score_100 < 10.0
        
        # Beaucoup trop élevé
        score_1200 = nutrition_scoring.score_nutrient_in_range(1200, "calories")
        assert 0.0 <= score_1200 <= 5.0

    def test_protein_scoring(self):
        """Test du scoring des protéines"""
        # Dans la plage optimale (30-70% DV)
        assert nutrition_scoring.score_nutrient_in_range(50, "protein") == 10.0
        
        # Trop bas
        score_10 = nutrition_scoring.score_nutrient_in_range(10, "protein")
        assert 0.0 <= score_10 < 10.0
        
        # Trop élevé
        score_150 = nutrition_scoring.score_nutrient_in_range(150, "protein")
        assert 0.0 <= score_150 <= 5.0

    def test_saturated_fat_scoring(self):
        """Test du scoring des graisses saturées"""
        # Optimal (bas est mieux)
        assert nutrition_scoring.score_nutrient_in_range(0, "saturated_fat") == 10.0
        assert nutrition_scoring.score_nutrient_in_range(20, "saturated_fat") == 10.0
        
        # Acceptable
        score_50 = nutrition_scoring.score_nutrient_in_range(50, "saturated_fat")
        assert 5.0 <= score_50 < 10.0
        
        # Trop élevé
        score_120 = nutrition_scoring.score_nutrient_in_range(120, "saturated_fat")
        assert 0.0 <= score_120 <= 5.0

    def test_sodium_scoring(self):
        """Test du scoring du sodium"""
        # Optimal (bas est mieux)
        assert nutrition_scoring.score_nutrient_in_range(0, "sodium") == 10.0
        assert nutrition_scoring.score_nutrient_in_range(15, "sodium") == 10.0
        
        # Acceptable
        score_30 = nutrition_scoring.score_nutrient_in_range(30, "sodium")
        assert 5.0 <= score_30 < 10.0
        
        # Trop élevé
        score_60 = nutrition_scoring.score_nutrient_in_range(60, "sodium")
        assert 0.0 <= score_60 <= 5.0

    def test_sugar_scoring(self):
        """Test du scoring du sucre"""
        # Optimal (bas est mieux)
        assert nutrition_scoring.score_nutrient_in_range(0, "sugar") == 10.0
        assert nutrition_scoring.score_nutrient_in_range(25, "sugar") == 10.0
        
        # Trop élevé
        score_80 = nutrition_scoring.score_nutrient_in_range(80, "sugar")
        assert 0.0 <= score_80 <= 5.0

    def test_unknown_nutrient(self):
        """Test avec un nutriment non défini"""
        result = nutrition_scoring.score_nutrient_in_range(50, "unknown_nutrient")
        assert result == 5.0  # Score neutre


class TestComputeBalancedScore:
    """Tests pour la fonction compute_balanced_score"""

    def test_perfect_nutrition_profile(self):
        """Test avec un profil nutritionnel parfait"""
        # Calories: 400 (optimal), Protein: 50% DV (optimal), etc.
        perfect_nutrition = [400, 20, 10, 15, 50, 25, 20]  # Valeurs dans plages optimales
        
        score = nutrition_scoring.compute_balanced_score(perfect_nutrition)
        
        assert score is not None
        assert score > 80  # Devrait avoir un score élevé

    def test_poor_nutrition_profile(self):
        """Test avec un profil nutritionnel pauvre"""
        # Valeurs excessives ou déséquilibrées
        poor_nutrition = [1500, 100, 150, 80, 200, 150, 200]  # Valeurs excessives
        
        score = nutrition_scoring.compute_balanced_score(poor_nutrition)
        
        assert score is not None
        assert score < 50  # Devrait avoir un score faible

    def test_balanced_nutrition_profile(self):
        """Test avec un profil équilibré mais pas parfait"""
        balanced_nutrition = [350, 25, 15, 25, 60, 40, 35]
        
        score = nutrition_scoring.compute_balanced_score(balanced_nutrition)
        
        assert score is not None
        assert 40 < score < 90  # Score moyen à bon

    def test_none_input(self):
        """Test avec None en entrée"""
        assert nutrition_scoring.compute_balanced_score(None) is None

    def test_balance_bonus_calculation(self):
        """Test du calcul du bonus d'équilibre"""
        # Créer un profil avec plusieurs nutriments dans la plage optimale
        # [calories, total_fat, sugar, sodium, protein, saturated_fat, carbs]
        optimal_nutrition = [300, 15, 5, 10, 40, 20, 15]  # Plusieurs dans plages optimales
        
        score = nutrition_scoring.compute_balanced_score(optimal_nutrition)
        
        # Devrait avoir un bonus d'équilibre significatif
        assert score is not None
        assert score > 70

    def test_extreme_penalty_application(self):
        """Test de l'application des pénalités extrêmes"""
        # Valeurs extrêmement élevées pour déclencher des pénalités
        extreme_nutrition = [2000, 150, 200, 100, 200, 200, 100]
        
        score = nutrition_scoring.compute_balanced_score(extreme_nutrition)
        
        assert score is not None
        assert score < 30  # Devrait être très pénalisé

    def test_nutrient_weights_application(self):
        """Test de l'application des poids des nutriments"""
        # Tester que les graisses saturées (poids élevé) ont plus d'impact
        high_sat_fat = [300, 15, 5, 10, 40, 150, 15]  # Graisses saturées très élevées
        high_carbs = [300, 15, 5, 10, 40, 20, 150]     # Glucides très élevés
        
        score_sat_fat = nutrition_scoring.compute_balanced_score(high_sat_fat)
        score_carbs = nutrition_scoring.compute_balanced_score(high_carbs)
        
        # Les graisses saturées devraient avoir plus d'impact négatif
        assert score_sat_fat < score_carbs

    def test_score_range_boundaries(self):
        """Test que les scores restent dans les limites attendues"""
        test_cases = [
            [0, 0, 0, 0, 0, 0, 0],  # Tous zéros
            [5000, 200, 300, 200, 300, 300, 300],  # Valeurs extrêmes
            [200, 10, 5, 8, 30, 15, 25],  # Valeurs raisonnables
        ]
        
        for nutrition in test_cases:
            score = nutrition_scoring.compute_balanced_score(nutrition)
            assert score is not None
            assert 0 <= score <= 110  # Plage théorique avant normalisation


class TestNormalizeScores:
    """Tests pour la fonction normalize_scores"""

    def test_basic_normalization(self):
        """Test de normalisation basique"""
        scores = pd.Series([20, 40, 60, 80, 100])
        normalized = nutrition_scoring.normalize_scores(scores)
        
        # Vérifier que tous les scores sont dans la plage [10, 98]
        assert all(10 <= score <= 98 for score in normalized)
        assert normalized.min() >= 10
        assert normalized.max() <= 98

    def test_normalization_with_outliers(self):
        """Test de normalisation avec des valeurs aberrantes"""
        scores = pd.Series([1, 5, 50, 55, 60, 200])  # 200 est une valeur aberrante
        normalized = nutrition_scoring.normalize_scores(scores)
        
        # La normalisation devrait gérer les outliers
        assert all(10 <= score <= 98 for score in normalized)

    def test_normalization_preserves_order(self):
        """Test que la normalisation préserve l'ordre"""
        scores = pd.Series([10, 30, 50, 70, 90])
        normalized = nutrition_scoring.normalize_scores(scores)
        
        # L'ordre devrait être préservé
        for i in range(len(normalized) - 1):
            assert normalized.iloc[i] <= normalized.iloc[i + 1]

    def test_normalization_with_nan_values(self):
        """Test de normalisation avec des valeurs NaN"""
        scores = pd.Series([20, np.nan, 60, 80, np.nan])
        normalized = nutrition_scoring.normalize_scores(scores)
        
        # Les NaN devraient rester NaN
        assert pd.isna(normalized.iloc[1])
        assert pd.isna(normalized.iloc[4])
        
        # Les valeurs valides devraient être normalisées
        valid_scores = normalized.dropna()
        assert all(10 <= score <= 98 for score in valid_scores)

    def test_empty_series_normalization(self):
        """Test de normalisation d'une série vide"""
        empty_scores = pd.Series([], dtype=float)
        normalized = nutrition_scoring.normalize_scores(empty_scores)
        
        assert len(normalized) == 0

    def test_all_nan_series_normalization(self):
        """Test de normalisation d'une série avec que des NaN"""
        nan_scores = pd.Series([np.nan, np.nan, np.nan])
        normalized = nutrition_scoring.normalize_scores(nan_scores)
        
        assert all(pd.isna(score) for score in normalized)

    def test_custom_min_max_range(self):
        """Test de normalisation avec plage personnalisée"""
        scores = pd.Series([20, 40, 60, 80, 100])
        normalized = nutrition_scoring.normalize_scores(scores, min_val=0, max_val=100)
        
        assert all(0 <= score <= 100 for score in normalized)


class TestAssignGrade:
    """Tests pour la fonction assign_grade"""

    def test_grade_assignments(self):
        """Test des attributions de grades"""
        # Test de tous les grades
        assert nutrition_scoring.assign_grade(95) == "A"
        assert nutrition_scoring.assign_grade(85) == "A"
        assert nutrition_scoring.assign_grade(84) == "B"
        assert nutrition_scoring.assign_grade(70) == "B"
        assert nutrition_scoring.assign_grade(69) == "C"
        assert nutrition_scoring.assign_grade(55) == "C"
        assert nutrition_scoring.assign_grade(54) == "D"
        assert nutrition_scoring.assign_grade(40) == "D"
        assert nutrition_scoring.assign_grade(39) == "E"
        assert nutrition_scoring.assign_grade(10) == "E"

    def test_boundary_values(self):
        """Test des valeurs limites"""
        # Tester exactement les seuils
        assert nutrition_scoring.assign_grade(85.0) == "A"
        assert nutrition_scoring.assign_grade(84.9) == "B"
        assert nutrition_scoring.assign_grade(70.0) == "B"
        assert nutrition_scoring.assign_grade(69.9) == "C"

    def test_nan_input(self):
        """Test avec NaN en entrée"""
        assert nutrition_scoring.assign_grade(np.nan) is None
        assert nutrition_scoring.assign_grade(pd.NA) is None

    def test_extreme_values(self):
        """Test avec des valeurs extrêmes"""
        # Valeurs au-delà de la plage normale
        assert nutrition_scoring.assign_grade(150) == "A"  # Au-dessus de 98
        assert nutrition_scoring.assign_grade(-10) == "E"   # En dessous de 10


class TestScoreNutritionMainFunction:
    """Tests pour la fonction principale score_nutrition"""

    def create_sample_dataframe(self):
        """Créer un DataFrame d'exemple pour les tests"""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Recipe A', 'Recipe B', 'Recipe C', 'Recipe D', 'Recipe E'],
            'nutrition': [
                [300, 15, 10, 500, 20, 5, 45],    # Équilibré
                [600, 30, 25, 1000, 40, 15, 80],  # Élevé
                [150, 5, 2, 200, 10, 1, 20],      # Faible
                [800, 40, 35, 1500, 50, 20, 100], # Très élevé
                [200, 8, 5, 300, 15, 3, 25]       # Bon équilibre
            ]
        })

    def test_basic_scoring_functionality(self):
        """Test de la fonctionnalité de base du scoring"""
        df = self.create_sample_dataframe()
        result = nutrition_scoring.score_nutrition(df)
        
        # Vérifier que les nouvelles colonnes ont été ajoutées
        assert 'nutrition_score' in result.columns
        assert 'nutrition_grade' in result.columns
        assert 'calories' in result.columns
        
        # Vérifier que les scores sont dans la bonne plage
        scores = result['nutrition_score'].dropna()
        assert all(10 <= score <= 98 for score in scores)
        
        # Vérifier que les grades sont valides
        grades = result['nutrition_grade'].dropna()
        valid_grades = {'A', 'B', 'C', 'D', 'E'}
        assert all(grade in valid_grades for grade in grades)

    def test_custom_nutrition_column(self):
        """Test avec un nom de colonne nutrition personnalisé"""
        df = pd.DataFrame({
            'custom_nutrition': [
                [300, 15, 10, 500, 20, 5, 45],
                [200, 8, 5, 300, 15, 3, 25]
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df, nutrition_col='custom_nutrition')
        
        assert 'nutrition_score' in result.columns
        assert 'nutrition_grade' in result.columns

    def test_mixed_valid_invalid_data(self):
        """Test avec un mélange de données valides et invalides"""
        df = pd.DataFrame({
            'nutrition': [
                [300, 15, 10, 500, 20, 5, 45],  # Valide
                "invalid_string",                # Invalide
                None,                            # Invalide
                [200, 8, 5, 300, 15, 3, 25],    # Valide
                [1, 2, 3]                        # Invalide (trop court)
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Les entrées valides devraient avoir des scores
        assert not pd.isna(result['nutrition_score'].iloc[0])
        assert not pd.isna(result['nutrition_score'].iloc[3])
        
        # Les entrées invalides devraient avoir NaN
        assert pd.isna(result['nutrition_score'].iloc[1])
        assert pd.isna(result['nutrition_score'].iloc[2])
        assert pd.isna(result['nutrition_score'].iloc[4])

    def test_calories_extraction(self):
        """Test de l'extraction des calories"""
        df = pd.DataFrame({
            'nutrition': [
                [300, 15, 10, 500, 20, 5, 45],
                [250, 12, 8, 400, 18, 4, 40],
                "invalid"
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Vérifier l'extraction des calories
        assert result['calories'].iloc[0] == 300.0
        assert result['calories'].iloc[1] == 250.0
        assert result['calories'].iloc[2] == 0.0  # Invalide -> 0

    def test_large_dataset_performance(self):
        """Test de performance avec un grand dataset"""
        n_rows = 5000
        nutrition_data = []
        
        for i in range(n_rows):
            nutrition_data.append([
                200 + (i % 400),   # calories
                10 + (i % 20),     # total_fat
                5 + (i % 15),      # sugar
                300 + (i % 700),   # sodium
                15 + (i % 30),     # protein
                3 + (i % 12),      # saturated_fat
                25 + (i % 50)      # carbohydrates
            ])
        
        df = pd.DataFrame({
            'id': range(n_rows),
            'nutrition': nutrition_data
        })
        
        import time
        start_time = time.time()
        result = nutrition_scoring.score_nutrition(df)
        end_time = time.time()
        
        # Vérifier que ça s'exécute en temps raisonnable
        execution_time = end_time - start_time
        assert execution_time < 10.0  # Moins de 10 secondes
        
        # Vérifier que tous les scores ont été calculés
        assert len(result) == n_rows
        valid_scores = result['nutrition_score'].dropna()
        assert len(valid_scores) == n_rows

    def test_copy_behavior(self):
        """Test que la fonction ne modifie pas le DataFrame original"""
        df = self.create_sample_dataframe()
        original_columns = list(df.columns)
        original_shape = df.shape
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Le DataFrame original ne devrait pas être modifié
        assert list(df.columns) == original_columns
        assert df.shape == original_shape
        assert 'nutrition_score' not in df.columns

    def test_logging_output(self, caplog):
        """Test des messages de logging"""
        df = self.create_sample_dataframe()
        
        import logging
        with caplog.at_level(logging.INFO):
            nutrition_scoring.score_nutrition(df)
        
        # Vérifier que les messages appropriés sont loggés
        log_messages = [record.message for record in caplog.records]
        
        assert any("Starting nutrition scoring" in msg for msg in log_messages)
        assert any("Nutrition scoring completed" in msg for msg in log_messages)
        assert any("Grade distribution" in msg for msg in log_messages)


class TestHealthyRangesConfiguration:
    """Tests pour la configuration des plages santé"""

    def test_healthy_ranges_completeness(self):
        """Test que toutes les plages santé nécessaires sont définies"""
        required_nutrients = [
            'calories', 'protein', 'total_fat', 'saturated_fat',
            'sugar', 'sodium', 'carbs'
        ]
        
        for nutrient in required_nutrients:
            assert nutrient in nutrition_scoring.HEALTHY_RANGES
            
            ranges = nutrition_scoring.HEALTHY_RANGES[nutrient]
            assert 'min_optimal' in ranges
            assert 'max_optimal' in ranges
            assert 'max_acceptable' in ranges
            assert 'description' in ranges

    def test_nutrient_weights_sum(self):
        """Test que les poids des nutriments somment à 1"""
        total_weight = sum(nutrition_scoring.NUTRIENT_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001  # Tolérance pour les erreurs de floating point

    def test_nutrient_weights_completeness(self):
        """Test que tous les nutriments ont un poids défini"""
        expected_nutrients = [
            'calories', 'protein', 'total_fat', 'saturated_fat',
            'sugar', 'sodium', 'carbs'
        ]
        
        for nutrient in expected_nutrients:
            assert nutrient in nutrition_scoring.NUTRIENT_WEIGHTS
            assert 0 < nutrition_scoring.NUTRIENT_WEIGHTS[nutrient] <= 1

    def test_ranges_logical_consistency(self):
        """Test la cohérence logique des plages"""
        for nutrient, ranges in nutrition_scoring.HEALTHY_RANGES.items():
            # min_optimal <= max_optimal <= max_acceptable
            assert ranges['min_optimal'] <= ranges['max_optimal']
            assert ranges['max_optimal'] <= ranges['max_acceptable']
            
            # Toutes les valeurs doivent être non-négatives
            assert ranges['min_optimal'] >= 0
            assert ranges['max_optimal'] >= 0
            assert ranges['max_acceptable'] >= 0


class TestEdgeCasesAndErrorHandling:
    """Tests pour les cas limites et la gestion d'erreurs"""

    def test_empty_dataframe(self):
        """Test avec un DataFrame vide"""
        empty_df = pd.DataFrame(columns=['nutrition'])
        result = nutrition_scoring.score_nutrition(empty_df)
        
        assert 'nutrition_score' in result.columns
        assert 'nutrition_grade' in result.columns
        assert 'calories' in result.columns
        assert len(result) == 0

    def test_all_invalid_nutrition_data(self):
        """Test avec toutes les données nutritionnelles invalides"""
        df = pd.DataFrame({
            'nutrition': [
                "invalid1",
                "invalid2",
                None,
                [1, 2, 3],  # Trop court
                "not a list"
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Tous les scores devraient être NaN
        assert all(pd.isna(score) for score in result['nutrition_score'])
        assert all(pd.isna(grade) for grade in result['nutrition_grade'])
        
        # Toutes les calories devraient être 0
        assert all(cal == 0.0 for cal in result['calories'])

    def test_extreme_nutrition_values(self):
        """Test avec des valeurs nutritionnelles extrêmes"""
        df = pd.DataFrame({
            'nutrition': [
                [0, 0, 0, 0, 0, 0, 0],  # Tous zéros
                [10000, 1000, 1000, 10000, 1000, 1000, 1000],  # Très élevés
                [-100, -50, -25, -200, -75, -30, -150]  # Négatifs
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Devrait gérer sans erreur
        assert len(result) == 3
        assert 'nutrition_score' in result.columns
        
        # Les scores devraient être dans la plage valide
        scores = result['nutrition_score'].dropna()
        assert all(10 <= score <= 98 for score in scores)

    def test_unicode_and_special_characters(self):
        """Test avec des caractères Unicode et spéciaux"""
        df = pd.DataFrame({
            'nutrition': [
                "['300', '15', '10', '500', '20', '5', '45']",  # Quotes
                "[300.0, 15.0, 10.0, 500.0, 20.0, 5.0, 45.0]",  # Normal
                "unicode_string_with_éàç",  # Unicode
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Ne devrait pas crash
        assert len(result) == 3
        assert 'nutrition_score' in result.columns


class TestRealWorldScenarios:
    """Tests avec des scénarios du monde réel"""

    def test_kaggle_dataset_simulation(self):
        """Test avec simulation du dataset Kaggle"""
        # Simuler des données réelles du dataset Food.com
        df = pd.DataFrame({
            'name': [
                'Chocolate Chip Cookies',
                'Caesar Salad',
                'Beef Stew',
                'Fruit Smoothie',
                'Pizza Margherita'
            ],
            'nutrition': [
                [412.3, 17.8, 24.1, 346.2, 6.1, 8.9, 58.7],  # Cookies
                [267.5, 22.4, 3.2, 1156.8, 14.2, 4.8, 8.9],  # Salade
                [389.7, 15.3, 1.8, 789.4, 32.6, 6.1, 18.4],  # Ragoût
                [198.2, 0.8, 42.3, 23.1, 4.2, 0.1, 49.8],    # Smoothie
                [276.8, 11.2, 4.7, 567.3, 12.8, 5.4, 33.1]   # Pizza
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Vérifier la cohérence des scores
        assert len(result) == 5
        
        # Le smoothie devrait avoir un bon score (faible en graisses saturées, sodium)
        smoothie_score = result[result['name'] == 'Fruit Smoothie']['nutrition_score'].iloc[0]
        
        # La salade César devrait avoir un score moyen (élevé en sodium)
        caesar_score = result[result['name'] == 'Caesar Salad']['nutrition_score'].iloc[0]
        
        # Les cookies devraient avoir un score plus faible (élevé en sucre, graisses)
        cookies_score = result[result['name'] == 'Chocolate Chip Cookies']['nutrition_score'].iloc[0]
        
        # Vérifications logiques
        assert smoothie_score > cookies_score  # Smoothie plus sain que cookies
        assert all(10 <= score <= 98 for score in result['nutrition_score'])

    def test_restaurant_vs_homemade_comparison(self):
        """Test comparaison restaurant vs fait maison"""
        df = pd.DataFrame({
            'type': ['restaurant', 'homemade', 'restaurant', 'homemade'],
            'nutrition': [
                [850, 45, 15, 1800, 35, 18, 85],  # Restaurant (élevé en tout)
                [320, 12, 8, 420, 22, 4, 38],     # Fait maison (équilibré)
                [720, 38, 22, 1500, 28, 15, 72],  # Restaurant (élevé)
                [280, 10, 5, 350, 18, 3, 32]      # Fait maison (bon)
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Les plats faits maison devraient généralement avoir de meilleurs scores
        restaurant_scores = result[result['type'] == 'restaurant']['nutrition_score']
        homemade_scores = result[result['type'] == 'homemade']['nutrition_score']
        
        assert homemade_scores.mean() > restaurant_scores.mean()

    def test_diet_type_analysis(self):
        """Test d'analyse par type de régime"""
        df = pd.DataFrame({
            'diet_type': ['vegan', 'keto', 'balanced', 'processed'],
            'nutrition': [
                [180, 3, 15, 120, 8, 0.5, 35],    # Vegan (faible gras, pas de gras saturés)
                [520, 45, 2, 350, 32, 20, 8],     # Keto (très gras, peu de glucides)
                [320, 12, 8, 420, 22, 4, 38],     # Équilibré
                [680, 35, 45, 1200, 15, 15, 78]   # Transformé (élevé en tout)
            ]
        })
        
        result = nutrition_scoring.score_nutrition(df)
        
        # Vérifier que les scores reflètent les attentes
        vegan_score = result[result['diet_type'] == 'vegan']['nutrition_score'].iloc[0]
        processed_score = result[result['diet_type'] == 'processed']['nutrition_score'].iloc[0]
        balanced_score = result[result['diet_type'] == 'balanced']['nutrition_score'].iloc[0]
        
        # Le plat équilibré devrait avoir le meilleur score
        assert balanced_score > processed_score
        # Le vegan devrait être bon aussi (faible en graisses saturées)
        assert vegan_score > processed_score


@pytest.fixture
def sample_nutrition_dataframe():
    """Fixture pour DataFrame avec données nutritionnelles variées"""
    return pd.DataFrame({
        'recipe_id': range(1, 11),
        'nutrition': [
            [300, 15, 10, 500, 20, 5, 45],    # Équilibré
            [600, 30, 25, 1000, 40, 15, 80],  # Élevé
            [150, 5, 2, 200, 10, 1, 20],      # Faible
            [800, 40, 35, 1500, 50, 20, 100], # Très élevé
            [200, 8, 5, 300, 15, 3, 25],      # Bon
            [450, 22, 18, 750, 25, 10, 55],   # Moyen-élevé
            [180, 6, 3, 250, 12, 2, 22],      # Bon-faible
            [720, 38, 40, 1300, 35, 18, 90],  # Mauvais
            [250, 10, 6, 380, 18, 4, 30],     # Bon équilibre
            [550, 28, 30, 900, 30, 14, 65]    # Moyen
        ]
    })


class TestComprehensiveIntegration:
    """Tests d'intégration complets"""

    def test_full_scoring_pipeline(self, sample_nutrition_dataframe):
        """Test du pipeline complet de scoring"""
        result = nutrition_scoring.score_nutrition(sample_nutrition_dataframe)
        
        # Vérifier la structure du résultat
        assert len(result) == 10
        expected_columns = ['recipe_id', 'nutrition', 'nutrition_score', 'nutrition_grade', 'calories']
        for col in expected_columns:
            assert col in result.columns
        
        # Vérifier la distribution des grades
        grade_counts = result['nutrition_grade'].value_counts()
        assert len(grade_counts) >= 3  # Au moins 3 grades différents
        
        # Vérifier la cohérence scores/grades
        for _, row in result.iterrows():
            score = row['nutrition_score']
            grade = row['nutrition_grade']
            
            if pd.notna(score):
                expected_grade = nutrition_scoring.assign_grade(score)
                assert grade == expected_grade

    def test_statistical_properties(self, sample_nutrition_dataframe):
        """Test des propriétés statistiques des scores"""
        result = nutrition_scoring.score_nutrition(sample_nutrition_dataframe)
        
        scores = result['nutrition_score'].dropna()
        
        # Distribution des scores
        assert len(scores) > 0
        assert scores.min() >= 10
        assert scores.max() <= 98
        assert scores.std() > 0  # Il devrait y avoir de la variabilité
        
        # Corrélation avec les calories
        calories = result['calories']
        correlation = scores.corr(calories)
        
        # Il devrait y avoir une corrélation (positive ou négative) mais pas parfaite
        assert abs(correlation) < 0.95

    def test_consistency_across_runs(self, sample_nutrition_dataframe):
        """Test de la cohérence entre plusieurs exécutions"""
        result1 = nutrition_scoring.score_nutrition(sample_nutrition_dataframe)
        result2 = nutrition_scoring.score_nutrition(sample_nutrition_dataframe)
        
        # Les résultats devraient être identiques
        pd.testing.assert_series_equal(
            result1['nutrition_score'], 
            result2['nutrition_score']
        )
        pd.testing.assert_series_equal(
            result1['nutrition_grade'], 
            result2['nutrition_grade']
        )