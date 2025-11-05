# 🤖 ADK-Gemini CLI Bridge

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Bridge production-ready pour connecter les Agents ADK (Agent Development Kit) à Gemini CLI, permettant l'orchestration A2A (Agent-to-Agent) entre agents spécialisés.

## ✨ Fonctionnalités

- 🔒 **Sécurité renforcée** - Validation stricte des paramètres, sanitisation, protection contre les injections
- ⚙️ **Configuration flexible** - YAML externe + variables d'environnement
- 📊 **Monitoring intégré** - Métriques, health checks, rotation des logs
- ✅ **Tests complets** - Suite de 80+ tests avec coverage > 80%
- 🚀 **CI/CD ready** - GitHub Actions, pre-commit hooks, linting automatique
- 📖 **Documentation complète** - Schémas MCP JSON, docstrings, exemples

## 🎯 Vue d'ensemble

Ce projet implémente une solution bridge qui expose 5 agents ADK comme outils utilisables dans Gemini CLI via le protocole MCP (Model Context Protocol). Il permet l'orchestration automatisée entre :

- **🔍 Watch Agent** - Collecte de veille technologique
- **🧠 Analysis Agent** - Analyse des rapports avec Gemini
- **📝 Curator Agent** - Curation de contenu (newsletter/thread)
- **🏷️ GitHub Labeler Agent** - Étiquetage automatique d'issues
- **🩺 Health Check** - Monitoring et métriques en temps réel

## 🏗️ Architecture

```
ADK Agents ↔ bridge.py ↔ Gemini CLI ↔ Claude Code
                ↓
         Config (YAML)
                ↓
    Validation → Logging → Metrics
```

### Caractéristiques Techniques

- **Communication STDIO** : Interface standardisée entre Gemini CLI et les agents
- **Isolation** : Chaque agent utilise son propre environnement Python
- **Sécurité** : Validation des paramètres avec regex, type checking, sanitisation
- **Observabilité** : Logs rotatifs (10MB max), métriques par agent, health checks
- **Configuration** : YAML externe avec fallback vers defaults intégrés
- **Modes d'exécution** : CLI direct + STDIO pour intégration MCP

## 🚀 Installation

### 1. Prérequis

- Python 3.8+
- Gemini CLI installé et configuré
- Workspace ADK avec les 4 agents dans `~/adk-workspace/`

### 2. Installation du Bridge

```bash
# Cloner le repository
git clone https://github.com/mlik-sudo/adk-gemini-cli-bridge.git
cd adk-gemini-cli-bridge

# Installer les dépendances
pip install -r requirements.txt

# Copier les fichiers vers le répertoire Gemini
cp bridge.py ~/.gemini/bridge.py
cp config.yaml ~/.gemini/config.yaml
chmod +x ~/.gemini/bridge.py

# Optionnel : Configurer les variables d'environnement
cp .env.example .env
nano .env
```

### 3. Configuration MCP

Ajouter les agents au fichier `~/.gemini/mcp_servers.json` :

```bash
# Fusionner avec votre configuration existante
cat mcp_servers.json.template >> ~/.gemini/mcp_servers.json
```

Ou copier manuellement les entrées du template dans votre fichier de configuration.

### 4. Structure ADK attendue

```
~/adk-workspace/
├── github_labeler/
│   ├── main.py
│   └── requirements.txt
├── veille_agent/
│   ├── main.py
│   ├── .venv/          # Environnement virtuel spécifique
│   └── requirements.txt
├── gemini_analysis/
│   ├── main.py
│   └── requirements.txt
├── curateur_agent/
│   ├── main.py
│   └── requirements.txt
└── adk-env/            # Environnement virtuel global
    └── bin/python
```

## 📖 Utilisation

### Via Gemini CLI

```bash
# Démarrer Gemini CLI
gemini

# Vérifier que les agents sont disponibles
/mcp list

# Utiliser les agents
run_tool watch_collect {"sources":["github","pypi"]}
run_tool analyse_watch_report {"report_path":"/path/to/report.md"}
run_tool curate_digest {"format":"newsletter"}
run_tool label_github_issue {"repo_name":"owner/repo","issue_number":123}

# Vérifier la santé du bridge
run_tool health_check {}
```

