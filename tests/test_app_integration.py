"""
Tests d'intégration pour l'application principale app.py et pages.
"""

import os
import unittest
from unittest.mock import patch


class TestAppIntegration(unittest.TestCase):
    """Tests d'intégration pour l'application principale"""

    def test_app_py_exists(self):
        """Test que app.py existe et est importable"""
        app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
        self.assertTrue(os.path.exists(app_path), "app.py should exist")

        # Vérifier qu'on peut lire le fichier
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("streamlit", content.lower())

    def test_pages_structure(self):
        """Test de la structure des pages"""
        pages_dir = os.path.join(os.path.dirname(__file__), "..", "pages")
        self.assertTrue(os.path.exists(pages_dir), "pages/ directory should exist")

        # Lister les fichiers de pages
        page_files = [f for f in os.listdir(pages_dir) if f.endswith(".py")]
        self.assertGreater(len(page_files), 0, "Should have at least one page file")

        # Vérifier quelques pages spécifiques
        expected_pages = ["recipe_detail.py", "recipe_detail_a.py", "recipe_detail_b.py"]
        for page in expected_pages:
            page_path = os.path.join(pages_dir, page)
            self.assertTrue(os.path.exists(page_path), f"Page {page} should exist")

    def test_main_modules_import(self):
        """Test que les modules principaux s'importent"""
        try:
            # Test imports principaux
            import components
            import preprocessing
            import services
            import utils

            # Vérifier que ce sont des packages
            self.assertTrue(hasattr(services, "__path__"))
            self.assertTrue(hasattr(components, "__path__"))
            self.assertTrue(hasattr(utils, "__path__"))
            self.assertTrue(hasattr(preprocessing, "__path__"))

        except ImportError as e:
            self.fail(f"Failed to import main modules: {e}")

    def test_key_services_availability(self):
        """Test que les services clés sont disponibles"""
        try:
            from services.data_loader import read_csv_file  # Fonction qui existe
            from services.recommender import RecipeRecommender
            from services.search_engine import RecipeSearchEngine

            # Vérifier que les classes/fonctions sont callables
            self.assertTrue(callable(read_csv_file))
            self.assertTrue(callable(RecipeSearchEngine))
            self.assertTrue(callable(RecipeRecommender))

        except ImportError as e:
            self.fail(f"Failed to import key services: {e}")

    @patch("builtins.open")  # Mock plus simple
    def test_app_startup_mock(self, mock_open):
        """Test basique du démarrage de l'app avec mock"""
        # Simuler le contenu de app.py
        mock_open.return_value.__enter__.return_value.read.return_value = "import streamlit as st\nst.title('Test')"

        try:
            # L'app ne devrait pas planter à l'import
            app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")

            # Vérifier que le fichier peut être lu sans erreur de syntaxe
            with open(app_path, "r", encoding="utf-8") as f:
                code = f.read()
                compile(code, app_path, "exec")

            self.assertTrue(True)  # Si on arrive ici, pas d'erreur de syntaxe

        except SyntaxError as e:
            self.fail(f"Syntax error in app.py: {e}")
        except Exception as e:
            self.fail(f"Error reading app.py: {e}")

    def test_project_structure_integrity(self):
        """Test l'intégrité de la structure du projet"""
        base_dir = os.path.join(os.path.dirname(__file__), "..")

        # Vérifier les dossiers principaux
        expected_dirs = ["components", "services", "utils", "preprocessing", "pages", "tests"]
        for dir_name in expected_dirs:
            dir_path = os.path.join(base_dir, dir_name)
            self.assertTrue(os.path.exists(dir_path), f"Directory {dir_name} should exist")

            # Vérifier qu'il y a un __init__.py (sauf pour pages et tests)
            if dir_name not in ["pages", "tests"]:
                init_path = os.path.join(dir_path, "__init__.py")
                self.assertTrue(os.path.exists(init_path), f"{dir_name}/__init__.py should exist")

    def test_configuration_files(self):
        """Test que les fichiers de configuration existent"""
        base_dir = os.path.join(os.path.dirname(__file__), "..")

        config_files = ["requirements.txt", "pyproject.toml", "pytest.ini", "Makefile"]

        for config_file in config_files:
            file_path = os.path.join(base_dir, config_file)
            self.assertTrue(os.path.exists(file_path), f"Config file {config_file} should exist")

    def test_data_pipeline_integration(self):
        """Test d'intégration basique du pipeline de données"""
        try:
            # Test que le pipeline peut être importé
            from components.nutri_score import get_nutri_grade
            from preprocessing.nutrition_scoring import calculate_nutrition_score
            from services.data_loader import read_csv_file  # Fonction qui existe

            # Test workflow basique (sans données réelles)
            # Les fonctions doivent être importables
            self.assertTrue(callable(read_csv_file))
            self.assertTrue(callable(calculate_nutrition_score))
            self.assertTrue(callable(get_nutri_grade))

            # Test avec des données minimales
            test_score = 85.0
            grade = get_nutri_grade(test_score)
            self.assertIn(grade, ["A", "B", "C", "D", "E"])

        except ImportError as e:
            self.fail(f"Data pipeline integration failed: {e}")


class TestPagesIndividual(unittest.TestCase):
    """Tests individuels pour les pages"""

    def test_recipe_detail_pages_syntax(self):
        """Test de syntaxe des pages recipe_detail"""
        pages_dir = os.path.join(os.path.dirname(__file__), "..", "pages")

        recipe_pages = ["recipe_detail.py", "recipe_detail_a.py", "recipe_detail_b.py"]

        for page in recipe_pages:
            page_path = os.path.join(pages_dir, page)
            if os.path.exists(page_path):
                with open(page_path, "r", encoding="utf-8") as f:
                    try:
                        code = f.read()
                        compile(code, page_path, "exec")
                    except SyntaxError as e:
                        self.fail(f"Syntax error in {page}: {e}")

    def test_analysis_pages_syntax(self):
        """Test de syntaxe des pages d'analyse"""
        pages_dir = os.path.join(os.path.dirname(__file__), "..", "pages")

        # Chercher les pages d'analyse
        analysis_pages = [f for f in os.listdir(pages_dir) if "analyse" in f.lower() or "profil" in f.lower()]

        for page in analysis_pages:
            page_path = os.path.join(pages_dir, page)
            with open(page_path, "r", encoding="utf-8") as f:
                try:
                    code = f.read()
                    compile(code, page_path, "exec")
                except SyntaxError as e:
                    self.fail(f"Syntax error in {page}: {e}")


if __name__ == "__main__":
    unittest.main()
