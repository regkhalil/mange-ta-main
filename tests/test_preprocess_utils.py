"""
Tests unitaires pour le module preprocess_utils.py

Ce module teste toutes les fonctions utilitaires de preprocessing :
- load_recipe_data : chargement des données avec gestion d'erreurs
- setup_logging : configuration du système de logging
"""

import logging
import os
import tempfile
import unittest.mock
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Configuration du path pour les imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing import preprocess_utils


class TestLoadRecipeData:
    """Tests pour la fonction load_recipe_data"""

    def test_load_existing_file(self, tmp_path):
        """Test le chargement d'un fichier existant"""
        # Créer un fichier CSV de test
        test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Recipe 1', 'Recipe 2', 'Recipe 3'],
            'ingredients': [['salt', 'pepper'], ['flour', 'sugar'], ['tomato', 'basil']]
        })
        test_file = tmp_path / "test_recipes.csv"
        test_data.to_csv(test_file, index=False)
        
        # Tester le chargement
        result = preprocess_utils.load_recipe_data(str(test_file), str(tmp_path))
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'id' in result.columns
        assert 'name' in result.columns
        pd.testing.assert_frame_equal(result, test_data)

    def test_load_nonexistent_file_with_download_failure(self, tmp_path):
        """Test le comportement quand le fichier n'existe pas et le téléchargement échoue"""
        nonexistent_file = tmp_path / "nonexistent.csv"
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'curl', stderr='Download failed')
            
            with pytest.raises(subprocess.CalledProcessError):
                preprocess_utils.load_recipe_data(str(nonexistent_file), str(tmp_path))

    @patch('subprocess.run')
    @patch('zipfile.ZipFile')
    @patch('os.remove')
    def test_load_nonexistent_file_with_successful_download(self, mock_remove, mock_zipfile, mock_run, tmp_path):
        """Test le téléchargement réussi quand le fichier n'existe pas"""
        nonexistent_file = tmp_path / "RAW_recipes.csv"
        
        # Mock successful download
        mock_run.return_value = Mock()
        
        # Mock ZipFile extraction
        mock_zip_instance = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
        
        # Créer le fichier après "extraction"
        def create_file_after_extract(*args, **kwargs):
            test_data = pd.DataFrame({
                'id': [1, 2],
                'name': ['Downloaded Recipe 1', 'Downloaded Recipe 2']
            })
            test_data.to_csv(nonexistent_file, index=False)
        
        mock_zip_instance.extractall.side_effect = create_file_after_extract
        
        # Tester
        result = preprocess_utils.load_recipe_data(str(nonexistent_file), str(tmp_path))
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert mock_run.called
        assert mock_zipfile.called
        assert mock_remove.called

    def test_load_empty_file(self, tmp_path):
        """Test le chargement d'un fichier vide"""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("id,name,ingredients\n")  # Fichier avec headers seulement
        
        result = preprocess_utils.load_recipe_data(str(empty_file), str(tmp_path))
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ['id', 'name', 'ingredients']

    def test_load_malformed_csv(self, tmp_path):
        """Test le chargement d'un fichier CSV mal formé"""
        malformed_file = tmp_path / "malformed.csv"
        malformed_file.write_text("id,name\n1,Recipe 1,extra_column\n2")  # CSV mal formé
        
        # Pandas peut gérer certains CSV mal formés, testons que ça ne crash pas
        result = preprocess_utils.load_recipe_data(str(malformed_file), str(tmp_path))
        assert isinstance(result, pd.DataFrame)

    @patch('logging.getLogger')
    def test_logging_calls(self, mock_get_logger, tmp_path):
        """Test que les bonnes informations de logging sont appelées"""
        # Créer un fichier de test
        test_data = pd.DataFrame({'id': [1], 'name': ['Test Recipe']})
        test_file = tmp_path / "test.csv"
        test_data.to_csv(test_file, index=False)
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        preprocess_utils.load_recipe_data(str(test_file), str(tmp_path))
        
        # Vérifier que le logger a été appelé
        assert mock_logger.info.called
        
        # Vérifier le contenu des messages de log
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Loading existing file" in call for call in log_calls)
        assert any("Loaded 1 recipes" in call for call in log_calls)


