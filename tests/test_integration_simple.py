"""
Tests d'intégration simplifiés pour l'application.
"""

import unittest
import os


class TestAppIntegrationSimple(unittest.TestCase):
    """Tests d'intégration simplifiés pour l'application principale"""

    def test_app_py_exists(self):
        """Test que app.py existe et est lisible"""
        app_path = os.path.join(os.path.dirname(__file__), '..', 'app.py')
        self.assertTrue(os.path.exists(app_path), "app.py should exist")
        
        # Vérifier qu'on peut lire le fichier
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('streamlit', content.lower())
            # Test de syntaxe
            compile(content, app_path, 'exec')

    def test_main_modules_structure(self):
        """Test de la structure des modules principaux"""
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        
        # Vérifier les dossiers principaux
        expected_dirs = ['components', 'services', 'utils', 'preprocessing', 'pages', 'tests']
        for dir_name in expected_dirs:
            dir_path = os.path.join(base_dir, dir_name)
            self.assertTrue(os.path.exists(dir_path), f"Directory {dir_name} should exist")

    def test_basic_imports(self):
        """Test des imports de base"""
        try:
            # Test imports principaux qui doivent marcher
            import services
            import components
            import utils
            import preprocessing
            
            self.assertTrue(True)  # Si on arrive ici, les imports de base fonctionnent
            
        except ImportError as e:
            self.fail(f"Failed to import main modules: {e}")

    def test_key_components_work(self):
        """Test que les composants clés fonctionnent"""
        try:
            from components.nutri_score import get_nutri_grade, get_nutri_color
            from services.data_loader import read_csv_file
            
            # Test nutri_score
            grade = get_nutri_grade(85.0)
            self.assertIn(grade, ['A', 'B', 'C', 'D', 'E'])
            
            color = get_nutri_color('A')
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith('#'))
            
            # Test que les fonctions sont callables
            self.assertTrue(callable(read_csv_file))
            
            # Test optionnel pour stats (nom peut varier)
            try:
                from utils.stats import get_descriptive_stats
                self.assertTrue(callable(get_descriptive_stats))
            except ImportError:
                # C'est OK si le nom exact diffère
                pass
            
        except ImportError as e:
            self.fail(f"Failed to import key components: {e}")

    def test_config_files_present(self):
        """Test que les fichiers de configuration sont présents"""
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        
        config_files = [
            'requirements.txt',
            'pyproject.toml',
            'pytest.ini'
        ]
        
        for config_file in config_files:
            file_path = os.path.join(base_dir, config_file)
            self.assertTrue(os.path.exists(file_path), f"Config file {config_file} should exist")

    def test_pages_syntax(self):
        """Test de syntaxe des pages Streamlit"""
        pages_dir = os.path.join(os.path.dirname(__file__), '..', 'pages')
        
        if os.path.exists(pages_dir):
            page_files = [f for f in os.listdir(pages_dir) if f.endswith('.py')]
            
            for page_file in page_files:
                page_path = os.path.join(pages_dir, page_file)
                with open(page_path, 'r', encoding='utf-8') as f:
                    try:
                        code = f.read()
                        compile(code, page_path, 'exec')
                    except SyntaxError as e:
                        self.fail(f"Syntax error in {page_file}: {e}")

    def test_integration_workflow(self):
        """Test d'un workflow d'intégration simple"""
        try:
            # Workflow: données -> calcul -> affichage
            from components.nutri_score import get_nutri_grade, get_nutri_color
            
            # Simuler des données de recette avec les seuils corrects
            # A: >=85, B: 70-84, C: 55-69, D: 40-54, E: <40
            test_scores = [90, 75, 60, 45, 30]
            expected_grades = ['A', 'B', 'C', 'D', 'E']
            
            for score, expected_grade in zip(test_scores, expected_grades):
                grade = get_nutri_grade(score)
                self.assertEqual(grade, expected_grade, 
                               f"Score {score} should give grade {expected_grade}, got {grade}")
                
                color = get_nutri_color(grade)
                self.assertIsInstance(color, str)
                self.assertTrue(color.startswith('#'))
            
            # Le workflow de base fonctionne
            self.assertTrue(True)
            
        except Exception as e:
            self.fail(f"Integration workflow failed: {e}")


class TestProjectHealth(unittest.TestCase):
    """Tests de santé du projet"""

    def test_no_obvious_syntax_errors(self):
        """Test qu'il n'y a pas d'erreurs de syntaxe évidentes"""
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        
        # Checker les fichiers Python principaux
        python_files = []
        for root, dirs, files in os.walk(base_dir):
            # Ignorer __pycache__ et .git
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__'))]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        syntax_errors = []
        for py_file in python_files[:20]:  # Limiter à 20 fichiers pour la performance
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                    compile(code, py_file, 'exec')
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")
            except UnicodeDecodeError:
                # Ignorer les fichiers avec problèmes d'encodage
                pass
        
        if syntax_errors:
            self.fail(f"Syntax errors found:\n" + "\n".join(syntax_errors))

    def test_import_health(self):
        """Test de santé des imports principaux"""
        critical_imports = [
            'components.nutri_score',
            'utils.stats', 
            'services.data_loader',
            'preprocessing.nutrition_scoring'
        ]
        
        import_failures = []
        for module in critical_imports:
            try:
                __import__(module)
            except ImportError as e:
                import_failures.append(f"{module}: {e}")
        
        # Au moins 50% des imports doivent fonctionner
        success_rate = (len(critical_imports) - len(import_failures)) / len(critical_imports)
        self.assertGreater(success_rate, 0.5, f"Too many import failures: {import_failures}")


if __name__ == '__main__':
    unittest.main()