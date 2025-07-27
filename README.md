# 🤖 ADK-Gemini CLI Bridge

Bridge pour connecter les Agents ADK (Agent Development Kit) à Gemini CLI, permettant l'orchestration A2A (Agent-to-Agent) entre les agents spécialisés.

## 🎯 Vue d'ensemble

Ce projet implémente une solution bridge qui expose 4 agents ADK comme outils utilisables dans Gemini CLI via le protocole MCP (Model Context Protocol). Il permet l'orchestration automatisée entre :

- **🔍 Watch Agent** - Collecte de veille technologique
- **🧠 Analysis Agent** - Analyse des rapports avec Gemini
- **📝 Curator Agent** - Curation de contenu (newsletter/thread)
- **🏷️ GitHub Labeler Agent** - Étiquetage automatique d'issues

## 🏗️ Architecture

```
ADK Agents ↔ bridge.py ↔ Gemini CLI ↔ Claude Code
```

- **Communication STDIO** : Interface standardisée entre Gemini CLI et les agents
- **Environnements virtuels** : Chaque agent utilise son propre environnement Python
- **Gestion d'erreurs robuste** : Logs centralisés et timeouts configurables
- **Modes d'exécution** : CLI direct et STDIO pour intégration MCP

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

# Copier le bridge vers le répertoire Gemini
cp bridge.py ~/.gemini/bridge.py
chmod +x ~/.gemini/bridge.py
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
```

### Via CLI direct

```bash
# Test direct du bridge
python3 ~/.gemini/bridge.py watch_collect '{"sources":["github"]}'

# Mode STDIO
echo '{"tool":"watch_collect","params":{"sources":["github"]}}' | python3 -u ~/.gemini/bridge.py
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

## 🔧 Configuration

### Variables d'environnement

```bash
# Pour GitHub Labeler Agent
export GITHUB_TOKEN="your_github_token"

# Pour Gemini Analysis Agent  
export GEMINI_API_KEY="your_gemini_api_key"
```

### Logs

Les logs sont centralisés dans :
```
~/.gemini/bridge.log
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

## 🤝 Contribution

1. Fork le repository
2. Créer une branche feature : `git checkout -b feature/amazing-feature`
3. Commit les changements : `git commit -m 'Add amazing feature'`
4. Push vers la branche : `git push origin feature/amazing-feature`
5. Ouvrir une Pull Request

## 📋 Roadmap

- [ ] Support pour plus d'agents ADK
- [ ] Interface web de monitoring
- [ ] Métriques et analytics des agents
- [ ] Configuration dynamique des agents
- [ ] Support Docker pour déploiement

## 📄 Licence

MIT License - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🔗 Liens utiles

- [Gemini CLI Documentation](https://github.com/google-gemini/gemini-cli)
- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [ADK Framework Documentation](link-to-adk-docs)

---

**Développé avec ❤️ pour l'écosystème A2A (Agent-to-Agent)**