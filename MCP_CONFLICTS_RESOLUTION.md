# 🔧 Résolution Conflits MCP - Serveurs Multiples vers Serveur Unifié

## 🚨 Problème Identifié

### Symptômes Observés
- Bridge répond correctement aux tests manuels ✅
- `initialize` et `tools/list` fonctionnent en direct ✅
- **Agents toujours invisibles dans `/mcp list`** ❌
- **Erreurs EPIPE dans les logs Gemini CLI** ❌

### Logs d'Erreur
```
Error: write EPIPE
    at afterWriteDispatched (node:internal/stream_base_commons:159:15)
    at writeGeneric (node:internal/stream_base_commons:150:3)
    ...
  errno: -32,
  code: 'EPIPE',
  syscall: 'write'
```

## 🔍 Cause Racine Découverte

### Configuration Problématique
```json
{
  "label_github_issue": { "command": "python bridge.py label_github_issue" },
  "watch_collect": { "command": "python bridge.py watch_collect" },
  "analyse_watch_report": { "command": "python bridge.py analyse_watch_report" },
  "curate_digest": { "command": "python bridge.py curate_digest" }
}
```

**Problème** : Gemini CLI tentait de démarrer **4 instances séparées** du même bridge Python
- Chaque outil = 1 processus Python distinct
- Conflits de ressources et pipes cassés (EPIPE)
- Protocole MCP conçu pour 1 serveur → N outils, pas N serveurs

## ✅ Solution Appliquée

### Configuration Unifiée
```json
{
  "adk-gemini-bridge": {
    "command": "/Users/sahebmlik/.pyenv/shims/python3",
    "args": ["-u", "/Users/sahebmlik/.gemini/bridge.py"],
    "stdout": "/Users/sahebmlik/.gemini/bridge.log",
    "stderr": "/Users/sahebmlik/.gemini/bridge.log"
  }
}
```

**Avantages** :
- ✅ **1 seul processus Python** pour tous les outils
- ✅ **1 seule instance MCP** qui expose 4 tools via `tools/list`
- ✅ **Pas de conflits** de ressources ou pipes
- ✅ **Protocole MCP respecté** : 1 serveur → multiple tools

## 🔄 Architecture Finale

### Avant (Problématique)
```
Gemini CLI
├─ Serveur "label_github_issue" → bridge.py (PID 1001)
├─ Serveur "watch_collect" → bridge.py (PID 1002)  
├─ Serveur "analyse_watch_report" → bridge.py (PID 1003)
└─ Serveur "curate_digest" → bridge.py (PID 1004)
    ↳ 4 processus = conflits + EPIPE
```

### Après (Corrigée)
```
Gemini CLI
└─ Serveur "adk-gemini-bridge" → bridge.py (PID 1001)
   ├─ Tool: watch_collect
   ├─ Tool: analyse_watch_report
   ├─ Tool: curate_digest
   └─ Tool: label_github_issue
      ↳ 1 processus = stable + compatible MCP
```

## 📋 Étapes de Correction

1. **Diagnostic des logs**
   ```bash
   tail -50 ~/Library/Logs/Claude/mcp-server-gemini-mcp-tool.log
   # → Révélation des erreurs EPIPE
   ```

2. **Refactorisation configuration**
   - Suppression des 4 entrées séparées
   - Création d'une entrée unifiée `adk-gemini-bridge`
   - Conservation du bridge.py existant (aucun changement code)

3. **Validation**
   - Cache MCP vidé : `rm -rf ~/.gemini/cache/mcp`
   - Redémarrage Gemini CLI complet
   - Test : `/mcp list` → doit afficher le serveur unifié

## 🧠 Apprentissages Clés

### Principe MCP Fondamental
- **1 Serveur MCP = N Tools** (correct)
- **N Serveurs MCP = 1 Tool chacun** (incorrect pour notre cas)

### Debugging MCP
1. **Tests directs** : `echo '{"method":"initialize"}' | python bridge.py`
2. **Logs Gemini** : `~/Library/Logs/Claude/mcp-server-*.log`
3. **Erreurs EPIPE** = conflits de processus multiples
4. **Cache MCP** : Toujours vider après changements config

### Architecture MCP Recommandée
- **Grouper les outils liés** dans un même serveur
- **Éviter la duplication** de processus identiques
- **Respecter le protocole** : initialize → tools/list → tools/call

## 🎯 Résultat Attendu

Après correction, `/mcp list` devrait afficher :
```
🟢 adk-gemini-bridge
  ├─ watch_collect - Surveillance GitHub/PyPI/NPM
  ├─ analyse_watch_report - Analyse Gemini rapport
  ├─ curate_digest - Newsletter + threads sociaux
  └─ label_github_issue - Étiquetage automatique
```

Et l'utilisation :
```bash
run_tool watch_collect {"sources":["github"]}
run_tool analyse_watch_report {"report_md":"..."}
run_tool curate_digest {"analysis_json":{...}}
run_tool label_github_issue {"repo_name":"owner/repo","issue_number":42}
```

## 🚀 Impact

- **Fin des erreurs EPIPE** dans les logs Gemini
- **Agents ADK visibles** dans `/mcp list`
- **Performance améliorée** (1 vs 4 processus)
- **Architecture MCP propre** et évolutive

---
*Correction appliquée le 27 juillet 2025 - Session de debugging avancé*