class TestSetupLogging:
    """Tests pour la fonction setup_logging"""

    def test_setup_logging_creates_directory(self, tmp_path):
        """Test que setup_logging crée le répertoire de logs"""
        logs_dir = tmp_path / "test_logs"
        assert not logs_dir.exists()
        
        preprocess_utils.setup_logging(str(logs_dir))
        
        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_setup_logging_creates_log_file(self, tmp_path):
        """Test que setup_logging crée un fichier de log"""
        logs_dir = tmp_path / "test_logs"
        
        preprocess_utils.setup_logging(str(logs_dir))
        
        # Vérifier qu'un fichier de log a été créé
        log_files = list(logs_dir.glob("preprocessing_*.log"))
        assert len(log_files) == 1
        
        log_file = log_files[0]
        assert log_file.name.startswith("preprocessing_")
        assert log_file.name.endswith(".log")

    def test_setup_logging_configures_level(self, tmp_path):
        """Test que setup_logging configure le niveau de logging"""
        logs_dir = tmp_path / "test_logs"
        
        preprocess_utils.setup_logging(str(logs_dir))
        
        # Vérifier que le niveau de logging est INFO
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_logging_with_existing_directory(self, tmp_path):
        """Test setup_logging avec un répertoire existant"""
        logs_dir = tmp_path / "existing_logs"
        logs_dir.mkdir()
        
        # Créer un fichier existant
        existing_file = logs_dir / "existing.log"
        existing_file.write_text("existing content")
        
        preprocess_utils.setup_logging(str(logs_dir))
        
        # Vérifier que le répertoire existe toujours
        assert logs_dir.exists()
        # Vérifier que le fichier existant n'a pas été supprimé
        assert existing_file.exists()
        # Vérifier qu'un nouveau fichier de log a été créé
        log_files = list(logs_dir.glob("preprocessing_*.log"))
        assert len(log_files) >= 1

    @patch('logging.basicConfig')
    def test_setup_logging_configuration_parameters(self, mock_basic_config, tmp_path):
        """Test que setup_logging appelle basicConfig avec les bons paramètres"""
        logs_dir = tmp_path / "test_logs"
        
        preprocess_utils.setup_logging(str(logs_dir))
        
        # Vérifier que basicConfig a été appelé
        assert mock_basic_config.called
        
        # Récupérer les arguments passés à basicConfig
        call_args = mock_basic_config.call_args
        kwargs = call_args.kwargs
        
        assert kwargs['level'] == logging.INFO
        assert 'format' in kwargs
        assert 'handlers' in kwargs
        
        # Vérifier le format
        expected_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert kwargs['format'] == expected_format

    def test_setup_logging_filename_format(self, tmp_path):
        """Test que le nom du fichier de log suit le bon format"""
        logs_dir = tmp_path / "test_logs"
        
        preprocess_utils.setup_logging(str(logs_dir))
        
        log_files = list(logs_dir.glob("preprocessing_*.log"))
        assert len(log_files) == 1
        
        log_filename = log_files[0].name
        # Format: preprocessing_YYYYMMDD_HHMMSS.log
        import re
        pattern = r'preprocessing_\d{8}_\d{6}\.log'
        assert re.match(pattern, log_filename)

    def test_setup_logging_with_special_characters_in_path(self, tmp_path):
        """Test setup_logging avec des caractères spéciaux dans le chemin"""
        logs_dir = tmp_path / "logs with spaces & special-chars"
        
        preprocess_utils.setup_logging(str(logs_dir))
        
        assert logs_dir.exists()
        log_files = list(logs_dir.glob("preprocessing_*.log"))
        assert len(log_files) == 1


