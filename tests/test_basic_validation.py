"""
Test simple pour valider la configuration et les imports
"""

import pandas as pd
import pytest
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test que tous les modules peuvent être importés"""
    from preprocessing import extract_nutrition
    from preprocessing import nutrition_scoring  
    from preprocessing import preprocess_utils
    from preprocessing import text_cleaner
    
    assert extract_nutrition is not None
    assert nutrition_scoring is not None
    assert preprocess_utils is not None
    assert text_cleaner is not None

def test_extract_nutrition_basic():
    """Test basique d'extraction de nutrition"""
    from preprocessing import extract_nutrition
    
    df = pd.DataFrame({
        'nutrition': [[300, 15, 10, 500, 20, 5, 45]]
    })
    
    result = extract_nutrition.extract_nutrition_columns(df)
    
    assert 'calories' in result.columns
    assert result['calories'].iloc[0] == 300
    assert result['protein'].iloc[0] == 20

def test_text_cleaner_basic():
    """Test basique de nettoyage de texte"""
    from preprocessing import text_cleaner
    
    text = "this is a test"
    result = text_cleaner.clean_text(text, is_sentence=True)
    
    assert result.startswith("This")

def test_nutrition_scoring_basic():
    """Test basique de scoring nutritionnel"""
    from preprocessing import nutrition_scoring
    
    df = pd.DataFrame({
        'nutrition': [[300, 15, 10, 500, 20, 5, 45]]
    })
    
    result = nutrition_scoring.score_nutrition(df)
    
    assert 'nutrition_score' in result.columns
    assert 'nutrition_grade' in result.columns
    assert 10 <= result['nutrition_score'].iloc[0] <= 98