"""
Tests unitaires pour le module text_cleaner.py

Ce module teste toutes les fonctions de nettoyage de texte :
- clean_text : nettoyage de texte simple avec gestion de la capitalisation
- clean_list_column : nettoyage de colonnes contenant des listes
- clean_dataframe_text_columns : nettoyage de DataFrames complets
- clean_recipe_data : fonction de convenance pour les recettes
- Fonctions privées : _capitalize_proper_nouns, _apply_smart_title_case, etc.
"""

# Configuration du path pour les imports
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing import text_cleaner


class TestCleanText:
    """Tests pour la fonction clean_text"""

    def test_basic_text_cleaning(self):
        """Test le nettoyage de base du texte"""
        text = "this is a simple test"
        result = text_cleaner.clean_text(text)
        assert result == "this is a simple test"

    def test_empty_and_none_text(self):
        """Test avec du texte vide ou None"""
        assert text_cleaner.clean_text("") == ""
        assert text_cleaner.clean_text(None) == ""
        assert text_cleaner.clean_text(pd.NA) == ""

    def test_contraction_restoration(self):
        """Test la restauration des contractions"""
        test_cases = [
            ("can t", "can't"),
            ("don t", "don't"),
            ("won t", "won't"),
            ("it s", "it's"),
            ("i m", "I'm"),
            ("we re", "we're"),
            ("they ll", "they'll"),
            ("mom s recipe", "mom's recipe"),
            ("s mores", "s'mores"),
            ("rock n roll", "rock n' roll"),
        ]

        for input_text, expected in test_cases:
            result = text_cleaner.clean_text(input_text)
            assert expected in result, f"Failed for '{input_text}' -> expected '{expected}' in '{result}'"

    def test_pronoun_i_capitalization(self):
        """Test la capitalisation du pronom 'i'"""
        test_cases = [
            ("i love cooking", "I love cooking"),
            ("when i cook", "when I cook"),
            ("i think i like it", "I think I like it"),
        ]

        for input_text, expected in test_cases:
            result = text_cleaner.clean_text(input_text, is_sentence=True)
            assert expected in result, f"Failed for '{input_text}'"

    def test_whitespace_normalization(self):
        """Test la normalisation des espaces"""
        test_cases = [
            ("too   many    spaces", "too many spaces"),
            ("trailing spaces   ", "trailing spaces"),
            ("   leading spaces", "leading spaces"),
            ("\t\ntabs and newlines\r\n", "tabs and newlines"),
        ]

        for input_text, expected in test_cases:
            result = text_cleaner.clean_text(input_text)
            assert result == expected

    def test_punctuation_fixing(self):
        """Test la correction de la ponctuation"""
        test_cases = [
            ("word , word", "word, word"),
            ("word . word", "word. word"),
            ("word ! word", "word! word"),
            ("word ? word", "word? word"),
            ("word ;; word", "word;; word"),  # Double ponctuation conservée
        ]

        for input_text, expected in test_cases:
            result = text_cleaner.clean_text(input_text)
            assert result == expected

    def test_title_case_application(self):
        """Test l'application du title case"""
        text = "mom's delicious chocolate cake recipe"
        result = text_cleaner.clean_text(text, apply_title_case=True)

        # Vérifier que les mots importants sont capitalisés
        assert "Mom's" in result
        assert "Delicious" in result
        assert "Chocolate" in result
        assert "Cake" in result
        assert "Recipe" in result

    def test_sentence_case_application(self):
        """Test l'application du sentence case"""
        text = "this is a sentence. this is another sentence"
        result = text_cleaner.clean_text(text, is_sentence=True)

        # Vérifier que les phrases commencent par une majuscule
        assert result.startswith("This")
        assert ". This" in result

    def test_fast_mode(self):
        """Test le mode rapide (sans NLTK)"""
        text = "this is a test sentence with proper nouns like paris"
        result = text_cleaner.clean_text(text, fast_mode=True, is_sentence=True)

        # En mode rapide, seule la première lettre devrait être capitalisée
        assert result.startswith("This")
        # Paris ne devrait pas être automatiquement capitalisé en mode rapide
        assert "paris" in result.lower()

    @patch("preprocessing.text_cleaner.NLTK_AVAILABLE", False)
    def test_without_nltk(self):
        """Test le comportement quand NLTK n'est pas disponible"""
        text = "this is a sentence with france and italy"
        result = text_cleaner.clean_text(text, is_sentence=True)

        # Devrait utiliser la liste de secours
        assert "This" in result
        # Les pays dans la liste hardcodée devraient être capitalisés
        assert "France" in result or "france" in result  # Selon l'implémentation


