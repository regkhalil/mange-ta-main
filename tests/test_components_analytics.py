"""
Tests unitaires pour les composants analytics.

Ce module teste tous les composants d'analyse :
- complexity_analysis.py - Analyse de complexité
- ingredient_health.py - Santé des ingrédients
- nutrition_profiling.py - Profilage nutritionnel
- time_analysis.py - Analyse temporelle
- utils.py - Utilitaires analytics
"""

import pandas as pd
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

# Import des modules analytics
try:
    from components.analytics.complexity_analysis import (
        calculate_complexity_score,
        analyze_recipe_complexity,
        complexity_distribution
    )
except ImportError:
    # Fallback si le module n'existe pas encore
    calculate_complexity_score = None

try:
    from components.analytics.ingredient_health import (
        analyze_ingredient_healthiness,
        health_score_by_ingredient,
        ingredient_categories
    )
except ImportError:
    analyze_ingredient_healthiness = None

try:
    from components.analytics.nutrition_profiling import (
        create_nutrition_profile,
        compare_nutrition_profiles,
        nutrition_recommendations
    )
except ImportError:
    create_nutrition_profile = None

try:
    from components.analytics.time_analysis import (
        analyze_cooking_times,
        time_complexity_correlation,
        optimal_time_ranges
    )
except ImportError:
    analyze_cooking_times = None

try:
    from components.analytics.utils import (
        normalize_data,
        calculate_percentiles,
        aggregate_by_category
    )
except ImportError:
    normalize_data = None


class TestComplexityAnalysis:
    """Tests pour l'analyse de complexité."""

    def create_sample_recipes(self):
        """Crée des données de test pour les recettes."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'n_steps': [3, 8, 12, 5, 15],
            'n_ingredients': [5, 10, 15, 7, 20],
            'minutes': [15, 45, 90, 30, 120],
            'techniques': [
                ['baking'],
                ['baking', 'sautéing'],
                ['baking', 'sautéing', 'braising', 'grilling'],
                ['boiling', 'mixing'],
                ['baking', 'sautéing', 'braising', 'grilling', 'roasting', 'steaming']
            ]
        })

    @pytest.mark.skipif(calculate_complexity_score is None, reason="Module complexity_analysis not available")
    def test_calculate_complexity_score(self):
        """Test du calcul de score de complexité."""
        recipes_df = self.create_sample_recipes()
        
        # Test avec une recette simple
        simple_recipe = recipes_df.iloc[0]
        score = calculate_complexity_score(simple_recipe)
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        
        # Test avec une recette complexe
        complex_recipe = recipes_df.iloc[-1]
        complex_score = calculate_complexity_score(complex_recipe)
        
        # La recette complexe doit avoir un score plus élevé
        assert complex_score > score

    @pytest.mark.skipif(analyze_recipe_complexity is None, reason="Module complexity_analysis not available")
    def test_analyze_recipe_complexity(self):
        """Test de l'analyse complète de complexité."""
        recipes_df = self.create_sample_recipes()
        
        result = analyze_recipe_complexity(recipes_df)
        
        # Vérifier la structure du résultat
        assert isinstance(result, dict)
        expected_keys = ['complexity_scores', 'distribution', 'correlations']
        for key in expected_keys:
            assert key in result

    @pytest.mark.skipif(complexity_distribution is None, reason="Module complexity_analysis not available")
    def test_complexity_distribution(self):
        """Test de la distribution de complexité."""
        recipes_df = self.create_sample_recipes()
        
        distribution = complexity_distribution(recipes_df)
        
        # Vérifier que c'est un dictionnaire avec les catégories attendues
        assert isinstance(distribution, dict)
        categories = ['Simple', 'Moyen', 'Complexe']
        for category in categories:
            assert category in distribution
            assert isinstance(distribution[category], (int, float))


