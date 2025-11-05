# Changelog

Tous les changements notables de ce projet seront documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-05

### ✨ Ajouté

#### Outils de Diagnostic
- **Script de diagnostic complet** (`diagnose.py`)
  - Vérification automatique de l'installation
  - 40+ checks (Python, dépendances, fichiers, workspace, agents)
  - Mode verbose pour détails
  - Mode `--fix` pour réparations automatiques
  - Smoke tests intégrés (syntaxe, import, health check)
  - Output coloré avec résumé détaillé

#### Documentation
- **AGENT_PROTOCOL.md** - Documentation complète du protocole
  - Détails du protocole hybride (CLI args + JSON stdin)
  - Guide d'implémentation pour les développeurs d'agents
  - Exemples de code pour chaque approche
  - Spécifications de validation des paramètres
  - Best practices et troubleshooting
  - Guide de migration

### 🔧 Modifié

#### README
- Amélioration section configuration MCP
  - ⚠️ Avertissement contre `cat >>` (risque de JSON invalide)
  - Instructions de fusion manuelle détaillées
  - Commandes de validation JSON
  - Sauvegarde recommandée
- Ajout section "Diagnostic et Vérification"
  - Documentation du script diagnose.py
  - Exemple de sortie
  - Liste des vérifications effectuées
- Amélioration section "Dépannage"
  - Structuration en sous-sections numérotées
  - Ajout troubleshooting JSON invalide
  - Ajout troubleshooting permissions

### 📝 Notes

- La création automatique du répertoire de logs existait déjà (bridge.py:272)
- La validation de l'existence des scripts agents existait déjà (bridge.py:407)
- L'import `lru_cache` inutilisé avait déjà été supprimé dans v1.0.0

### 🔄 Compatibilité

- Rétrocompatible avec v1.0.0
- Aucun changement dans l'API ou le protocole
- Script diagnose.py est optionnel

---

## [1.0.0] - 2025-11-05

### ✨ Ajouté

#### Configuration & Flexibilité
- **Configuration YAML externe** (`config.yaml`) pour personnaliser le comportement du bridge
- Support des **variables d'environnement** (`ADK_WORKSPACE`, `BRIDGE_LOG_LEVEL`, `BRIDGE_LOG_FILE`)
- Configuration par défaut intégrée (fallback automatique si config.yaml absent)
- **Timeouts configurables** par agent
- Paramètres par défaut personnalisables par agent

#### Sécurité
- **Validation stricte des paramètres** avec regex et type checking
  - Validation du format `owner/repo` pour GitHub
  - Validation des numéros d'issue (positifs, limites raisonnables)
  - Validation des sources (whitelist)
- **Sanitisation des entrées** pour prévenir les injections
- Limites de taille des payloads (10KB par défaut, configurable)
- Validation JSON Schema dans MCP template

#### Logging & Monitoring
- **Rotation automatique des logs** avec `RotatingFileHandler`
  - Taille maximale: 10MB par défaut
  - 5 fichiers de backup
- **Système de métriques** complet
  - Compteurs d'appels, succès, erreurs
  - Durées d'exécution moyennes
  - Historique des erreurs (100 dernières)
- **Endpoint `health_check`** pour monitoring
  - Status global (healthy/degraded)
  - Métriques par agent
  - Taux d'erreur

#### Tests & Qualité
- **Suite de tests complète** avec pytest (80+ tests)
  - Tests de validation (12 tests)
  - Tests de configuration (8 tests)
  - Tests de dispatch (10 tests)
  - Tests de métriques (12 tests)
- Coverage > 80%
- Fixtures réutilisables

#### CI/CD & Automatisation
- **GitHub Actions workflow** complet
  - Lint (Black, isort, Flake8, Pylint, Mypy)
  - Tests multi-versions Python (3.8-3.12)
  - Security scan (Bandit, Safety)
  - Validation de configuration
  - Build de package
- **Pre-commit hooks** configurés
- **pyproject.toml** pour configuration centralisée

#### MCP & Documentation
- **Schémas JSON complets** dans `mcp_servers.json.template`
  - Input schemas avec validation
  - Output schemas
  - Descriptions détaillées
  - Exemples d'utilisation
- Agent `health_check` documenté

#### Fichiers de Projet
- `requirements.txt` - Dépendances de production
- `requirements-dev.txt` - Outils de développement
- `setup.py` & `pyproject.toml` - Configuration de package
- `.gitignore` - Exclusions Git
- `.env.example` - Template de configuration
- `.pre-commit-config.yaml` - Hooks de pre-commit
- `CHANGELOG.md` - Ce fichier

### 🔧 Modifié

#### Code Core
- **Refactorisation complète de `bridge.py`** (265 → 674 lignes)
  - Architecture modulaire avec classes
  - Séparation des responsabilités
  - Type hints ajoutés
  - Documentation améliorée
- **Suppression des imports inutilisés** (`functools.lru_cache`)
- **Gestion d'erreurs améliorée**
  - JSON invalide retourne maintenant une erreur
  - Messages d'erreur plus détaillés
  - Logging contextualisé

#### Performance
- Validation des paramètres avant exécution des agents
- Métriques collectées en temps réel
- Timeouts adaptés par agent (180s à 600s selon le type)

### 🐛 Corrigé

- **Sécurité**: Paramètres non validés passés directement aux commandes shell
- **Logs**: Fichier de log pouvait grossir indéfiniment sans rotation
- **Erreurs**: JSON invalide retournait `success` au lieu de `error`
- **Configuration**: Chemins hardcodés empêchaient la personnalisation
- **Code mort**: Import `lru_cache` jamais utilisé

### 🔒 Sécurité

- Validation stricte des entrées utilisateur
- Sanitisation des chaînes pour prévenir les injections
- Limites de taille des payloads
- Timeouts pour éviter les blocages
- Scan de sécurité automatisé (Bandit)
- Audit des dépendances (Safety)

### 📚 Documentation

- CHANGELOG détaillé (ce fichier)
- README amélioré avec exemples de configuration
- Docstrings complètes dans le code
- Schémas MCP avec exemples
- Guide de contribution
- Template de variables d'environnement

### 🔄 Compatibilité

- **Python**: 3.8+ (testé sur 3.8, 3.9, 3.10, 3.11, 3.12)
- **Rétrocompatibilité**: ✅ Fonctionne sans config.yaml (utilise defaults)
- **Dépendances**: PyYAML optionnel (fallback vers configuration par défaut)

---

## [0.1.0] - 2025-11-04

### ✨ Version Initiale

- Bridge STDIO basique pour 4 agents ADK
- Support CLI direct et mode STDIO
- Configuration hardcodée
- Logging basique
- Documentation README

---

## Légende

- ✨ **Ajouté** : Nouvelles fonctionnalités
- 🔧 **Modifié** : Changements dans les fonctionnalités existantes
- 🐛 **Corrigé** : Corrections de bugs
- 🔒 **Sécurité** : Correctifs de sécurité
- 📚 **Documentation** : Améliorations de documentation
- 🔄 **Compatibilité** : Informations de compatibilité
- ⚠️ **Déprécié** : Fonctionnalités obsolètes (à supprimer)
- 🗑️ **Supprimé** : Fonctionnalités supprimées