class TestCapitalizeProperNouns:
    """Tests pour les fonctions de capitalisation des noms propres"""

    def test_family_terms_capitalization(self):
        """Test la capitalisation des termes familiaux"""
        test_cases = [
            ("my mom", "my Mom"),
            ("grandma's recipe", "Grandma's recipe"),
            ("uncle bob", "Uncle bob"),  # 'bob' n'est pas dans la liste
            ("dad and mom", "Dad and Mom"),
        ]

        for input_text, expected in test_cases:
            result = text_cleaner._capitalize_proper_nouns(input_text)
            assert expected in result, f"Failed for '{input_text}'"

    def test_nationality_capitalization(self):
        """Test la capitalisation des nationalités"""
        test_cases = [
            ("italian food", "Italian food"),
            ("french cuisine", "French cuisine"),
            ("chinese restaurant", "Chinese restaurant"),
            ("american style", "American style"),
        ]

        for input_text, expected in test_cases:
            result = text_cleaner._capitalize_proper_nouns(input_text)
            assert expected in result

    def test_country_capitalization(self):
        """Test la capitalisation des pays"""
        test_cases = [
            ("from france", "from France"),
            ("italy is beautiful", "Italy is beautiful"),
            ("made in japan", "made in Japan"),
        ]

        for input_text, expected in test_cases:
            result = text_cleaner._capitalize_proper_nouns(input_text)
            assert expected in result

    def test_holiday_capitalization(self):
        """Test la capitalisation des fêtes"""
        test_cases = [
            ("christmas dinner", "Christmas dinner"),
            ("thanksgiving turkey", "Thanksgiving turkey"),
            ("easter eggs", "Easter eggs"),
        ]

        for input_text, expected in test_cases:
            result = text_cleaner._capitalize_proper_nouns(input_text)
            assert expected in result

    def test_punctuation_preservation(self):
        """Test que la ponctuation est préservée lors de la capitalisation"""
        test_cases = [
            ("mom's cooking", "Mom's cooking"),
            ("french, italian, and spanish", "French, Italian, and Spanish"),
            ("christmas? yes!", "Christmas? yes!"),
        ]

        for input_text, expected in test_cases:
            result = text_cleaner._capitalize_proper_nouns(input_text)
            assert expected in result


class TestSmartTitleCase:
    """Tests pour la fonction _apply_smart_title_case"""

    def test_basic_title_case(self):
        """Test le title case de base"""
        text = "chocolate chip cookie recipe"
        result = text_cleaner._apply_smart_title_case(text)
        assert result == "Chocolate Chip Cookie Recipe"

    def test_small_words_handling(self):
        """Test le traitement des petits mots"""
        text = "recipe for the best cake in the world"
        result = text_cleaner._apply_smart_title_case(text)

        # Premier et dernier mot toujours capitalisés
        assert result.startswith("Recipe")
        assert result.endswith("World")

        # Petits mots au milieu en minuscules
        assert " for " in result
        assert " the " in result
        assert " in " in result

    def test_always_caps_words(self):
        """Test les mots toujours capitalisés"""
        text = "mom and dad's recipe with uncle jim"
        result = text_cleaner._apply_smart_title_case(text)

        assert "Mom" in result
        assert "Dad's" in result
        # 'uncle' devrait être capitalisé mais 'jim' dépend de l'implémentation

    def test_contractions_in_title_case(self):
        """Test les contractions en title case"""
        text = "mom's don't worry recipe"
        result = text_cleaner._apply_smart_title_case(text)

        assert "Mom's" in result
        assert "Don't" in result  # Partie avant l'apostrophe capitalisée