### Via CLI direct

```bash
# Test direct du bridge
python3 ~/.gemini/bridge.py watch_collect '{"sources":["github"]}'

# Health check
python3 ~/.gemini/bridge.py health_check '{}'

# Mode STDIO
echo '{"tool":"watch_collect","params":{"sources":["github"]}}' | python3 -u ~/.gemini/bridge.py
```

### Health Check & Monitoring

Le bridge expose un endpoint `health_check` pour monitorer l'état :

```bash
python3 bridge.py health_check '{}'
```

**Sortie exemple** :
```json
{
  "status": "success",
  "health": {
    "status": "healthy",
    "total_calls": 42,
    "total_errors": 2,
    "error_rate": 0.047,
    "agents": {
      "watch_collect": {
        "calls": 15,
        "success_rate": 0.933,
        "avg_duration": 45.2
      },
      "label_github_issue": {
        "calls": 10,
        "success_rate": 1.0,
        "avg_duration": 2.1
      }
    }
  }
}
```

## 🛠️ Agents disponibles

### 🔍 watch_collect
**Collecte de veille technologique**

Paramètres :
- `sources` (optionnel) : Sources à surveiller `["github", "pypi", "npm"]`
- `output_format` (optionnel) : Format de sortie `"markdown"`

Exemple :
```json
{"sources": ["github", "pypi"], "output_format": "markdown"}
```

### 🧠 analyse_watch_report
**Analyse de rapports avec Gemini**

Paramètres :
- `report` : Contenu du rapport (texte)
- `report_path` : Chemin vers le fichier rapport

Exemple :
```json
{"report_path": "/Users/user/adk-workspace/veille_agent/rapport_veille.md"}
```

### 📝 curate_digest
**Curation de contenu**

Paramètres :
- `format` (optionnel) : Format de sortie `"newsletter"`
- `output` (optionnel) : Type de sortie `"markdown"`

Exemple :
```json
{"format": "newsletter", "output": "markdown"}
```

### 🏷️ label_github_issue
**Étiquetage automatique GitHub**

Paramètres :
- `repo_name` : Repository `"owner/repo"`
- `issue_number` : Numéro de l'issue
- `dry_run` (optionnel) : Mode simulation `true/false` (défaut: `true`)

Exemple :
```json
{"repo_name": "facebook/react", "issue_number": 123, "dry_run": false}
```

### 🩺 health_check
**Monitoring et métriques**

Retourne l'état de santé du bridge et les métriques de tous les agents.

Paramètres :
- Aucun

Exemple :
```bash
python3 bridge.py health_check '{}'
```

Sortie :
```json
{
  "status": "success",
  "health": {
    "status": "healthy",
    "total_calls": 42,
    "error_rate": 0.047,
    "agents": { ... }
  }
}
```

## 🔧 Configuration

### Configuration YAML

Le bridge utilise `config.yaml` pour la configuration. Par défaut, il cherche le fichier dans le même répertoire que `bridge.py`.

```yaml
# config.yaml
workspace:
  path: ~/adk-workspace  # Personnalisable

logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file: ~/.gemini/bridge.log
  rotation:
    enabled: true
    max_bytes: 10485760  # 10 MB
    backup_count: 5

agents:
  watch_collect:
    timeout: 600  # Secondes
    defaults:
      sources: ["github", "pypi", "npm"]

security:
  validate_inputs: true
  max_param_length: 10000

performance:
  collect_metrics: true
```

### Variables d'environnement

Les variables d'environnement ont priorité sur le fichier YAML :

```bash
# Configuration du bridge
export ADK_WORKSPACE="~/adk-workspace"
export BRIDGE_LOG_LEVEL="DEBUG"
export BRIDGE_LOG_FILE="~/.gemini/bridge.log"

# API Keys pour les agents
export GITHUB_TOKEN="your_github_token"
export GEMINI_API_KEY="your_gemini_api_key"
```

