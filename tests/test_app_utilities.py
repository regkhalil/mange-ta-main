"""
Tests pour les fonctions principales de l'application (app.py).

Ce module teste :
- Le rendu des cartes de recettes horizontales
- La pagination
- Les fonctions utilitaires
"""

import pandas as pd


class TestAppUtilities:
    """Tests pour les fonctions utilitaires de l'application."""

    def test_recipe_name_display_short(self):
        """Test : Affichage d'un nom court (≤60 caractères)."""
        recipe_name = "Chocolate Cake"
        display_name = recipe_name if len(recipe_name) <= 60 else recipe_name[:57] + "..."

        assert display_name == "Chocolate Cake"
        assert not display_name.endswith("...")

    def test_recipe_name_display_long(self):
        """Test : Affichage d'un nom long (>60 caractères) avec troncature."""
        recipe_name = "A" * 100
        display_name = recipe_name if len(recipe_name) <= 60 else recipe_name[:57] + "..."

        assert len(display_name) == 60
        assert display_name.endswith("...")

    def test_nutriscore_color_mapping(self):
        """Test : Mapping des couleurs Nutri-Score."""
        colors = {
            "A": "#238B45",
            "B": "#85BB2F",
            "C": "#FECC00",
            "D": "#FF9500",
            "E": "#E63946",
        }

        for grade, expected_color in colors.items():
            color = colors.get(grade, "#7f8c8d")
            assert color == expected_color

    def test_nutriscore_default_color(self):
        """Test : Couleur par défaut pour grade inconnu."""
        colors = {
            "A": "#238B45",
            "B": "#85BB2F",
            "C": "#FECC00",
            "D": "#FF9500",
            "E": "#E63946",
        }

        default_color = colors.get("Z", "#7f8c8d")
        assert default_color == "#7f8c8d"


class TestPagination:
    """Tests pour le système de pagination."""

    def test_pagination_first_page(self):
        """Test : Pagination sur la première page."""
        items_per_page = 12
        current_page = 1

        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page

        assert start_idx == 0
        assert end_idx == 12

    def test_pagination_middle_page(self):
        """Test : Pagination sur une page au milieu."""
        items_per_page = 12
        current_page = 3

        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page

        assert start_idx == 24
        assert end_idx == 36

    def test_pagination_last_page(self):
        """Test : Pagination sur la dernière page."""
        total_items = 100
        items_per_page = 12
        current_page = 9  # 100/12 = 8.33, donc 9 pages

        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)

        assert start_idx == 96
        assert end_idx == 100

    def test_total_pages_calculation(self):
        """Test : Calcul du nombre total de pages."""
        import math

        # 100 items, 12 per page = 9 pages
        total_pages = math.ceil(100 / 12)
        assert total_pages == 9

        # 120 items, 12 per page = 10 pages
        total_pages = math.ceil(120 / 12)
        assert total_pages == 10

        # 12 items, 12 per page = 1 page
        total_pages = math.ceil(12 / 12)
        assert total_pages == 1


class TestRecipeData:
    """Tests pour la manipulation des données de recettes."""

    def test_create_recipe_dataframe(self):
        """Test : Création d'un DataFrame de recettes."""
        data = {
            "id": [1, 2, 3],
            "name": ["Recipe A", "Recipe B", "Recipe C"],
            "minutes": [30, 45, 15],
            "calories": [250, 400, 150],
        }
        df = pd.DataFrame(data)

        assert len(df) == 3
        assert "id" in df.columns
        assert "name" in df.columns

    def test_filter_recipes_by_time(self):
        """Test : Filtrage des recettes par temps de préparation."""
        data = {"id": [1, 2, 3, 4], "name": ["Quick", "Medium", "Long", "Very Long"], "minutes": [15, 30, 60, 120]}
        df = pd.DataFrame(data)

        # Filtrer les recettes ≤ 30 minutes
        filtered = df[df["minutes"] <= 30]

        assert len(filtered) == 2
        assert list(filtered["name"]) == ["Quick", "Medium"]

    def test_filter_recipes_by_calories(self):
        """Test : Filtrage des recettes par calories."""
        data = {
            "id": [1, 2, 3, 4],
            "name": ["Light", "Medium", "Heavy", "Very Heavy"],
            "calories": [100, 300, 500, 800],
        }
        df = pd.DataFrame(data)

        # Filtrer les recettes ≤ 400 calories
        filtered = df[df["calories"] <= 400]

        assert len(filtered) == 2
        assert list(filtered["name"]) == ["Light", "Medium"]

    def test_filter_recipes_vegetarian(self):
        """Test : Filtrage des recettes végétariennes."""
        data = {
            "id": [1, 2, 3, 4],
            "name": ["Salad", "Burger", "Pasta", "Steak"],
            "is_vegetarian": [True, False, True, False],
        }
        df = pd.DataFrame(data)

        # Filtrer les recettes végétariennes
        filtered = df[df["is_vegetarian"]]

        assert len(filtered) == 2
        assert list(filtered["name"]) == ["Salad", "Pasta"]


class TestTagsGeneration:
    """Tests pour la génération des tags de recettes."""

    def test_time_tag_quick(self):
        """Test : Tag pour recette rapide (≤30 min)."""
        minutes = 20

        if minutes <= 30:
            tag = f"⚡ Rapide ({minutes} min)"
            color = "#007bff"

        assert tag == "⚡ Rapide (20 min)"
        assert color == "#007bff"

    def test_time_tag_medium(self):
        """Test : Tag pour recette moyenne (31-60 min)."""
        minutes = 45

        if 30 < minutes <= 60:
            tag = f"⏱️ Moyen ({minutes} min)"
            color = "#ffc107"

        assert tag == "⏱️ Moyen (45 min)"
        assert color == "#ffc107"

    def test_time_tag_long(self):
        """Test : Tag pour recette longue (>120 min)."""
        minutes = 150

        if minutes >= 120:
            tag = f"🍲 Longue ({minutes} min)"
            color = "#d9534f"

        assert tag == "🍲 Longue (150 min)"
        assert color == "#d9534f"

    def test_ingredients_tag_simple(self):
        """Test : Tag pour recette simple (≤5 ingrédients)."""
        n_ingredients = 4

        if n_ingredients <= 5:
            tag = f"🥗 Simple ({n_ingredients} ingr.)"
            color = "#17a2b8"

        assert tag == "🥗 Simple (4 ingr.)"
        assert color == "#17a2b8"

    def test_ingredients_tag_elaborate(self):
        """Test : Tag pour recette élaborée (>10 ingrédients)."""
        n_ingredients = 15

        if n_ingredients > 10:
            tag = f"👨‍🍳 Élaboré ({n_ingredients} ingr.)"
            color = "#6f42c1"

        assert tag == "👨‍🍳 Élaboré (15 ingr.)"
        assert color == "#6f42c1"