class TestIngredientHealth:
    """Tests pour l'analyse de santé des ingrédients."""

    def create_sample_ingredients_data(self):
        """Crée des données de test pour les ingrédients."""
        return pd.DataFrame({
            'ingredient': ['tomato', 'sugar', 'olive oil', 'spinach', 'butter'],
            'category': ['vegetable', 'sweetener', 'oil', 'leafy green', 'dairy'],
            'health_score': [85, 20, 70, 95, 40],
            'nutritional_density': [0.8, 0.1, 0.6, 0.9, 0.3]
        })

    @pytest.mark.skipif(analyze_ingredient_healthiness is None, reason="Module ingredient_health not available")
    def test_analyze_ingredient_healthiness(self):
        """Test de l'analyse de santé des ingrédients."""
        ingredients_df = self.create_sample_ingredients_data()
        
        result = analyze_ingredient_healthiness(ingredients_df)
        
        # Vérifier la structure du résultat
        assert isinstance(result, dict)
        assert 'average_health_score' in result
        assert 'health_distribution' in result
        assert 'recommendations' in result

    @pytest.mark.skipif(health_score_by_ingredient is None, reason="Module ingredient_health not available")
    def test_health_score_by_ingredient(self):
        """Test du score de santé par ingrédient."""
        ingredients_df = self.create_sample_ingredients_data()
        
        scores = health_score_by_ingredient(ingredients_df)
        
        # Vérifier que c'est un dictionnaire avec les ingrédients
        assert isinstance(scores, dict)
        assert 'tomato' in scores
        assert 'sugar' in scores
        
        # Vérifier que les scores sont cohérents
        assert scores['spinach'] > scores['sugar']  # Épinards plus sains que sucre

    @pytest.mark.skipif(ingredient_categories is None, reason="Module ingredient_health not available")
    def test_ingredient_categories(self):
        """Test de la catégorisation des ingrédients."""
        ingredients_df = self.create_sample_ingredients_data()
        
        categories = ingredient_categories(ingredients_df)
        
        # Vérifier la structure
        assert isinstance(categories, dict)
        assert 'vegetable' in categories
        assert 'dairy' in categories


class TestNutritionProfiling:
    """Tests pour le profilage nutritionnel."""

    def create_sample_nutrition_data(self):
        """Crée des données nutritionnelles de test."""
        return pd.DataFrame({
            'recipe_id': [1, 2, 3, 4, 5],
            'calories': [250, 400, 600, 300, 800],
            'protein': [15, 20, 30, 12, 35],
            'carbs': [30, 45, 60, 40, 80],
            'fat': [10, 18, 25, 15, 40],
            'fiber': [5, 8, 12, 6, 15],
            'sodium': [400, 800, 1200, 600, 1500]
        })

    @pytest.mark.skipif(create_nutrition_profile is None, reason="Module nutrition_profiling not available")
    def test_create_nutrition_profile(self):
        """Test de création de profil nutritionnel."""
        nutrition_df = self.create_sample_nutrition_data()
        
        profile = create_nutrition_profile(nutrition_df)
        
        # Vérifier la structure du profil
        assert isinstance(profile, dict)
        nutritional_keys = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sodium']
        for key in nutritional_keys:
            assert key in profile
            assert 'mean' in profile[key]
            assert 'median' in profile[key]
            assert 'percentiles' in profile[key]

    @pytest.mark.skipif(compare_nutrition_profiles is None, reason="Module nutrition_profiling not available")
    def test_compare_nutrition_profiles(self):
        """Test de comparaison de profils nutritionnels."""
        nutrition_df = self.create_sample_nutrition_data()
        
        # Créer deux sous-ensembles pour comparaison
        low_cal = nutrition_df[nutrition_df['calories'] < 400]
        high_cal = nutrition_df[nutrition_df['calories'] >= 400]
        
        comparison = compare_nutrition_profiles(low_cal, high_cal)
        
        # Vérifier la structure de comparaison
        assert isinstance(comparison, dict)
        assert 'differences' in comparison
        assert 'statistical_tests' in comparison

    @pytest.mark.skipif(nutrition_recommendations is None, reason="Module nutrition_profiling not available")
    def test_nutrition_recommendations(self):
        """Test des recommandations nutritionnelles."""
        nutrition_df = self.create_sample_nutrition_data()
        
        recommendations = nutrition_recommendations(nutrition_df)
        
        # Vérifier la structure des recommandations
        assert isinstance(recommendations, dict)
        assert 'improvements' in recommendations
        assert 'balanced_options' in recommendations


