# Guide des Tests Unitaires - Module Preprocessing

## 📋 Vue d'ensemble

Ce guide décrit la suite de tests unitaires complète créée pour le module `preprocessing` du projet mange-ta-main. Les tests couvrent tous les aspects du pipeline de preprocessing des données de recettes, avec un focus sur la qualité, la couverture de code et la robustesse.

## 🎯 Objectifs des Tests

- **Couverture de code** : Objectif ≥80% sur tous les modules preprocessing
- **Tests complets** : Fonctions, classes, méthodes et cas limites
- **Intégration** : Tests du pipeline complet de bout en bout
- **Performance** : Validation des performances sur de gros datasets
- **Robustesse** : Gestion d'erreurs et données corrompues

## 📁 Structure des Tests

```
tests/
├── conftest.py                          # Configuration pytest et fixtures partagées
├── test_centralized_data_loading.py     # Tests existants (services)
├── test_preprocess_utils.py             # Tests utilitaires de preprocessing
├── test_text_cleaner.py                 # Tests nettoyage de texte
├── test_extract_nutrition.py            # Tests extraction données nutritionnelles
├── test_nutrition_scoring.py            # Tests système de scoring nutritionnel
└── test_preprocessing_integration.py    # Tests d'intégration du pipeline complet
```

## 🔧 Configuration et Installation

### Prérequis

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier les dépendances installées
pip list | grep -E "(pytest|coverage)"
```

### Fichiers de Configuration

- **`pytest.ini`** : Configuration principale de pytest avec options de couverture
- **`.coveragerc`** : Configuration détaillée de coverage.py
- **`run_tests.sh`** : Script d'exécution automatisé avec options

## 🚀 Exécution des Tests

### Méthode Simple - Script Automatisé

```bash
# Tous les tests avec couverture
./run_tests.sh

# Tests rapides seulement (évite les tests marqués 'slow')
./run_tests.sh --fast

# Tests preprocessing seulement
./run_tests.sh --preprocessing

# Avec ouverture automatique du rapport HTML
./run_tests.sh --browser

# Aide
./run_tests.sh --help
```

### Méthode Manuelle - Commandes Pytest

```bash
# Tous les tests preprocessing avec couverture
pytest tests/test_preprocess*.py tests/test_text_cleaner.py tests/test_extract_nutrition.py tests/test_nutrition_scoring.py --cov=preprocessing --cov-report=html

# Tests spécifiques par module
pytest tests/test_text_cleaner.py -v
pytest tests/test_nutrition_scoring.py -v

# Tests avec niveau de verbosité élevé
pytest tests/ -vv --tb=long

# Tests d'intégration seulement
pytest tests/test_preprocessing_integration.py -v
```

### Options Avancées

```bash
# Tests en parallèle (si pytest-xdist installé)
pytest tests/ -n auto

# Tests avec profiling
pytest tests/ --profile

# Tests avec arrêt au premier échec
pytest tests/ -x