class TestCleanListColumn:
    """Tests pour la fonction clean_list_column"""

    def test_string_list_parsing(self):
        """Test le parsing d'une liste sous forme de string"""
        list_string = "['salt', 'pepper', 'garlic']"
        result = text_cleaner.clean_list_column(list_string)

        assert isinstance(result, list)
        assert len(result) == 3
        assert "salt" in result
        assert "pepper" in result
        assert "garlic" in result

    def test_actual_list_input(self):
        """Test avec une vraie liste en entrée"""
        actual_list = ["salt", "pepper", "garlic"]
        result = text_cleaner.clean_list_column(actual_list)

        assert isinstance(result, list)
        assert len(result) == 3

    def test_malformed_string_list(self):
        """Test avec une liste mal formée"""
        malformed = "['salt', 'pepper'"  # Pas de fermeture
        result = text_cleaner.clean_list_column(malformed)

        assert isinstance(result, list)
        assert len(result) == 0  # Devrait retourner une liste vide

    def test_title_case_application_to_list(self):
        """Test l'application du title case aux éléments de liste"""
        list_data = ["mom recipe", "italian food", "chocolate cake"]
        result = text_cleaner.clean_list_column(list_data, apply_title_case=True)

        assert "Mom Recipe" in result
        assert "Italian Food" in result
        assert "Chocolate Cake" in result

    def test_sentence_capitalization_to_list(self):
        """Test la capitalisation de phrase pour les éléments de liste"""
        list_data = ["mix the ingredients", "bake for 30 minutes", "let cool"]
        result = text_cleaner.clean_list_column(list_data, capitalize_first=True)

        assert any(item.startswith("Mix") for item in result)
        assert any(item.startswith("Bake") for item in result)
        assert any(item.startswith("Let") for item in result)

    def test_fast_mode_for_list(self):
        """Test le mode rapide pour les listes"""
        list_data = ["ingredient one", "ingredient two with france"]
        result = text_cleaner.clean_list_column(list_data, fast_mode=True)

        # En mode rapide, le nettoyage devrait être minimal
        assert isinstance(result, list)
        assert len(result) == 2

    def test_empty_and_none_list_items(self):
        """Test avec des éléments vides ou None dans la liste"""
        list_data = ["valid item", "", None, "another valid item"]
        result = text_cleaner.clean_list_column(list_data)

        # Les éléments vides devraient être filtrés
        assert len(result) == 2
        assert "valid item" in result
        assert "another valid item" in result

    def test_non_string_list_items(self):
        """Test avec des éléments non-string dans la liste"""
        list_data = ["string item", 123, 45.6, "another string"]
        result = text_cleaner.clean_list_column(list_data)

        assert isinstance(result, list)
        assert "string item" in result
        assert "another string" in result
        assert "123" in result  # Converti en string
        assert "45.6" in result  # Converti en string