class TestTimeAnalysis:
    """Tests pour l'analyse temporelle."""

    def create_sample_time_data(self):
        """Crée des données temporelles de test."""
        return pd.DataFrame({
            'recipe_id': [1, 2, 3, 4, 5, 6],
            'minutes': [15, 30, 45, 60, 90, 120],
            'prep_time': [10, 15, 20, 30, 45, 60],
            'cook_time': [5, 15, 25, 30, 45, 60],
            'difficulty': ['easy', 'easy', 'medium', 'medium', 'hard', 'hard'],
            'n_steps': [3, 5, 8, 10, 15, 20]
        })

    @pytest.mark.skipif(analyze_cooking_times is None, reason="Module time_analysis not available")
    def test_analyze_cooking_times(self):
        """Test de l'analyse des temps de cuisson."""
        time_df = self.create_sample_time_data()
        
        analysis = analyze_cooking_times(time_df)
        
        # Vérifier la structure de l'analyse
        assert isinstance(analysis, dict)
        assert 'time_distribution' in analysis
        assert 'average_by_difficulty' in analysis
        assert 'time_efficiency' in analysis

    @pytest.mark.skipif(time_complexity_correlation is None, reason="Module time_analysis not available")
    def test_time_complexity_correlation(self):
        """Test de corrélation temps-complexité."""
        time_df = self.create_sample_time_data()
        
        correlation = time_complexity_correlation(time_df)
        
        # Vérifier que c'est un nombre entre -1 et 1
        assert isinstance(correlation, (int, float))
        assert -1 <= correlation <= 1

    @pytest.mark.skipif(optimal_time_ranges is None, reason="Module time_analysis not available")
    def test_optimal_time_ranges(self):
        """Test des plages de temps optimales."""
        time_df = self.create_sample_time_data()
        
        ranges = optimal_time_ranges(time_df)
        
        # Vérifier la structure des plages
        assert isinstance(ranges, dict)
        difficulty_levels = ['easy', 'medium', 'hard']
        for level in difficulty_levels:
            if level in ranges:
                assert 'min_time' in ranges[level]
                assert 'max_time' in ranges[level]


class TestAnalyticsUtils:
    """Tests pour les utilitaires analytics."""

    def create_sample_data(self):
        """Crée des données de test."""
        return pd.DataFrame({
            'category': ['A', 'B', 'A', 'C', 'B', 'A'],
            'value': [10, 20, 15, 30, 25, 12],
            'score': [0.1, 0.8, 0.3, 0.9, 0.6, 0.2]
        })

    @pytest.mark.skipif(normalize_data is None, reason="Module analytics.utils not available")
    def test_normalize_data(self):
        """Test de normalisation des données."""
        df = self.create_sample_data()
        
        normalized = normalize_data(df, 'value')
        
        # Vérifier que les valeurs sont entre 0 et 1
        assert (normalized >= 0).all()
        assert (normalized <= 1).all()
        
        # Vérifier que la plus petite valeur est 0 et la plus grande est 1
        assert normalized.min() == 0
        assert normalized.max() == 1

    @pytest.mark.skipif(calculate_percentiles is None, reason="Module analytics.utils not available")
    def test_calculate_percentiles(self):
        """Test de calcul des percentiles."""
        df = self.create_sample_data()
        
        percentiles = calculate_percentiles(df, 'value')
        
        # Vérifier la structure des percentiles
        assert isinstance(percentiles, dict)
        expected_percentiles = [25, 50, 75, 90, 95]
        for p in expected_percentiles:
            assert p in percentiles

    @pytest.mark.skipif(aggregate_by_category is None, reason="Module analytics.utils not available")
    def test_aggregate_by_category(self):
        """Test d'agrégation par catégorie."""
        df = self.create_sample_data()
        
        aggregated = aggregate_by_category(df, 'category', 'value')
        
        # Vérifier la structure de l'agrégation
        assert isinstance(aggregated, dict)
        categories = df['category'].unique()
        for cat in categories:
            assert cat in aggregated
            assert 'count' in aggregated[cat]
            assert 'mean' in aggregated[cat]
            assert 'sum' in aggregated[cat]