# Tests avec capture de logs
pytest tests/ --log-cli-level=INFO
```

## 📊 Rapports de Couverture

### Types de Rapports Générés

1. **Rapport Terminal** : Affichage direct dans la console
2. **Rapport HTML** : Interface web interactive (`htmlcov/index.html`)
3. **Rapport XML** : Format pour intégration CI/CD (`reports/coverage.xml`)
4. **Rapport JSON** : Format machine (`reports/coverage.json`)

### Interprétation des Résultats

#### Rapport Terminal
```
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
preprocessing/extract_nutrition.py     45      2    96%   23, 67
preprocessing/nutrition_scoring.py    156      8    95%   145-152
preprocessing/preprocess_utils.py      67      3    96%   89-91
preprocessing/text_cleaner.py         234     12    95%   45, 123-134
------------------------------------------------------------------
TOTAL                                 502     25    95%
```

#### Métriques Importantes
- **Stmts** : Nombre total d'instructions
- **Miss** : Instructions non couvertes
- **Cover** : Pourcentage de couverture
- **Missing** : Lignes spécifiques non couvertes

### Seuils de Qualité

- 🟢 **≥90%** : Excellente couverture
- 🟡 **80-89%** : Bonne couverture (objectif minimum)
- 🟠 **70-79%** : Couverture acceptable
- 🔴 **<70%** : Couverture insuffisante

## 📋 Détail des Tests par Module

### 1. test_preprocess_utils.py

**Fonctions testées :**
- `load_recipe_data()` : Chargement de données avec téléchargement Kaggle
- `setup_logging()` : Configuration du système de logging

**Scénarios couverts :**
- ✅ Chargement fichier existant
- ✅ Téléchargement automatique depuis Kaggle
- ✅ Gestion des erreurs de réseau
- ✅ Fichiers CSV malformés
- ✅ Permissions et accès fichiers
- ✅ Configuration logging avec timestamps
- ✅ Création répertoires de logs

**Cas limites testés :**
- Fichiers vides
- Erreurs de permission
- Contenu Unicode
- Très gros fichiers

### 2. test_text_cleaner.py

**Fonctions testées :**
- `clean_text()` : Nettoyage de texte avec options de capitalisation
- `clean_list_column()` : Nettoyage de colonnes listes
- `clean_dataframe_text_columns()` : Nettoyage de DataFrames
- `clean_recipe_data()` : Fonction principale pour recettes
- Fonctions privées : `_capitalize_proper_nouns()`, `_apply_smart_title_case()`

**Scénarios couverts :**
- ✅ Restauration contractions (can't, don't, it's, etc.)
- ✅ Capitalisation intelligente (noms propres, famille, pays)
- ✅ Normalisation espaces et ponctuation
- ✅ Mode rapide vs mode complet
- ✅ Intégration NLTK (si disponible)
- ✅ Gestion des listes Python encodées en string
- ✅ Title case intelligent (petits mots, exceptions)

**Cas limites testés :**
- Texte très long (10000+ mots)
- Caractères spéciaux et Unicode
- Listes malformées
- Données mixtes (strings/numbers)
- Intégration sans NLTK

### 3. test_extract_nutrition.py

**Fonctions testées :**
- `extract_nutrition_columns()` : Extraction des 7 colonnes nutritionnelles

**Scénarios couverts :**
- ✅ Arrays nutrition sous forme de listes Python
- ✅ Arrays nutrition sous forme de strings
- ✅ Arrays nutrition sous forme de tuples
- ✅ Formats mixtes dans le même DataFrame
- ✅ Gestion des valeurs manquantes (None, NaN)
- ✅ Arrays malformés ou trop courts
- ✅ Validation des types de données (float)
- ✅ Performance sur gros datasets (10k+ recettes)

**Cas limites testés :**
- DataFrame vide
- Toutes valeurs invalides
- Valeurs nutritionnelles extrêmes (négatives, très élevées)
- Mémoire avec datasets volumineux
- Compatibilité format Kaggle exact

### 4. test_nutrition_scoring.py

**Fonctions testées :**
- `parse_nutrition_entry()` : Parsing des données nutritionnelles
- `score_nutrient_in_range()` : Scoring individuel par nutriment
- `compute_balanced_score()` : Algorithme de scoring équilibré
- `normalize_scores()` : Normalisation 10-98
- `assign_grade()` : Attribution grades A-E
- `score_nutrition()` : Fonction principale complète

**Scénarios couverts :**
- ✅ Plages santé basées sur recommandations WHO/USDA/AHA
- ✅ Poids des nutriments selon impact santé
- ✅ Bonus d'équilibre nutritionnel
- ✅ Pénalités pour valeurs extrêmes
- ✅ Normalisation statistique robuste
- ✅ Système de grades cohérent
- ✅ Extraction calories simultanée

**Cas limites testés :**
- Profils nutritionnels parfaits vs très mauvais
- Valeurs nutritionnelles extrêmes (0, négatives, très élevées)
- Données mixtes valides/invalides
- Performance sur gros datasets
- Cohérence statistique des résultats

### 5. test_preprocessing_integration.py

**Scénarios d'intégration testés :**
- ✅ Pipeline complet : text_cleaner → extract_nutrition → nutrition_scoring
- ✅ Intégrité des données de bout en bout
- ✅ Performance pipeline sur datasets volumineux
- ✅ Gestion des données manquantes/corrompues
- ✅ Compatibilité format Kaggle Food.com
- ✅ Analyse par types de régimes alimentaires
- ✅ Comparaisons restaurant vs fait maison
- ✅ Validation statistique des résultats

**Tests de robustesse :**
- ✅ Données corrompues de types mixtes
- ✅ Efficacité mémoire (datasets 10k+ recettes)
- ✅ Gestion d'erreurs sans crash
- ✅ Cohérence résultats entre exécutions multiples

## 🎯 Métriques de Qualité

### Couverture par Module

| Module | Couverture Cible | Fonctions Critiques |
|--------|------------------|---------------------|
| `preprocess_utils.py` | ≥85% | `load_recipe_data`, `setup_logging` |
| `text_cleaner.py` | ≥90% | `clean_text`, `clean_recipe_data` |
| `extract_nutrition.py` | ≥95% | `extract_nutrition_columns` |
| `nutrition_scoring.py` | ≥90% | `score_nutrition`, `compute_balanced_score` |

### Indicateurs de Performance

- **Temps d'exécution** : <30s pour 1000 recettes
- **Mémoire** : <1GB augmentation pour 10k recettes
- **Robustesse** : 0% de crash sur données corrompues

## 🐛 Debugging et Résolution de Problèmes

### Échecs de Tests Fréquents

#### 1. Échec d'Import
```bash
ModuleNotFoundError: No module named 'preprocessing'
```
**Solution :** Vérifier le PYTHONPATH et la structure des répertoires

#### 2. Données de Test Manquantes
```bash
FileNotFoundError: data/test_recipes.csv
```
**Solution :** Les tests utilisent des fixtures, pas de fichiers externes

#### 3. Couverture Insuffisante
```bash
FAILED: coverage under 80%
```
**Solution :** Ajouter des tests pour les lignes non couvertes identifiées

#### 4. Tests de Performance Lents
```bash
Tests taking too long...
```
**Solution :** Utiliser `./run_tests.sh --fast` ou réduire la taille des datasets de test

### Debug Interactif

```bash
# Exécuter un test spécifique avec debugging
pytest tests/test_nutrition_scoring.py::TestScoreNutrition::test_basic_scoring -v --pdb

