# Fix Protocol Version 2025-02-01 - Corrections Critiques MCP

## 🎯 Objectif
Résoudre les problèmes d'affichage des agents ADK dans `/mcp list` de Gemini CLI en corrigeant les incompatibilités de protocole.

## 🔍 Problèmes Identifiés

### 1. Version Protocole Obsolète
- **Avant** : `protocolVersion: "2024-11-05"`
- **Après** : `protocolVersion: "2025-02-01"`
- **Impact** : Gemini CLI ≥ v0.7 attend la version février 2025

### 2. ServerInfo Incomplet
- **Avant** : Seulement `name` et `version`
- **Après** : Ajout du champ `description`
- **Impact** : Parsing UI amélioré

### 3. InputSchemas Vides
- **Avant** : `{"type": "object", "properties": {}, "required": []}`
- **Après** : Schémas complets avec propriétés typées
- **Impact** : CLI ignore les tools sans schéma détaillé

### 4. Mélange Stdout/Stderr
- **Avant** : `stdout` et `stderr` vers même fichier
- **Après** : Seulement `stderr` configuré
- **Impact** : Parser JSON-RPC plus stable

## ✅ Corrections Appliquées

### Bridge.py - Handshake Initialize
```python
# AVANT
"protocolVersion": "2024-11-05",
"serverInfo": {
    "name": "adk-gemini-bridge",
    "version": "1.0.0"
}

# APRÈS  
"protocolVersion": "2025-02-01",
"serverInfo": {
    "name": "adk-gemini-bridge", 
    "version": "1.0.0",
    "description": "ADK Agents Bridge - 4 tools for tech watch, analysis, curation, and GitHub labeling"
}
```

### Bridge.py - InputSchemas Détaillés
```python
# Exemple: watch_collect
{
    "type": "object",
    "properties": {
        "sources": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Sources à surveiller (github, pypi, npm)",
            "default": ["github", "pypi", "npm"]
        },
        "output_format": {
            "type": "string", 
            "description": "Format de sortie",
            "default": "markdown"
        }
    },
    "required": []
}
```

### mcp_servers.json - Configuration Optimisée
```json
// AVANT
{
    "stdout": "/Users/sahebmlik/.gemini/bridge.log",
    "stderr": "/Users/sahebmlik/.gemini/bridge.log"
}

// APRÈS
{
    "stderr": "/Users/sahebmlik/.gemini/bridge.log"
}
```

## 🧪 Tests de Validation

### Initialize Handshake
```bash
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | python3 bridge.py
# ✅ Retourne protocolVersion: 2025-02-01
```

### Tools Catalog
```bash
echo '{"jsonrpc":"2.0","method":"tools/list","id":2}' | python3 bridge.py  
# ✅ Retourne 4 outils avec schémas complets
```

## 🎯 Résultat Attendu

```bash
/mcp list
🟢 adk-gemini-bridge - ADK Agents Bridge - 4 tools for tech watch, analysis, curation, and GitHub labeling
    ├─ watch_collect - Surveillance GitHub/PyPI/NPM pour collecter les nouveautés tech
    ├─ analyse_watch_report - Analyse Gemini du rapport de veille markdown  
    ├─ curate_digest - Génération newsletter + threads sociaux à partir de l'analyse
    └─ label_github_issue - Étiquetage automatique d'issues GitHub
```

## 📋 Checklist Pre-Test
- [x] Cache MCP vidé : `rm -rf ~/.gemini/cache/mcp`
- [x] Bridge validé en direct
- [x] Configuration MCP mise à jour
- [x] Logs stderr séparés

## 🔄 Prochaines Étapes
1. **Test final** : `/mcp list` dans Gemini CLI
2. **Validation fonctionnelle** : `run_tool watch_collect`
3. **Pipeline A2A** : Tests chaînés watch → analyse → curate → label

---
**Branche** : `fix-protocol-version-2025`  
**Status** : ✅ Corrections appliquées - Prêt pour test final