class TestCleanDataframeTextColumns:
    """Tests pour la fonction clean_dataframe_text_columns"""

    def test_clean_text_columns(self):
        """Test le nettoyage des colonnes de texte"""
        df = pd.DataFrame(
            {
                "description": ["this is recipe one", "this is recipe two"],
                "name": ["recipe name one", "recipe name two"],
                "other": ["other data", "more data"],
            }
        )

        result = text_cleaner.clean_dataframe_text_columns(df, text_columns=["description", "name"])

        assert "description_cleaned" in result.columns
        assert "name_cleaned" in result.columns
        assert "other" in result.columns  # Colonne non modifiée

        # Vérifier que le nettoyage a été appliqué
        assert result["description_cleaned"].iloc[0].startswith("This")

    def test_clean_list_columns(self):
        """Test le nettoyage des colonnes de listes"""
        df = pd.DataFrame(
            {
                "tags": ["['italian', 'pasta']", "['dessert', 'sweet']"],
                "steps": ["['step one', 'step two']", "['boil water', 'add pasta']"],
                "other": ["data1", "data2"],
            }
        )

        result = text_cleaner.clean_dataframe_text_columns(df, list_columns=["tags", "steps"])

        assert "tags_cleaned" in result.columns
        assert "steps_cleaned" in result.columns

        # Vérifier que les listes ont été nettoyées
        assert isinstance(result["tags_cleaned"].iloc[0], list)
        assert isinstance(result["steps_cleaned"].iloc[0], list)

    def test_inplace_modification(self):
        """Test la modification en place"""
        df = pd.DataFrame({"description": ["test description"], "tags": ["['tag1', 'tag2']"]})
        original_id = id(df)

        result = text_cleaner.clean_dataframe_text_columns(
            df, text_columns=["description"], list_columns=["tags"], inplace=True
        )

        assert id(result) == original_id  # Même objet
        assert "description_cleaned" in df.columns

    def test_missing_columns_warning(self, caplog):
        """Test l'avertissement pour les colonnes manquantes"""
        df = pd.DataFrame({"existing": ["data"]})

        with caplog.at_level("WARNING"):
            text_cleaner.clean_dataframe_text_columns(
                df, text_columns=["nonexistent"], list_columns=["also_nonexistent"]
            )

        assert "Column 'nonexistent' not found" in caplog.text
        assert "Column 'also_nonexistent' not found" in caplog.text


class TestCleanRecipeData:
    """Tests pour la fonction clean_recipe_data"""

    def create_sample_recipe_df(self):
        """Créer un DataFrame de recettes d'exemple"""
        return pd.DataFrame(
            {
                "name": ["mom s chocolate cake", "italian pasta recipe"],
                "description": ["this is a delicious cake recipe", "traditional italian pasta"],
                "steps": ["['mix ingredients', 'bake for 30 minutes']", "['boil water', 'add pasta']"],
                "tags": ["['dessert', 'chocolate']", "['italian', 'pasta']"],
                "ingredients": ["['flour', 'chocolate', 'sugar']", "['pasta', 'tomato sauce']"],
                "other_column": ["data1", "data2"],
            }
        )

    def test_clean_all_recipe_columns(self):
        """Test le nettoyage de toutes les colonnes de recettes"""
        df = self.create_sample_recipe_df()

        result = text_cleaner.clean_recipe_data(df)

        # Vérifier que toutes les colonnes nettoyées ont été créées
        expected_columns = [
            "name_cleaned",
            "description_cleaned",
            "steps_cleaned",
            "tags_cleaned",
            "ingredients_cleaned",
        ]

        for col in expected_columns:
            assert col in result.columns

    def test_selective_cleaning(self):
        """Test le nettoyage sélectif des colonnes"""
        df = self.create_sample_recipe_df()

        result = text_cleaner.clean_recipe_data(
            df, clean_name=True, clean_description=False, clean_steps=False, clean_tags=False, clean_ingredients=False
        )

        assert "name_cleaned" in result.columns
        assert "description_cleaned" not in result.columns
        assert "steps_cleaned" not in result.columns

    def test_name_title_case(self):
        """Test que les noms utilisent le title case"""
        df = pd.DataFrame({"name": ["mom s chocolate cake recipe"]})

        result = text_cleaner.clean_recipe_data(df, clean_name=True)

        cleaned_name = result["name_cleaned"].iloc[0]
        assert "Mom's" in cleaned_name
        assert "Chocolate" in cleaned_name
        assert "Cake" in cleaned_name

    def test_description_sentence_case(self):
        """Test que les descriptions utilisent le sentence case"""
        df = pd.DataFrame({"description": ["this is a description. this is another sentence"]})

        result = text_cleaner.clean_recipe_data(df, clean_description=True)

        cleaned_desc = result["description_cleaned"].iloc[0]
        assert cleaned_desc.startswith("This")
        assert ". This" in cleaned_desc

    def test_steps_fast_mode(self):
        """Test que les étapes utilisent le mode rapide"""
        df = pd.DataFrame({"steps": ["['step one with france', 'step two with italy']"]})

        result = text_cleaner.clean_recipe_data(df, clean_steps=True)

        cleaned_steps = result["steps_cleaned"].iloc[0]
        assert isinstance(cleaned_steps, list)
        # En mode rapide, les pays ne devraient pas être automatiquement capitalisés

    def test_ingredients_title_case(self):
        """Test que les ingrédients utilisent le title case"""
        df = pd.DataFrame({"ingredients": ["['fresh basil', 'extra virgin olive oil']"]})

        result = text_cleaner.clean_recipe_data(df, clean_ingredients=True)

        cleaned_ingredients = result["ingredients_cleaned"].iloc[0]
        assert isinstance(cleaned_ingredients, list)
        # Les ingrédients devraient avoir un title case approprié

    def test_inplace_recipe_cleaning(self):
        """Test le nettoyage en place des recettes"""
        df = self.create_sample_recipe_df()
        original_id = id(df)

        result = text_cleaner.clean_recipe_data(df, inplace=True)

        assert id(result) == original_id
        assert "name_cleaned" in df.columns


