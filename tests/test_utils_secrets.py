"""
Tests unitaires pour les utilitaires (utils/).

Ce module teste les utilitaires :
- secrets.py - Gestion des secrets et variables d'environnement
- Autres modules utils (navigation.py, recipe_detail.py, stats.py déjà testés)
"""

import json
import os
import pytest
from unittest.mock import MagicMock, patch

from utils.secrets import get_secret, get_google_token_json, get_google_folder_id, get_google_credentials_json


class TestSecretsManagement:
    """Tests pour la gestion des secrets."""

    def test_get_secret_simple_string(self):
        """Test de récupération d'un secret simple."""
        with patch.dict(os.environ, {'TEST_KEY': 'test_value'}):
            result = get_secret('TEST_KEY')
            assert result == 'test_value'

    def test_get_secret_with_default(self):
        """Test avec valeur par défaut."""
        # Clé qui n'existe pas
        result = get_secret('NONEXISTENT_KEY', 'default_value')
        assert result == 'default_value'

    def test_get_secret_case_conversion(self):
        """Test de conversion automatique en majuscules."""
        with patch.dict(os.environ, {'TEST_KEY_UPPER': 'upper_value'}):
            # Test avec clé en minuscules
            result = get_secret('test_key_upper')
            assert result == 'upper_value'
            
            # Test avec points convertis en underscores
            result = get_secret('test.key.upper')
            assert result == 'upper_value'

    def test_get_secret_json_parsing(self):
        """Test du parsing JSON automatique."""
        json_data = '{"key1": "value1", "key2": 42}'
        
        with patch.dict(os.environ, {'JSON_SECRET': json_data}):
            result = get_secret('JSON_SECRET')
            
            assert isinstance(result, dict)
            assert result['key1'] == 'value1'
            assert result['key2'] == 42

    def test_get_secret_json_with_nested_key(self):
        """Test avec clé nestée dans JSON."""
        json_data = '{"database": {"host": "localhost", "port": 5432}, "api_key": "secret123"}'
        
        with patch.dict(os.environ, {'CONFIG_JSON': json_data}):
            # Test de récupération de clé nestée
            result = get_secret('CONFIG_JSON', nested_key='api_key')
            assert result == 'secret123'
            
            # Test de récupération d'objet nested
            result = get_secret('CONFIG_JSON', nested_key='database')
            assert result == {"host": "localhost", "port": 5432}
            
            # Test de clé nestée inexistante
            result = get_secret('CONFIG_JSON', default='not_found', nested_key='missing_key')
            assert result == 'not_found'

    def test_get_secret_json_array(self):
        """Test avec array JSON."""
        json_array = '["item1", "item2", "item3"]'
        
        with patch.dict(os.environ, {'ARRAY_SECRET': json_array}):
            result = get_secret('ARRAY_SECRET')
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0] == 'item1'

    def test_get_secret_invalid_json(self):
        """Test avec JSON invalide."""
        invalid_json = '{"invalid": json,}'
        
        with patch.dict(os.environ, {'INVALID_JSON': invalid_json}):
            # Doit retourner la chaîne brute si le parsing JSON échoue
            result = get_secret('INVALID_JSON')
            assert result == invalid_json

    def test_get_secret_empty_string(self):
        """Test avec chaîne vide."""
        with patch.dict(os.environ, {'EMPTY_SECRET': ''}):
            result = get_secret('empty_secret', 'default')
            # Chaîne vide est évaluée comme False, donc retourne default
            assert result == 'default'
            
        # Test sans la variable d'environnement
        result = get_secret('TRULY_MISSING', 'default')
        assert result == 'default'

    def test_get_google_token_json(self):
        """Test récupération token Google JSON."""
        google_token = {
            "access_token": "access_123",
            "refresh_token": "refresh_456",
            "token_type": "Bearer"
        }
        
        with patch.dict(os.environ, {'GOOGLE_TOKEN': json.dumps(google_token)}):
            result = get_google_token_json()
            assert result == google_token
            assert isinstance(result, dict)
            assert result['access_token'] == 'access_123'

    def test_get_google_token_json_missing(self):
        """Test avec token Google manquant."""
        # Assurer qu'aucune variable d'environnement Google n'existe
        env_vars_to_clear = ['GOOGLE_TOKEN_JSON', 'GOOGLE']
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_google_token_json()
            assert result is None

    def test_get_google_token_json_from_nested(self):
        """Test récupération token depuis config nested."""
        config = {
            "google": {
                "token": {
                    "access_token": "nested_access_token",
                    "refresh_token": "nested_refresh_token"
                }
            }
        }
        
        with patch.dict(os.environ, {'GOOGLE': json.dumps(config['google'])}):
            # get_google_token_json ne supporte pas nested key directement
            # Elle cherche seulement GOOGLE_TOKEN
            result = get_google_token_json()
            assert result is None  # Car GOOGLE_TOKEN n'est pas défini
            
        # Test avec GOOGLE_TOKEN défini
        with patch.dict(os.environ, {'GOOGLE_TOKEN': json.dumps(config['google']['token'])}):
            result = get_google_token_json()
            assert isinstance(result, dict)
            assert result['access_token'] == 'nested_access_token'

    def test_get_google_folder_id(self):
        """Test de récupération de l'ID du dossier Google."""
        # Test avec ID direct
        with patch.dict(os.environ, {'GOOGLE_FOLDER_ID': 'direct_folder_id'}):
            result = get_google_folder_id()
            assert result == 'direct_folder_id'

    def test_get_google_folder_id_from_nested(self):
        """Test récupération folder ID depuis config nested."""
        config = {
            "google": {
                "folder_id": "nested_folder_id"
            }
        }
        
        with patch.dict(os.environ, {'GOOGLE': json.dumps(config['google'])}):
            # get_google_folder_id cherche directement GOOGLE_FOLDER_ID
            result = get_google_folder_id()
            assert result is None  # Car GOOGLE_FOLDER_ID n'est pas défini
            
        # Test avec GOOGLE_FOLDER_ID défini
        with patch.dict(os.environ, {'GOOGLE_FOLDER_ID': 'nested_folder_id'}):
            result = get_google_folder_id()
            assert result == 'nested_folder_id'

    def test_get_google_folder_id_missing(self):
        """Test avec ID de dossier manquant."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_google_folder_id()
            assert result is None

    def test_secrets_integration_workflow(self):
        """Test workflow complet de récupération de secrets."""
        # Configuration complète
        google_creds = {"client_id": "workflow_client", "client_secret": "workflow_secret"}
        google_token = {"access_token": "workflow_access_token", "refresh_token": "workflow_refresh"}
        
        with patch.dict(os.environ, {
            'GOOGLE_CREDENTIALS': json.dumps(google_creds),
            'GOOGLE_TOKEN': json.dumps(google_token),
            'GOOGLE_FOLDER_ID': 'workflow_folder_123'
        }):
            # Test récupération credentials
            creds = get_google_credentials_json()
            assert creds['client_id'] == 'workflow_client'
            
            # Test récupération token
            token = get_google_token_json()
            assert token['access_token'] == 'workflow_access_token'
            
            # Test folder ID
            folder_id = get_google_folder_id()
            assert folder_id == 'workflow_folder_123'

    def test_secrets_error_handling(self):
        """Test gestion d'erreurs avec JSON malformé."""
        # JSON malformé
        with patch.dict(os.environ, {'MALFORMED_JSON': '{"key": "value"'}):  # JSON incomplet
            result = get_secret('malformed_json', 'default')
            # JSON malformé retourne la chaîne telle quelle
            assert result == '{"key": "value"'

    def test_secrets_type_conversions(self):
        """Test des conversions de types automatiques."""
        test_configs = {
            'STRING_VAL': 'just_a_string',
            'NUMBER_VAL': '42',
            'BOOL_VAL': 'true',
            'JSON_OBJECT': '{"nested": {"value": 123}}',
            'JSON_ARRAY': '[1, 2, 3, 4, 5]'
        }
        
        with patch.dict(os.environ, test_configs):
            # String normal
            assert get_secret('STRING_VAL') == 'just_a_string'
            
            # Nombre (reste string sauf si JSON)
            assert get_secret('NUMBER_VAL') == '42'
            
            # Booléen (reste string sauf si JSON)
            assert get_secret('BOOL_VAL') == 'true'
            
            # Objet JSON
            obj = get_secret('JSON_OBJECT')
            assert isinstance(obj, dict)
            assert obj['nested']['value'] == 123
            
            # Array JSON
            arr = get_secret('JSON_ARRAY')
            assert isinstance(arr, list)
            assert len(arr) == 5

    def test_secrets_environment_compatibility(self):
        """Test de compatibilité entre différents environnements."""
        # Simuler différents scénarios d'environnement
        scenarios = [
            {
                'name': 'local_development',
                'env': {'STREAMLIT_ENV': 'dev', 'DEBUG_MODE': 'true'}
            },
            {
                'name': 'hugging_face_spaces',
                'env': {'SPACE_ID': 'test-space', 'STREAMLIT_ENV': 'prod'}
            },
            {
                'name': 'docker_deployment',
                'env': {'CONTAINER_ENV': 'docker', 'STREAMLIT_ENV': 'prod'}
            }
        ]
        
        for scenario in scenarios:
            with patch.dict(os.environ, scenario['env'], clear=True):
                env = get_secret('STREAMLIT_ENV', 'dev')
                assert env in ['dev', 'prod']
                
                # Test que les secrets manquants retournent les defaults
                missing_secret = get_secret('NONEXISTENT_SECRET', 'default_value')
                assert missing_secret == 'default_value'