# Afficher tous les prints et logs
pytest tests/ -s --log-cli-level=DEBUG

# Capture des warnings détaillés
pytest tests/ --tb=long --disable-warnings
```

## 📈 Amélioration Continue

### Ajout de Nouveaux Tests

1. **Identifier la fonction** à tester
2. **Créer la classe de test** : `class TestNomFonction:`
3. **Implémenter les scénarios** :
   - Cas normal
   - Cas limites
   - Gestion d'erreurs
4. **Ajouter fixtures** si nécessaire
5. **Vérifier la couverture** : `coverage report --include="preprocessing/*"`

### Bonnes Pratiques

- ✅ **Noms explicites** : `test_clean_text_with_contractions`
- ✅ **Une assertion par concept** testé
- ✅ **Fixtures réutilisables** pour données de test
- ✅ **Mocking** pour les dépendances externes
- ✅ **Tests déterministes** (pas de random sans seed)
- ✅ **Documentation** des scénarios complexes

## 🔧 Intégration CI/CD

### Configuration GitHub Actions

```yaml
name: Tests Preprocessing
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests with coverage
      run: |
        ./run_tests.sh
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
      with:
        file: ./reports/coverage.xml
```

### Configuration Badge de Couverture

```markdown
[![Coverage](https://codecov.io/gh/regkhalil/mange-ta-main/branch/main/graph/badge.svg)](https://codecov.io/gh/regkhalil/mange-ta-main)
```

## 📚 Ressources et Références

### Documentation Technique

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Pandas Testing Guide](https://pandas.pydata.org/docs/reference/general.html#testing)

### Standards de Nutrition

- [WHO Dietary Guidelines](https://www.who.int/nutrition/publications/guidelines/en/)
- [USDA Nutrition Guidelines](https://www.dietaryguidelines.gov/)
- [AHA Heart-Healthy Guidelines](https://www.heart.org/en/healthy-living/healthy-eating)

## 🤝 Contribution

Pour contribuer aux tests :

1. **Fork** le projet
2. **Créer une branche** : `git checkout -b feature/nouveau-test`
3. **Ajouter vos tests** en suivant les conventions
4. **Vérifier la couverture** : `./run_tests.sh`
5. **Commit et Push** : `git commit -m "Add: tests for new feature"`
6. **Créer une Pull Request**

## 📞 Support

Pour questions ou problèmes avec les tests :

- **Issues GitHub** : [Créer une issue](https://github.com/regkhalil/mange-ta-main/issues)
- **Documentation** : Consulter ce guide d'abord
- **Logs** : Vérifier les logs de test pour diagnostics

---

**Dernière mise à jour** : Octobre 29, 2025  
**Version des tests** : 1.0  
**Couverture actuelle** : Objectif ≥80%