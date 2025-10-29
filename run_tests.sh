#!/bin/bash
#
# Script pour exécuter les tests de preprocessing avec couverture
# 
# Usage:
#   ./run_tests.sh                    # Tous les tests
#   ./run_tests.sh --preprocessing    # Tests preprocessing seulement
#   ./run_tests.sh --fast            # Tests rapides seulement
#   ./run_tests.sh --coverage-only   # Générer seulement le rapport de couverture
#

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "pytest.ini" ]; then
    print_error "Ce script doit être exécuté depuis la racine du projet (où se trouve pytest.ini)"
    exit 1
fi

# Activer l'environnement virtuel si disponible
if [ -d "venv" ]; then
    print_success "Activation de l'environnement virtuel"
    source venv/bin/activate
else
    print_warning "Aucun environnement virtuel trouvé (venv/). Utilisation de l'environnement système."
fi

# Vérifier que pytest et pytest-cov sont installés
python -c "import pytest, pytest_cov" 2>/dev/null || {
    print_error "pytest et pytest-cov ne sont pas installés. Installez-les avec:"
    echo "pip install pytest pytest-cov"
    exit 1
}

# Arguments par défaut
PYTEST_ARGS=""
RUN_COVERAGE=true
SHOW_BROWSER=false

# Parser les arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --preprocessing)
            PYTEST_ARGS="$PYTEST_ARGS -m preprocessing or test_preprocess"
            print_success "Mode: Tests preprocessing seulement"
            shift
            ;;
        --fast)
            PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
            print_success "Mode: Tests rapides seulement"
            shift
            ;;
        --coverage-only)
            RUN_COVERAGE=false
            print_success "Mode: Rapport de couverture seulement"
            shift
            ;;
        --browser)
            SHOW_BROWSER=true
            print_success "Mode: Ouverture automatique du navigateur"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --preprocessing    Exécuter seulement les tests de preprocessing"
            echo "  --fast            Exécuter seulement les tests rapides (skip slow)"
            echo "  --coverage-only   Générer seulement le rapport de couverture"
            echo "  --browser         Ouvrir automatiquement le rapport HTML dans le navigateur"
            echo "  --help, -h        Afficher cette aide"
            exit 0
            ;;
        *)
            print_error "Option inconnue: $1"
            echo "Utilisez --help pour voir les options disponibles"
            exit 1
            ;;
    esac
done

# Créer les répertoires nécessaires
mkdir -p htmlcov
mkdir -p reports

print_header "TESTS UNITAIRES - MODULE PREPROCESSING"

if [ "$RUN_COVERAGE" = true ]; then
    print_success "Exécution des tests avec couverture de code..."
    
    # Exécuter les tests avec couverture
    pytest $PYTEST_ARGS tests/test_preprocess*.py tests/test_text_cleaner.py tests/test_extract_nutrition.py tests/test_nutrition_scoring.py tests/test_compute_popularity.py || {
        print_error "Certains tests ont échoué"
        exit 1
    }
    
    print_success "Tests terminés avec succès!"
    
    # Générer un rapport de couverture en format texte
    print_header "RAPPORT DE COUVERTURE DE CODE"
    coverage report --include="preprocessing/*" --show-missing
    
    # Générer le rapport HTML
    print_success "Génération du rapport HTML..."
    coverage html --include="preprocessing/*" --directory=htmlcov
    
    # Générer le rapport XML pour CI/CD
    coverage xml --include="preprocessing/*" -o reports/coverage.xml
    
    print_success "Rapport HTML généré dans: htmlcov/index.html"
    print_success "Rapport XML généré dans: reports/coverage.xml"
    
    # Résumé de la couverture
    COVERAGE_PERCENT=$(coverage report --include="preprocessing/*" | tail -1 | awk '{print $4}' | sed 's/%//')
    
    if (( $(echo "$COVERAGE_PERCENT >= 80" | bc -l) )); then
        print_success "Couverture de code: ${COVERAGE_PERCENT}% (Objectif atteint ≥80%)"
    elif (( $(echo "$COVERAGE_PERCENT >= 70" | bc -l) )); then
        print_warning "Couverture de code: ${COVERAGE_PERCENT}% (Acceptable, objectif: ≥80%)"
    else
        print_error "Couverture de code: ${COVERAGE_PERCENT}% (Insuffisant, objectif: ≥80%)"
    fi
    
    # Ouvrir le navigateur si demandé
    if [ "$SHOW_BROWSER" = true ]; then
        if command -v xdg-open > /dev/null; then
            print_success "Ouverture du rapport dans le navigateur..."
            xdg-open htmlcov/index.html
        elif command -v open > /dev/null; then
            print_success "Ouverture du rapport dans le navigateur..."
            open htmlcov/index.html
        else
            print_warning "Impossible d'ouvrir automatiquement le navigateur"
            print_success "Ouvrez manuellement: htmlcov/index.html"
        fi
    fi
    
else
    print_success "Génération du rapport de couverture uniquement..."
    
    if [ ! -f ".coverage" ]; then
        print_error "Aucun fichier de couverture trouvé. Exécutez d'abord les tests."
        exit 1
    fi
    
    coverage report --include="preprocessing/*" --show-missing
    coverage html --include="preprocessing/*" --directory=htmlcov
    
    print_success "Rapport HTML mis à jour: htmlcov/index.html"
fi

print_header "RÉSUMÉ DES TESTS"

# Compter les fichiers de test
TEST_FILES=$(find tests/ -name "test_preprocess*.py" -o -name "test_text_cleaner.py" -o -name "test_extract_nutrition.py" -o -name "test_nutrition_scoring.py" -o -name "test_compute_popularity.py" | wc -l)
print_success "Fichiers de test: $TEST_FILES"

# Compter approximativement les tests
TEST_COUNT=$(grep -r "def test_" tests/test_preprocess*.py tests/test_text_cleaner.py tests/test_extract_nutrition.py tests/test_nutrition_scoring.py tests/test_compute_popularity.py 2>/dev/null | wc -l)
print_success "Tests approximatifs: $TEST_COUNT"

# Modules couverts
print_success "Modules testés:"
echo "  - preprocessing/preprocess_utils.py"
echo "  - preprocessing/text_cleaner.py"
echo "  - preprocessing/extract_nutrition.py"
echo "  - preprocessing/nutrition_scoring.py"
echo "  - preprocessing/compute_popularity.py"
echo "  - Intégration complète du pipeline"

print_header "COMMANDES UTILES"
echo "  # Exécuter seulement les tests rapides:"
echo "  ./run_tests.sh --fast"
echo ""
echo "  # Exécuter avec ouverture automatique du rapport:"
echo "  ./run_tests.sh --browser"
echo ""
echo "  # Voir le rapport de couverture détaillé:"
echo "  coverage report --include='preprocessing/*' --show-missing"
echo ""
echo "  # Ouvrir le rapport HTML:"
echo "  xdg-open htmlcov/index.html"

print_success "Tests de preprocessing terminés!"