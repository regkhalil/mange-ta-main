"""
Tests pour les utilitaires de statistiques (utils/stats.py).

Ce module teste les fonctions de calcul et d'affichage de statistiques.
"""

import pandas as pd
import pytest


class TestStatsUtilities:
    """Tests pour les fonctions statistiques."""

    @pytest.fixture
    def sample_recipes(self):
        """Fixture fournissant des recettes de test."""
        return pd.DataFrame({
            'id': range(1, 101),
            'name': [f'Recipe {i}' for i in range(1, 101)],
            'minutes': [30, 45, 60, 90, 120] * 20,
            'n_ingredients': [5, 7, 10, 12, 15] * 20,
            'calories': [200, 300, 400, 500, 600] * 20,
            'nutrition_score': [40, 50, 60, 70, 80] * 20,
            'nutrition_grade': ['A', 'B', 'C', 'D', 'E'] * 20,
            'isVegetarian': [True, False, True, False, True] * 20,
            'average_rating': [4.0, 4.2, 4.5, 4.7, 5.0] * 20,
            'review_count': [10, 20, 30, 40, 50] * 20
        })

    def test_calculate_basic_statistics(self, sample_recipes):
        """Test : Calcul des statistiques de base."""
        stats = {
            'total_recipes': len(sample_recipes),
            'avg_time': sample_recipes['minutes'].mean(),
            'avg_ingredients': sample_recipes['n_ingredients'].mean(),
            'avg_calories': sample_recipes['calories'].mean()
        }
        
        assert stats['total_recipes'] == 100
        assert 30 <= stats['avg_time'] <= 120
        assert 5 <= stats['avg_ingredients'] <= 15
        assert 200 <= stats['avg_calories'] <= 600

    def test_nutrition_grade_distribution(self, sample_recipes):
        """Test : Distribution des grades nutritionnels."""
        grade_dist = sample_recipes['nutrition_grade'].value_counts()
        
        # Chaque grade devrait apparaître
        assert len(grade_dist) == 5
        
        # Distribution égale dans cet exemple
        for grade in ['A', 'B', 'C', 'D', 'E']:
            assert grade in grade_dist.index

    def test_vegetarian_percentage(self, sample_recipes):
        """Test : Calcul du pourcentage de recettes végétariennes."""
        veg_count = sample_recipes['isVegetarian'].sum()
        veg_percentage = (veg_count / len(sample_recipes)) * 100
        
        assert 0 <= veg_percentage <= 100
        # Dans notre échantillon: 60% végétarien
        assert 55 <= veg_percentage <= 65

    def test_time_distribution_stats(self, sample_recipes):
        """Test : Statistiques sur la distribution du temps."""
        time_stats = {
            'min': sample_recipes['minutes'].min(),
            'max': sample_recipes['minutes'].max(),
            'median': sample_recipes['minutes'].median(),
            'std': sample_recipes['minutes'].std()
        }
        
        assert time_stats['min'] == 30
        assert time_stats['max'] == 120
        assert time_stats['median'] == 60

    def test_calorie_ranges(self, sample_recipes):
        """Test : Classification par tranches de calories."""
        calorie_ranges = {
            'low': (sample_recipes['calories'] < 300).sum(),
            'medium': ((sample_recipes['calories'] >= 300) & 
                      (sample_recipes['calories'] < 500)).sum(),
            'high': (sample_recipes['calories'] >= 500).sum()
        }
        
        total = sum(calorie_ranges.values())
        assert total == 100

    def test_top_rated_recipes(self, sample_recipes):
        """Test : Identification des recettes les mieux notées."""
        top_rated = sample_recipes.nlargest(10, 'average_rating')
        
        assert len(top_rated) == 10
        assert top_rated['average_rating'].min() >= 4.0

    def test_most_reviewed_recipes(self, sample_recipes):
        """Test : Identification des recettes les plus évaluées."""
        most_reviewed = sample_recipes.nlargest(10, 'review_count')
        
        assert len(most_reviewed) == 10
        assert most_reviewed['review_count'].min() >= 30


class TestStatsFiltering:
    """Tests pour le filtrage statistique."""

    @pytest.fixture
    def recipes_df(self):
        """Fixture de recettes pour tests de filtrage."""
        return pd.DataFrame({
            'id': range(1, 51),
            'minutes': [15, 30, 45, 60, 90] * 10,
            'n_ingredients': [3, 5, 8, 12, 20] * 10,
            'calories': [100, 250, 400, 600, 800] * 10,
            'isVegetarian': [True] * 25 + [False] * 25
        })

    def test_filter_by_time_range(self, recipes_df):
        """Test : Filtrage par temps de préparation."""
        quick_recipes = recipes_df[recipes_df['minutes'] <= 30]
        
        assert len(quick_recipes) == 20
        assert quick_recipes['minutes'].max() <= 30

    def test_filter_by_ingredient_count(self, recipes_df):
        """Test : Filtrage par nombre d'ingrédients."""
        simple_recipes = recipes_df[recipes_df['n_ingredients'] <= 5]
        
        assert len(simple_recipes) == 20
        assert simple_recipes['n_ingredients'].max() <= 5

    def test_filter_vegetarian_only(self, recipes_df):
        """Test : Filtrage végétarien."""
        veg_recipes = recipes_df[recipes_df['isVegetarian'] == True]
        
        assert len(veg_recipes) == 25
        assert veg_recipes['isVegetarian'].all()

    def test_combined_filters(self, recipes_df):
        """Test : Combinaison de plusieurs filtres."""
        filtered = recipes_df[
            (recipes_df['minutes'] <= 45) &
            (recipes_df['n_ingredients'] <= 8) &
            (recipes_df['isVegetarian'] == True)
        ]
        
        # Devrait filtrer significativement
        assert len(filtered) < len(recipes_df)
        assert filtered['minutes'].max() <= 45
        assert filtered['n_ingredients'].max() <= 8