class TestIntegration:
    """Tests d'intégration pour les fonctions de preprocess_utils"""

    def test_logging_after_setup(self, tmp_path):
        """Test que le logging fonctionne après setup_logging"""
        logs_dir = tmp_path / "integration_logs"
        
        # Setup logging
        preprocess_utils.setup_logging(str(logs_dir))
        
        # Obtenir le logger du module
        logger = logging.getLogger('preprocessing.preprocess_utils')
        test_message = "Test integration message"
        logger.info(test_message)
        
        # Vérifier que le message a été écrit dans le fichier
        log_files = list(logs_dir.glob("preprocessing_*.log"))
        assert len(log_files) == 1
        
        log_content = log_files[0].read_text()
        assert test_message in log_content

    def test_load_recipe_data_with_logging(self, tmp_path):
        """Test d'intégration: load_recipe_data avec logging activé"""
        logs_dir = tmp_path / "integration_logs"
        preprocess_utils.setup_logging(str(logs_dir))
        
        # Créer des données de test
        test_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Recipe A', 'Recipe B', 'Recipe C', 'Recipe D', 'Recipe E'],
            'nutrition': [[100, 10, 5, 200, 15, 3, 30], [200, 15, 8, 300, 20, 5, 45]]
        })
        test_file = tmp_path / "integration_test.csv"
        test_data.to_csv(test_file, index=False)
        
        # Charger les données
        result = preprocess_utils.load_recipe_data(str(test_file), str(tmp_path))
        
        # Vérifier les données
        assert len(result) == 5
        
        # Vérifier que les logs contiennent les bonnes informations
        log_files = list(logs_dir.glob("preprocessing_*.log"))
        log_content = log_files[0].read_text()
        assert "Loading existing file" in log_content
        assert "Loaded 5 recipes" in log_content


# Ajout d'import manquant
import subprocess


@pytest.fixture
def sample_recipe_data():
    """Fixture pour des données de recettes d'exemple"""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Pasta Carbonara', 'Chocolate Cake', 'Green Salad'],
        'minutes': [30, 60, 10],
        'tags': [['italian', 'pasta'], ['dessert', 'chocolate'], ['healthy', 'vegetarian']],
        'nutrition': [
            [350, 12, 5, 800, 25, 8, 45],
            [450, 18, 35, 300, 8, 12, 65],
            [120, 8, 3, 150, 5, 1, 15]
        ],
        'n_steps': [5, 8, 3],
        'n_ingredients': [6, 10, 5]
    })


class TestEdgeCases:
    """Tests pour les cas limites et la gestion d'erreurs"""

    def test_load_recipe_data_with_permission_error(self, tmp_path):
        """Test le comportement avec une erreur de permission"""
        if os.name == 'nt':  # Windows
            pytest.skip("Test de permission non applicable sur Windows")
        
        protected_file = tmp_path / "protected.csv"
        protected_file.write_text("id,name\n1,test")
        protected_file.chmod(0o000)  # Aucune permission
        
        try:
            with pytest.raises(PermissionError):
                preprocess_utils.load_recipe_data(str(protected_file), str(tmp_path))
        finally:
            # Restaurer les permissions pour le nettoyage
            protected_file.chmod(0o644)

    def test_setup_logging_with_readonly_directory(self, tmp_path):
        """Test setup_logging avec un répertoire en lecture seule"""
        if os.name == 'nt':  # Windows
            pytest.skip("Test de permission non applicable sur Windows")
        
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Lecture seule
        
        try:
            with pytest.raises(PermissionError):
                preprocess_utils.setup_logging(str(readonly_dir))
        finally:
            # Restaurer les permissions pour le nettoyage
            readonly_dir.chmod(0o755)

    def test_load_recipe_data_with_unicode_content(self, tmp_path):
        """Test le chargement avec du contenu Unicode"""
        unicode_data = pd.DataFrame({
            'id': [1, 2],
            'name': ['Crème Brûlée', 'Ratatouille Niçoise'],
            'description': ['Un dessert français classique', 'Plat végétarien de Nice']
        })
        unicode_file = tmp_path / "unicode_recipes.csv"
        unicode_data.to_csv(unicode_file, index=False, encoding='utf-8')
        
        result = preprocess_utils.load_recipe_data(str(unicode_file), str(tmp_path))
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'Crème Brûlée' in result['name'].values
        assert 'Ratatouille Niçoise' in result['name'].values

    def test_load_very_large_file_simulation(self, tmp_path):
        """Test simulation d'un fichier très volumineux"""
        # Créer un DataFrame avec beaucoup de lignes
        large_data = pd.DataFrame({
            'id': range(10000),
            'name': [f'Recipe {i}' for i in range(10000)],
            'description': [f'Description for recipe {i}' for i in range(10000)]
        })
        large_file = tmp_path / "large_recipes.csv"
        large_data.to_csv(large_file, index=False)
        
        result = preprocess_utils.load_recipe_data(str(large_file), str(tmp_path))
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10000
        assert 'Recipe 5000' in result['name'].values