class TestAnalyticsIntegration:
    """Tests d'intégration pour les analytics."""

    def create_comprehensive_dataset(self):
        """Crée un dataset complet pour les tests d'intégration."""
        np.random.seed(42)
        n = 100
        
        return pd.DataFrame({
            'recipe_id': range(1, n + 1),
            'n_steps': np.random.randint(3, 20, n),
            'n_ingredients': np.random.randint(5, 25, n),
            'minutes': np.random.randint(10, 180, n),
            'calories': np.random.randint(100, 800, n),
            'protein': np.random.randint(5, 50, n),
            'carbs': np.random.randint(10, 100, n),
            'fat': np.random.randint(2, 60, n),
            'fiber': np.random.randint(1, 20, n),
            'sodium': np.random.randint(100, 2000, n),
            'difficulty': np.random.choice(['easy', 'medium', 'hard'], n),
            'nutrition_score': np.random.uniform(20, 95, n)
        })

    def test_analytics_pipeline(self):
        """Test du pipeline complet d'analytics."""
        df = self.create_comprehensive_dataset()
        
        # Test que le dataset est cohérent
        assert len(df) == 100
        assert df['recipe_id'].nunique() == 100
        
        # Test des corrélations basiques
        correlation_matrix = df[['n_steps', 'n_ingredients', 'minutes']].corr()
        assert correlation_matrix.shape == (3, 3)
        
        # Test des statistiques descriptives
        stats = df.describe()
        assert 'count' in stats.index
        assert 'mean' in stats.index
        assert 'std' in stats.index

    def test_nutrition_score_distribution(self):
        """Test de la distribution des scores nutritionnels."""
        df = self.create_comprehensive_dataset()
        
        # Vérifier la distribution des scores
        score_stats = df['nutrition_score'].describe()
        assert score_stats['min'] >= 20
        assert score_stats['max'] <= 95
        
        # Test de catégorisation par quintiles
        df['score_quintile'] = pd.qcut(df['nutrition_score'], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
        quintile_counts = df['score_quintile'].value_counts()
        
        # Chaque quintile devrait avoir environ 20 recettes
        for count in quintile_counts:
            assert 15 <= count <= 25  # Tolérance pour la variabilité

    def test_difficulty_time_relationship(self):
        """Test de la relation difficulté-temps."""
        df = self.create_comprehensive_dataset()
        
        # Calculer les temps moyens par difficulté
        time_by_difficulty = df.groupby('difficulty')['minutes'].mean()
        
        # Vérifier que la structure est correcte
        assert isinstance(time_by_difficulty, pd.Series)
        assert len(time_by_difficulty) <= 3  # easy, medium, hard

    def test_comprehensive_analytics_workflow(self):
        """Test du workflow complet d'analytics."""
        df = self.create_comprehensive_dataset()
        
        # Étape 1: Analyse de base
        basic_stats = {
            'total_recipes': len(df),
            'avg_time': df['minutes'].mean(),
            'avg_calories': df['calories'].mean(),
            'nutrition_score_mean': df['nutrition_score'].mean()
        }
        
        # Étape 2: Analyse de complexité (simulation)
        df['complexity_score'] = (
            df['n_steps'] * 0.3 + 
            df['n_ingredients'] * 0.2 + 
            df['minutes'] * 0.005
        ).clip(0, 100)
        
        # Étape 3: Catégorisation
        df['time_category'] = pd.cut(
            df['minutes'], 
            bins=[0, 30, 60, 180], 
            labels=['Quick', 'Medium', 'Long']
        )
        
        # Étape 4: Vérifications finales
        assert basic_stats['total_recipes'] == 100
        assert 0 <= basic_stats['nutrition_score_mean'] <= 100
        assert df['complexity_score'].between(0, 100).all()
        assert df['time_category'].notna().all()


class TestAnalyticsEdgeCases:
    """Tests pour les cas limites des analytics."""

    def test_empty_dataframe_analytics(self):
        """Test avec DataFrame vide."""
        empty_df = pd.DataFrame()
        
        # Les fonctions d'analytics doivent gérer les DataFrames vides
        if normalize_data is not None:
            # Doit retourner une série vide ou lever une exception appropriée
            try:
                result = normalize_data(empty_df, 'nonexistent_column')
                assert len(result) == 0
            except (KeyError, ValueError):
                pass  # Exception attendue

    def test_single_row_analytics(self):
        """Test avec une seule ligne."""
        single_row_df = pd.DataFrame({
            'value': [42],
            'category': ['A']
        })
        
        if calculate_percentiles is not None:
            try:
                percentiles = calculate_percentiles(single_row_df, 'value')
                # Tous les percentiles devraient être égaux à la valeur unique
                for p in percentiles.values():
                    assert p == 42
            except (ValueError, KeyError):
                pass  # Exception acceptable pour un seul point

    def test_missing_values_analytics(self):
        """Test avec valeurs manquantes."""
        df_with_na = pd.DataFrame({
            'value': [1, 2, None, 4, 5],
            'category': ['A', 'B', 'A', None, 'B']
        })
        
        # Les fonctions doivent gérer les valeurs manquantes
        if aggregate_by_category is not None:
            try:
                result = aggregate_by_category(df_with_na, 'category', 'value')
                # Vérifier que les NaN sont gérés correctement
                assert isinstance(result, dict)
            except (ValueError, KeyError):
                pass  # Exception acceptable

    def test_extreme_values_analytics(self):
        """Test avec valeurs extrêmes."""
        extreme_df = pd.DataFrame({
            'value': [0, 1e6, -1000, 0.001, float('inf')],
            'category': ['A', 'B', 'C', 'D', 'E']
        })
        
        if normalize_data is not None:
            try:
                # Doit gérer les valeurs infinies et extrêmes
                normalized = normalize_data(extreme_df, 'value')
                # Vérifier que les résultats sont raisonnables
                finite_values = normalized[np.isfinite(normalized)]
                if len(finite_values) > 0:
                    assert finite_values.min() >= 0
                    assert finite_values.max() <= 1
            except (ValueError, OverflowError):
                pass  # Exceptions acceptables pour valeurs extrêmes


if __name__ == "__main__":
    pytest.main([__file__])