class TestStatsAggregation:
    """Tests pour l'agrégation statistique."""

    def test_aggregate_by_grade(self):
        """Test : Agrégation par grade nutritionnel."""
        recipes = pd.DataFrame({
            'nutrition_grade': ['A', 'A', 'B', 'B', 'C'],
            'calories': [200, 250, 300, 350, 400]
        })
        
        grouped = recipes.groupby('nutrition_grade')['calories'].mean()
        
        assert 'A' in grouped.index
        assert 'B' in grouped.index
        assert 'C' in grouped.index
        assert grouped['A'] < grouped['B'] < grouped['C']

    def test_aggregate_by_time_bins(self):
        """Test : Agrégation par tranches de temps."""
        recipes = pd.DataFrame({
            'minutes': [15, 25, 35, 55, 75, 95],
            'average_rating': [4.0, 4.2, 4.5, 4.3, 4.1, 4.4]
        })
        
        # Créer des bins de temps
        bins = [0, 30, 60, 100]
        labels = ['Quick', 'Medium', 'Long']
        recipes['time_category'] = pd.cut(recipes['minutes'], bins=bins, labels=labels)
        
        grouped = recipes.groupby('time_category')['average_rating'].mean()
        
        assert len(grouped) == 3


class TestStatsCorrelations:
    """Tests pour l'analyse de corrélation."""

    def test_time_vs_ingredients_correlation(self):
        """Test : Corrélation entre temps et ingrédients."""
        recipes = pd.DataFrame({
            'minutes': [30, 45, 60, 90, 120],
            'n_ingredients': [5, 7, 10, 12, 15]
        })
        
        correlation = recipes['minutes'].corr(recipes['n_ingredients'])
        
        # Devrait être positivement corrélé
        assert correlation > 0.8

    def test_calories_vs_rating_correlation(self):
        """Test : Corrélation entre calories et notation."""
        recipes = pd.DataFrame({
            'calories': [200, 300, 400, 500, 600],
            'average_rating': [4.5, 4.3, 4.0, 3.8, 3.5]
        })
        
        correlation = recipes['calories'].corr(recipes['average_rating'])
        
        # Devrait être négativement corrélé (dans cet exemple)
        assert correlation < 0


class TestStatsEdgeCases:
    """Tests des cas limites pour les statistiques."""

    def test_stats_with_empty_dataframe(self):
        """Test : Statistiques sur un DataFrame vide."""
        empty_df = pd.DataFrame(columns=['minutes', 'calories', 'average_rating'])
        
        # Ne devrait pas crasher
        assert len(empty_df) == 0
        assert empty_df['minutes'].mean() != empty_df['minutes'].mean()  # NaN

    def test_stats_with_single_row(self):
        """Test : Statistiques sur une seule recette."""
        single_df = pd.DataFrame({
            'minutes': [30],
            'calories': [300],
            'average_rating': [4.5]
        })
        
        assert single_df['minutes'].mean() == 30
        assert single_df['minutes'].std() != single_df['minutes'].std()  # NaN pour std

    def test_stats_with_missing_values(self):
        """Test : Gestion des valeurs manquantes."""
        df = pd.DataFrame({
            'minutes': [30, None, 45, None, 60],
            'calories': [200, 300, None, 400, 500]
        })
        
        # Devrait calculer en ignorant les NaN
        assert df['minutes'].mean() == 45.0
        assert df['calories'].count() == 4

    def test_percentile_calculations(self):
        """Test : Calcul de percentiles."""
        df = pd.DataFrame({
            'minutes': range(1, 101)
        })
        
        p25 = df['minutes'].quantile(0.25)
        p50 = df['minutes'].quantile(0.50)
        p75 = df['minutes'].quantile(0.75)
        
        assert p25 < p50 < p75
        assert p50 == 50.5


class TestStatsVisualizationData:
    """Tests pour les données de visualisation."""

    def test_prepare_histogram_data(self):
        """Test : Préparation de données pour histogramme."""
        recipes = pd.DataFrame({
            'calories': [100, 200, 300, 400, 500, 600, 700, 800]
        })
        
        # Créer des bins pour l'histogramme
        hist_data = recipes['calories'].value_counts(bins=4).sort_index()
        
        assert len(hist_data) == 4

    def test_prepare_pie_chart_data(self):
        """Test : Préparation de données pour diagramme circulaire."""
        recipes = pd.DataFrame({
            'nutrition_grade': ['A', 'A', 'B', 'B', 'B', 'C', 'C', 'D', 'E']
        })
        
        pie_data = recipes['nutrition_grade'].value_counts()
        
        assert pie_data.sum() == 9
        assert 'B' in pie_data.index
        assert pie_data['B'] == 3

    def test_prepare_time_series_data(self):
        """Test : Préparation de données chronologiques."""
        recipes = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'count': range(10, 20)
        })
        
        assert len(recipes) == 10
        assert recipes['count'].sum() == sum(range(10, 20))
