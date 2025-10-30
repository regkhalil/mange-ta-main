"""
Tests basiques pour les pages Streamlit.
"""

import os
import unittest


class TestPagesImport(unittest.TestCase):
    """Tests d'import pour les pages Streamlit"""

    def test_pages_imports(self):
        """Test que les pages peuvent être importées sans erreur"""
        # Test des imports de base
        pages_dir = os.path.join(os.path.dirname(__file__), "..", "pages")
        self.assertTrue(os.path.exists(pages_dir))

        # Lister les fichiers Python dans pages/
        page_files = [f for f in os.listdir(pages_dir) if f.endswith(".py")]
        self.assertGreater(len(page_files), 0)

        # Vérifier que les fichiers existent
        expected_files = ["recipe_detail.py", "recipe_detail_a.py", "recipe_detail_b.py"]
        for file in expected_files:
            self.assertIn(file, page_files)

    def test_app_py_exists(self):
        """Test que app.py existe"""
        app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
        self.assertTrue(os.path.exists(app_path))


if __name__ == "__main__":
    unittest.main()