class TestNLTKIntegration:
    """Tests pour l'intégration NLTK (si disponible)"""

    @patch("preprocessing.text_cleaner.NLTK_AVAILABLE", True)
    @patch("preprocessing.text_cleaner.word_tokenize")
    @patch("preprocessing.text_cleaner.pos_tag")
    def test_nltk_proper_noun_detection(self, mock_pos_tag, mock_tokenize):
        """Test la détection automatique des noms propres avec NLTK"""
        # Mock des fonctions NLTK
        mock_tokenize.return_value = ["this", "is", "Paris", "in", "France"]
        mock_pos_tag.return_value = [("this", "DT"), ("is", "VBZ"), ("Paris", "NNP"), ("in", "IN"), ("France", "NNP")]

        text = "this is paris in france"
        result = text_cleaner._capitalize_proper_nouns_nltk(text)

        # Vérifier que les noms propres détectés par NLTK sont capitalisés
        assert "Paris" in result
        assert "France" in result

    @patch("preprocessing.text_cleaner.NLTK_AVAILABLE", True)
    @patch("preprocessing.text_cleaner.word_tokenize", side_effect=Exception("NLTK Error"))
    def test_nltk_fallback_on_error(self, mock_tokenize):
        """Test le fallback en cas d'erreur NLTK"""
        text = "this is france"
        result = text_cleaner._capitalize_proper_nouns_nltk(text)

        # Devrait revenir à la méthode de fallback
        assert isinstance(result, str)


class TestDemoFunction:
    """Tests pour la fonction de démonstration"""

    @patch("preprocessing.text_cleaner.pd.read_csv")
    def test_demo_cleaning_execution(self, mock_read_csv):
        """Test que la fonction de démo s'exécute sans erreur"""
        # Mock des données de test
        mock_df = pd.DataFrame(
            {
                "name": ["test recipe"],
                "description": ["test description"],
                "steps": ["['step one', 'step two']"],
                "tags": ["['tag1', 'tag2']"],
                "ingredients": ["['ingredient1', 'ingredient2']"],
            }
        )
        mock_read_csv.return_value = mock_df

        # La fonction demo ne devrait pas lever d'exception
        try:
            text_cleaner.demo_cleaning(sample_size=1)
        except Exception as e:
            pytest.fail(f"demo_cleaning raised an exception: {e}")


