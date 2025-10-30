"""
Tests corrigés pour les composants Streamlit avec mocking approprié.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import sys
from types import SimpleNamespace

class MockSessionState:
    """Mock personnalisé pour st.session_state qui supporte les attributs et dict access"""
    def __init__(self):
        self._data = {}
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            if not hasattr(self, '_data'):
                super().__setattr__('_data', {})
            self._data[name] = value
    
    def __contains__(self, key):
        return key in self._data
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, value):
        self._data[key] = value

class TestFiltersPanel(unittest.TestCase):
    """Tests corrigés pour le composant filters_panel"""

    @patch('components.filters_panel.st')
    def test_render_filters_panel_sidebar_fixed(self, mock_st):
        """Test du rendu des filtres en sidebar avec mocking corrigé"""
        from components.filters_panel import render_filters_panel
        
        # Mock session state avec notre classe personnalisée
        mock_session = MockSessionState()
        mock_st.session_state = mock_session
        
        # Mock sidebar widgets
        mock_st.sidebar = Mock()
        mock_st.sidebar.header = Mock()
        mock_st.sidebar.subheader = Mock()
        mock_st.sidebar.caption = Mock()
        mock_st.sidebar.slider = Mock(side_effect=[
            (10, 30),  # prep_range
            (3, 8),    # ing_range  
            (200, 600) # cal_range
        ])
        mock_st.sidebar.multiselect = Mock(return_value=['A', 'B'])
        mock_st.sidebar.checkbox = Mock(return_value=True)
        mock_st.sidebar.markdown = Mock()
        
        # Exécuter la fonction
        result = render_filters_panel(in_sidebar=True)
        
        # Vérifications
        self.assertIsInstance(result, dict)
        self.assertIn('prep', result)
        self.assertIn('ingredients', result)
        self.assertIn('calories', result)
        self.assertIn('vegetarian_only', result)
        self.assertIn('nutrition_grades', result)
        
        # Vérifier que filter_key_suffix a été initialisé
        self.assertEqual(mock_session.filter_key_suffix, 0)
        
        # Vérifier les appels aux widgets
        mock_st.sidebar.header.assert_called_with("Filtres")
        self.assertEqual(mock_st.sidebar.slider.call_count, 3)
        mock_st.sidebar.multiselect.assert_called_once()
        mock_st.sidebar.checkbox.assert_called_once()

    @patch('components.filters_panel.st')
    def test_render_filters_panel_main_page_fixed(self, mock_st):
        """Test du rendu des filtres dans la page principale"""
        from components.filters_panel import render_filters_panel
        
        # Mock session state
        mock_session = MockSessionState()
        mock_st.session_state = mock_session
        
        # Mock page principale
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=(Mock(), Mock()))
        
        # Mock des colonnes
        col1, col2 = Mock(), Mock()
        mock_st.columns.return_value = (col1, col2)
        
        # Mock widgets dans les colonnes
        col1.subheader = Mock()
        col1.slider = Mock(side_effect=[(10, 30), (3, 8)])
        col2.subheader = Mock()
        col2.slider = Mock(return_value=(200, 600))
        col2.multiselect = Mock(return_value=['C'])
        col2.checkbox = Mock(return_value=False)
        col2.caption = Mock()
        col2.markdown = Mock()
        
        # Mock autres éléments
        mock_st.caption = Mock()
        
        # Exécuter la fonction
        result = render_filters_panel(in_sidebar=False)
        
        # Vérifications
        self.assertIsInstance(result, dict)
        self.assertEqual(result['nutrition_grades'], ['C'])
        self.assertFalse(result['vegetarian_only'])
        
        # Vérifier la création des colonnes
        mock_st.columns.assert_called_with(2)


class TestMetricsHeader(unittest.TestCase):
    """Tests corrigés pour le composant metrics_header"""

    @patch('components.metrics_header.st')
    def test_render_metrics_header_fixed(self, mock_st):
        """Test du rendu des métriques avec context managers mockés"""
        from components.metrics_header import render_metrics_header
        
        # Mock des colonnes avec support context manager
        class MockColumn:
            def __init__(self):
                pass
            
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                pass
        
        col1, col2, col3, col4 = MockColumn(), MockColumn(), MockColumn(), MockColumn()
        mock_st.columns = Mock(return_value=(col1, col2, col3, col4))
        mock_st.markdown = Mock()
        mock_st.metric = Mock()  # st.metric est appelé dans le context manager
        
        stats = {
            'total_recipes': 1000,
            'median_prep_time': 25.5,
            'avg_calories': 450.2,
            'vegetarian_percentage': 35.7
        }
        
        # Exécuter la fonction
        render_metrics_header(stats)
        
        # Vérifications
        mock_st.columns.assert_called_with(4)
        mock_st.markdown.assert_called()
        
        # Vérifier que st.metric a été appelé 4 fois (une fois par colonne)
        self.assertEqual(mock_st.metric.call_count, 4)
        
        # Vérifier les appels spécifiques
        calls = mock_st.metric.call_args_list
        self.assertIn('📚 Recettes totales', str(calls[0]))
        self.assertIn('⏱️ Temps médian', str(calls[1]))
        self.assertIn('🔥 Calories moyennes', str(calls[2]))
        self.assertIn('🌱 Végétarien', str(calls[3]))

    @patch('components.metrics_header.st')
    def test_render_metrics_header_missing_data(self, mock_st):
        """Test avec données manquantes"""
        from components.metrics_header import render_metrics_header
        
        # Setup mocks simples
        class MockColumn:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        mock_st.columns = Mock(return_value=tuple(MockColumn() for _ in range(4)))
        mock_st.markdown = Mock()
        mock_st.metric = Mock()
        
        # Données incomplètes
        stats = {'total_recipes': 500}
        
        # Doit fonctionner sans erreur
        render_metrics_header(stats)
        
        # Vérifier l'appel
        mock_st.columns.assert_called_with(4)
        self.assertEqual(mock_st.metric.call_count, 4)


if __name__ == '__main__':
    unittest.main()