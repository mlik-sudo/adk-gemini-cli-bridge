# Guide de Contribution

Merci de contribuer à **ADK-Gemini CLI Bridge** ! 🎉

## 📋 Table des matières

1. [Code de Conduite](#code-de-conduite)
2. [Comment Contribuer](#comment-contribuer)
3. [Configuration de Développement](#configuration-de-développement)
4. [Processus de Développement](#processus-de-développement)
5. [Standards de Code](#standards-de-code)
6. [Tests](#tests)
7. [Documentation](#documentation)

---

## Code de Conduite

Ce projet adhère à un code de conduite standard. En participant, vous acceptez de maintenir un environnement respectueux et inclusif.

---

## Comment Contribuer

### Signaler un Bug 🐛

1. Vérifiez que le bug n'a pas déjà été signalé dans les [Issues](https://github.com/mlik-sudo/adk-gemini-cli-bridge/issues)
2. Créez une nouvelle issue avec le template "Bug Report"
3. Incluez :
   - Description claire du problème
   - Étapes pour reproduire
   - Comportement attendu vs observé
   - Version Python, OS, logs pertinents

### Proposer une Fonctionnalité ✨

1. Créez une issue avec le template "Feature Request"
2. Décrivez :
   - Le problème que ça résout
   - La solution proposée
   - Des alternatives envisagées
   - Des exemples d'utilisation

### Soumettre une Pull Request 🔄

1. Fork le repository
2. Créez une branche : `git checkout -b feature/amazing-feature`
3. Commitez vos changements : `git commit -m 'Add amazing feature'`
4. Pushez vers la branche : `git push origin feature/amazing-feature`
5. Ouvrez une Pull Request

---

## Configuration de Développement

### Prérequis

- Python 3.8+
- Git
- pip

### Installation

```bash
# Cloner le repository
git clone https://github.com/mlik-sudo/adk-gemini-cli-bridge.git
cd adk-gemini-cli-bridge

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances de développement
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Installer les pre-commit hooks
pre-commit install
```

### Configuration

```bash
# Copier le template de configuration
cp config.yaml config.local.yaml
cp .env.example .env

# Éditer les configurations locales
nano config.local.yaml
nano .env
```

---

## Processus de Développement

### 1. Créer une Branche

```bash
# Feature
git checkout -b feature/my-feature

# Bug fix
git checkout -b fix/issue-123

# Documentation
git checkout -b docs/improve-readme
```

### 2. Développer

- Écrivez du code propre et lisible
- Ajoutez des tests pour les nouvelles fonctionnalités
- Mettez à jour la documentation si nécessaire
- Suivez les standards de code (voir ci-dessous)

### 3. Tester

```bash
# Exécuter tous les tests
pytest tests/ -v

# Avec coverage
pytest tests/ --cov=bridge --cov-report=html

# Tests spécifiques
pytest tests/test_validation.py -v

# Pre-commit checks
pre-commit run --all-files
```

### 4. Commiter

```bash
# Format du message de commit
<type>: <description courte>

[Corps optionnel avec détails]

[Footer optionnel avec références]
```

**Types de commits:**
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation uniquement
- `style:` Formatage, points-virgules manquants, etc.
- `refactor:` Refactorisation de code
- `test:` Ajout/modification de tests
- `chore:` Maintenance, dépendances, etc.

**Exemples:**
```bash
git commit -m "feat: add support for custom timeouts per agent"
git commit -m "fix: resolve parameter validation issue #123"
git commit -m "docs: improve configuration examples in README"
```

### 5. Pusher et PR

```bash
git push origin feature/my-feature
```

Ensuite, ouvrez une Pull Request sur GitHub avec :
- Description claire des changements
- Référence aux issues concernées
- Screenshots si applicable
- Checklist complétée

---

## Standards de Code

### Style Python

Nous suivons [PEP 8](https://pep8.org/) avec quelques ajustements :

- **Longueur de ligne** : 120 caractères max
- **Formatage** : Black
- **Imports** : isort
- **Linting** : Flake8, Pylint
- **Type hints** : Mypy

### Formatage Automatique

```bash
# Formatter le code
black bridge.py tests/

# Trier les imports
isort bridge.py tests/

# Vérifier le style
flake8 bridge.py tests/ --max-line-length=120

# Type checking
mypy bridge.py --ignore-missing-imports
```

### Conventions de Nommage

- **Variables/Fonctions** : `snake_case`
- **Classes** : `PascalCase`
- **Constants** : `UPPER_CASE`
- **Privé** : `_leading_underscore`

### Documentation du Code

```python
def function_name(param1: str, param2: int) -> dict:
    """Courte description (une ligne).

    Description détaillée optionnelle sur plusieurs lignes
    expliquant le comportement de la fonction.

    Args:
        param1: Description du premier paramètre
        param2: Description du second paramètre

    Returns:
        Description de ce qui est retourné

    Raises:
        ValueError: Quand param2 est négatif
        KeyError: Quand param1 n'existe pas
    """
    pass
```

---

## Tests

### Écrire des Tests

```python
import pytest
from bridge import Validator, ValidationError

class TestValidation:
    """Test the Validator class."""

    def test_valid_input(self):
        """Test with valid input."""
        result = Validator.validate_repo_name("owner/repo")
        assert result == "owner/repo"

    def test_invalid_input(self):
        """Test with invalid input."""
        with pytest.raises(ValidationError):
            Validator.validate_repo_name("invalid")
```

### Coverage Minimum

- **Nouveau code** : 80% minimum
- **Code critique** : 95% minimum
- **Exceptions** : Documentées dans `pyproject.toml`

### Exécuter les Tests

```bash
# Tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/test_validation.py::TestValidator::test_valid_input

# Avec coverage
pytest tests/ --cov=bridge --cov-report=term-missing

# En mode watch
pytest-watch tests/
```

---

## Documentation

### README

- Garder les exemples à jour
- Ajouter des captures d'écran si pertinent
- Documenter les nouvelles fonctionnalités

### Docstrings

- Toutes les fonctions publiques doivent avoir des docstrings
- Format Google Style ou NumPy Style
- Inclure type hints

### CHANGELOG

- Mettre à jour `CHANGELOG.md` pour chaque PR
- Suivre le format [Keep a Changelog](https://keepachangelog.com/)
- Catégoriser les changements (Added, Changed, Fixed, etc.)

---

## Checklist de Pull Request

Avant de soumettre votre PR, vérifiez que :

- [ ] Le code suit les standards de style (Black, isort, Flake8)
- [ ] Tous les tests passent (`pytest tests/`)
- [ ] Le coverage est >= 80% pour le nouveau code
- [ ] La documentation est à jour (README, docstrings)
- [ ] CHANGELOG.md est mis à jour
- [ ] Les pre-commit hooks passent
- [ ] Pas de secrets ou tokens commités
- [ ] Les messages de commit sont clairs

---

## Questions ?

- Créez une [Discussion](https://github.com/mlik-sudo/adk-gemini-cli-bridge/discussions)
- Contactez les mainteneurs via Issues

Merci de contribuer ! 🙏