class TestSecretsEdgeCases:
    """Tests pour les cas limites des secrets."""

    def test_unicode_secrets(self):
        """Test avec caractères Unicode."""
        unicode_secret = '{"message": "Héllo wörld! 🌍", "émoji": "✅"}'
        
        with patch.dict(os.environ, {'UNICODE_SECRET': unicode_secret}):
            result = get_secret('UNICODE_SECRET')
            
            assert isinstance(result, dict)
            assert result['message'] == "Héllo wörld! 🌍"
            assert result['émoji'] == "✅"

    def test_very_long_secrets(self):
        """Test avec secrets très longs."""
        long_value = 'x' * 10000  # 10KB de données
        
        with patch.dict(os.environ, {'LONG_SECRET': long_value}):
            result = get_secret('LONG_SECRET')
            assert len(result) == 10000
            assert result == long_value

    def test_special_characters_in_keys(self):
        """Test avec caractères spéciaux dans les clés."""
        special_configs = {
            'KEY_WITH_DASHES': 'dashes-value',
            'KEY_WITH_DOTS': 'dots.value',
            'KEY_WITH_NUMBERS_123': 'numbers-value'
        }
        
        with patch.dict(os.environ, special_configs):
            # Test conversion des points en underscores
            result = get_secret('key.with.dots')
            assert result == 'dots.value'
            
            # Test avec tirets (pas de conversion)
            result = get_secret('key-with-dashes', 'default')
            assert result == 'default'  # Clé non trouvée car pas de conversion pour tirets

    def test_nested_json_deep_nesting(self):
        """Test avec JSON très imbriqué."""
        deep_json = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "deep_value": "found_it!"
                        }
                    }
                }
            }
        }
        
        with patch.dict(os.environ, {'DEEP_JSON': json.dumps(deep_json)}):
            # Récupération de niveau 1
            result = get_secret('DEEP_JSON', nested_key='level1')
            assert 'level2' in result
            
            # Note: La fonction actuelle ne gère qu'un niveau de nesting
            # Pour des niveaux plus profonds, il faudrait l'étendre

    def test_concurrent_access_simulation(self):
        """Test de simulation d'accès concurrent."""
        import threading
        import time
        
        results = []
        
        def access_secret(secret_name, expected_value):
            """Fonction pour accéder aux secrets dans un thread."""
            result = get_secret(secret_name, 'default')
            results.append((secret_name, result, expected_value))
        
        with patch.dict(os.environ, {'CONCURRENT_SECRET': 'concurrent_value'}):
            threads = []
            
            # Créer plusieurs threads accédant au même secret
            for i in range(10):
                thread = threading.Thread(
                    target=access_secret,
                    args=('CONCURRENT_SECRET', 'concurrent_value')
                )
                threads.append(thread)
                thread.start()
            
            # Attendre que tous les threads terminent
            for thread in threads:
                thread.join()
            
            # Vérifier que tous ont obtenu la bonne valeur
            assert len(results) == 10
            for secret_name, result, expected in results:
                assert result == expected

    def test_memory_usage_with_large_configs(self):
        """Test d'utilisation mémoire avec grandes configurations."""
        # Créer une grande configuration JSON
        large_config = {
            f"key_{i}": f"value_{i}" * 100 for i in range(1000)
        }
        
        with patch.dict(os.environ, {'LARGE_CONFIG': json.dumps(large_config)}):
            # Récupération multiple - vérifier qu'il n'y a pas de fuite mémoire
            for _ in range(100):
                result = get_secret('LARGE_CONFIG')
                assert isinstance(result, dict)
                assert len(result) == 1000
            
            # Test de récupération d'une clé spécifique
            specific_value = get_secret('LARGE_CONFIG', nested_key='key_500')
            assert specific_value == 'value_500' * 100


if __name__ == "__main__":
    pytest.main([__file__])