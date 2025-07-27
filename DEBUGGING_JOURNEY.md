# 🔧 Parcours de Débogage - Intégration Protocole MCP

## 🎯 Problème Identifié

Les agents ADK étaient fonctionnels en appel direct mais **n'apparaissaient pas dans `/mcp list`** de Gemini CLI.

## 🔍 Diagnostic

### Symptômes
- ✅ Bridge répond aux appels directs : `echo '{"tool":"watch_collect","params":{}}' | python bridge.py`
- ❌ Agents invisibles dans Gemini CLI : `/mcp list` ne les affiche pas
- ❌ Serveurs marqués comme `🔴 Disconnected`

### Cause Racine
Le bridge ne parlait que le format personnalisé `{"tool":"nom","params":{}}` mais **pas le protocole MCP standard**.

Gemini CLI envoie toujours au démarrage :
1. `{"method":"initialize"}` → Hand-shake
2. `{"method":"tools/list"}` → Catalogue des outils

Sans ces réponses, Gemini CLI marque le serveur comme déconnecté.

## 🛠️ Solutions Appliquées

### 1. Cache MCP Vidé
```bash
rm -rf ~/.gemini/cache/mcp
```

### 2. Correction Python Path
**Problème** : `/usr/bin/python3` vs `pyenv`
**Solution** : Utiliser `/Users/sahebmlik/.pyenv/shims/python3`

### 3. Ajout des Logs
```json
{
  "watch_collect": {
    "command": "/Users/sahebmlik/.pyenv/shims/python3",
    "args": ["-u", "/Users/sahebmlik/.gemini/bridge.py", "watch_collect"],
    "stdout": "/Users/sahebmlik/.gemini/bridge.log",
    "stderr": "/Users/sahebmlik/.gemini/bridge.log"
  }
}
```

### 4. **Intégration Protocole MCP** ⭐

#### A. Catalogue des Outils
```python
AVAILABLE_TOOLS = {
    "watch_collect": {"description": "Surveillance GitHub/PyPI/NPM pour collecter les nouveautés tech"},
    "analyse_watch_report": {"description": "Analyse Gemini du rapport de veille markdown"},
    "curate_digest": {"description": "Génération newsletter + threads sociaux à partir de l'analyse"},
    "label_github_issue": {"description": "Étiquetage automatique d'issues GitHub"}
}
```

#### B. Dispatcher JSON-RPC
```python
def dispatch_rpc(request: dict):
    method = request.get("method")
    
    # 1️⃣ Hand-shake
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}

    # 2️⃣ Catalogue des outils
    if method == "tools/list":
        tools = [
            {
                "name": name,
                "description": meta["description"],
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            }
            for name, meta in AVAILABLE_TOOLS.items()
        ]
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {"tools": tools}}

    # 3️⃣ Appels réels envoyés par run_tool
    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        result = dispatch(tool_name, tool_args)
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "content": [{"type": "text", "text": json.dumps(result)}]
            }
        }
```

#### C. Boucle STDIO Hybride
```python
# Support both JSON-RPC (MCP) and legacy format
if "method" in payload:
    # JSON-RPC format (MCP protocol)
    result = dispatch_rpc(payload)
else:
    # Legacy format for backward compatibility
    tool = payload.get("tool")
    params = payload.get("params", {})
    result = dispatch(tool, params)
```

## ✅ Tests de Validation

### Initialize Protocol
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python bridge.py
# → {"jsonrpc": "2.0", "id": 1, "result": {}}
```

### Tools Listing
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python bridge.py
# → {"jsonrpc": "2.0", "id": 2, "result": {"tools": [...]}}
```

## 📋 Checklist Final

- [x] Cache MCP vidé
- [x] Python path corrigé (pyenv)
- [x] Logs configurés
- [x] Protocole MCP `initialize` implémenté
- [x] Protocole MCP `tools/list` implémenté
- [x] Protocole MCP `tools/call` implémenté
- [x] Rétrocompatibilité format legacy préservée
- [x] Tests protocole validés

## 🚀 Résultat Attendu

Après redémarrage de Gemini CLI :
```
/mcp list
🟢 watch_collect
🟢 analyse_watch_report  
🟢 curate_digest
🟢 label_github_issue
```

## 📚 Apprentissages

1. **MCP = JSON-RPC** : Protocole standardisé, pas format personnalisé
2. **Cache Impact** : Vider le cache MCP essentiel après modifications
3. **Python Path** : pyenv vs système, importance du bon chemin
4. **Debugging** : Logs cruciaux pour identifier les erreurs de communication
5. **Backward Compatibility** : Maintenir support legacy pendant transition

---
*Session de debugging complétée le 27 juillet 2025*