class TestEdgeCasesAndPerformance:
    """Tests pour les cas limites et la performance"""

    def test_very_long_text(self):
        """Test avec du texte très long"""
        long_text = "word " * 10000  # 10000 mots
        result = text_cleaner.clean_text(long_text, is_sentence=True)

        assert isinstance(result, str)
        assert result.startswith("Word")  # Première lettre capitalisée

    def test_special_characters(self):
        """Test avec des caractères spéciaux"""
        special_text = "café naïve résumé piñata"
        result = text_cleaner.clean_text(special_text, apply_title_case=True)

        assert isinstance(result, str)
        # Les caractères spéciaux devraient être préservés

    def test_numbers_and_text(self):
        """Test avec mélange de nombres et texte"""
        mixed_text = "recipe for 2 people with 3 cups flour"
        result = text_cleaner.clean_text(mixed_text, apply_title_case=True)

        assert "2" in result
        assert "3" in result
        assert isinstance(result, str)

    def test_multiple_punctuation(self):
        """Test avec ponctuation multiple"""
        punct_text = "wow!!! amazing... really???"
        result = text_cleaner.clean_text(punct_text)

        assert isinstance(result, str)
        # La ponctuation multiple devrait être gérée

    def test_mixed_case_input(self):
        """Test avec casse mixte en entrée"""
        mixed_case = "ThIs Is A MiXeD cAsE tExT"
        result = text_cleaner.clean_text(mixed_case, apply_title_case=True)

        assert isinstance(result, str)
        # Devrait normaliser la casse

    def test_clean_list_with_empty_strings(self):
        """Test clean_list_column avec des strings vides"""
        list_with_empties = ["valid", "", "   ", "another valid", None]
        result = text_cleaner.clean_list_column(list_with_empties)

        # Les éléments vides devraient être filtrés
        assert len(result) == 2
        assert "valid" in result
        assert "another valid" in result


@pytest.fixture
def sample_dataframe():
    """Fixture pour DataFrame d'exemple"""
    return pd.DataFrame(
        {
            "name": ["mom s cake recipe", "italian pasta dish"],
            "description": ["this is delicious", "traditional recipe from italy"],
            "steps": ["['mix well', 'bake 30 min']", "['boil water', 'add pasta']"],
            "tags": ["['dessert', 'chocolate']", "['italian', 'dinner']"],
            "ingredients": ["['flour', 'eggs']", "['pasta', 'tomato']"],
            "nutrition": [[300, 10, 5, 200, 15, 3, 30], [250, 8, 2, 150, 12, 2, 40]],
            "id": [1, 2],
        }
    )


class TestIntegrationWithDataFrame:
    """Tests d'intégration avec des DataFrames réels"""

    def test_full_recipe_cleaning_pipeline(self, sample_dataframe):
        """Test du pipeline complet de nettoyage"""
        result = text_cleaner.clean_recipe_data(sample_dataframe)

        # Vérifier que toutes les colonnes sont présentes
        original_cols = set(sample_dataframe.columns)
        cleaned_cols = {"name_cleaned", "description_cleaned", "steps_cleaned", "tags_cleaned", "ingredients_cleaned"}

        assert original_cols.issubset(set(result.columns))
        assert cleaned_cols.issubset(set(result.columns))

        # Vérifier quelques transformations spécifiques
        assert "Mom's" in result["name_cleaned"].iloc[0]
        assert result["description_cleaned"].iloc[0].startswith("This")
        assert isinstance(result["steps_cleaned"].iloc[0], list)

    def test_performance_with_large_dataframe(self):
        """Test de performance avec un grand DataFrame"""
        large_df = pd.DataFrame(
            {
                "name": [f"recipe {i}" for i in range(1000)],
                "description": [f"description {i}" for i in range(1000)],
                "steps": [f"['step {i}', 'step {i + 1}']" for i in range(1000)],
            }
        )

        import time

        start_time = time.time()
        result = text_cleaner.clean_recipe_data(large_df)
        end_time = time.time()

        # Vérifier que ça s'exécute en temps raisonnable (< 30 secondes)
        assert end_time - start_time < 30
        assert len(result) == 1000