### Logs

**Logs rotatifs automatiques** :
- Fichier : `~/.gemini/bridge.log`
- Taille max : 10 MB par fichier
- Backup : 5 fichiers conservés
- Format : `[2025-11-05 10:30:45] INFO [bridge]: Message`

**Consulter les logs** :
```bash
# Dernières lignes
tail -f ~/.gemini/bridge.log

# Rechercher des erreurs
grep ERROR ~/.gemini/bridge.log

# Logs d'un agent spécifique
grep "watch_collect" ~/.gemini/bridge.log
```

## 🐛 Dépannage

### Erreur "Python interpreter not found"

Vérifiez que les environnements virtuels existent :
```bash
ls -la ~/adk-workspace/veille_agent/.venv/bin/python
ls -la ~/adk-workspace/adk-env/bin/python
```

### Erreur "Agent script not found"

Vérifiez la structure du workspace ADK :
```bash
ls -la ~/adk-workspace/*/main.py
```

### MCP servers not appearing

Redémarrez Gemini CLI et vérifiez :
```bash
gemini
/mcp list
```

## 🧪 Tests

Le projet inclut une suite complète de tests unitaires :

```bash
# Installer les dépendances de développement
pip install -r requirements-dev.txt

# Exécuter tous les tests
pytest tests/ -v

# Avec coverage
pytest tests/ --cov=bridge --cov-report=html

# Tests spécifiques
pytest tests/test_validation.py -v
```

**Coverage actuel** : > 80%

## 🚀 Développement

### Installation pour le développement

```bash
# Cloner et installer
git clone https://github.com/mlik-sudo/adk-gemini-cli-bridge.git
cd adk-gemini-cli-bridge

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Installer avec les dépendances dev
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Installer les pre-commit hooks
pre-commit install
```

### Vérification du code

```bash
# Formater le code
black bridge.py tests/
isort bridge.py tests/

# Linting
flake8 bridge.py tests/ --max-line-length=120
pylint bridge.py

# Type checking
mypy bridge.py --ignore-missing-imports

# Security scan
bandit -r bridge.py
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez [CONTRIBUTING.md](CONTRIBUTING.md) pour les détails.

1. Fork le repository
2. Créer une branche feature : `git checkout -b feature/amazing-feature`
3. Commit les changements : `git commit -m 'feat: add amazing feature'`
4. Pusher vers la branche : `git push origin feature/amazing-feature`
5. Ouvrir une Pull Request

## 📋 Roadmap

- [x] ~~Configuration YAML externe~~
- [x] ~~Validation stricte des paramètres~~
- [x] ~~Système de métriques~~
- [x] ~~Tests unitaires complets~~
- [x] ~~CI/CD avec GitHub Actions~~
- [ ] Interface web de monitoring
- [ ] Support pour plus d'agents ADK
- [ ] Authentification/autorisation
- [ ] Rate limiting par agent
- [ ] Cache de résultats

## 📄 Licence

MIT License - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📚 Documentation

- [CHANGELOG](CHANGELOG.md) - Historique des versions
- [CONTRIBUTING](CONTRIBUTING.md) - Guide de contribution
- [LICENSE](LICENSE) - Licence MIT

## 🔗 Liens utiles

- [Gemini CLI Documentation](https://github.com/google-gemini/gemini-cli)
- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [ADK Framework Documentation](https://github.com/anthropics/anthropic-sdk-python)

## 📊 Statistiques du Projet

- **Lignes de code** : ~674 (bridge.py)
- **Tests** : 80+ tests unitaires
- **Coverage** : > 80%
- **Python supporté** : 3.8, 3.9, 3.10, 3.11, 3.12
- **Dépendances** : 1 (PyYAML)

## ⭐ Support

Si ce projet vous est utile, n'hésitez pas à lui donner une ⭐ sur GitHub !

---

**Développé avec ❤️ pour l'écosystème A2A (Agent-to-Agent)**