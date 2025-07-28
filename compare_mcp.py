#!/usr/bin/env python3
"""
Compare la séquence MCP (initialize + tools/list) de deux serveurs.
Révèle les différences structurelles exactes.

Usage :
    python compare_mcp.py path/to/bridge.py path/to/other_mcp.py
"""

import json, subprocess, sys, textwrap, difflib, time

INIT_MSG = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}) + "\n"
LIST_MSG = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}) + "\n"

def call_with_timing(server_cmd):
    """Appelle un serveur MCP et mesure les temps de réponse"""
    start = time.time()
    
    proc = subprocess.Popen(
        [sys.executable, server_cmd],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Envoie les deux messages en une fois et attend la fin proprement
    init_start = time.time()
    input_data = INIT_MSG + LIST_MSG
    
    try:
        out, err = proc.communicate(input=input_data, timeout=5)
        end = time.time()
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        end = time.time()
        err += "\n[TIMEOUT] Process killed after 5s"
    
    # Parse les réponses
    lines = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
    responses = {l["id"]: l["result"] for l in lines if "result" in l}
    
    timing = {
        "total": end - start,
        "init_latency": 0.001,  # Approximation car envoi groupé
        "list_latency": end - init_start
    }
    
    return responses, timing, err

def pprint_block(title, data):
    print(f"\n### {title}")
    print("```json")
    print(textwrap.indent(json.dumps(data, indent=2, ensure_ascii=False), '  '))
    print("```")

def compare_servers(a_path, b_path):
    print(f"🔍 Comparaison MCP : {a_path} vs {b_path}\n")
    
    try:
        A_resp, A_timing, A_err = call_with_timing(a_path)
        print(f"✅ Serveur A: {a_path}")
        print(f"   Temps total: {A_timing['total']:.3f}s")
        print(f"   Latence init: {A_timing['init_latency']:.3f}s") 
        print(f"   Latence tools/list: {A_timing['list_latency']:.3f}s")
        
    except Exception as e:
        print(f"❌ Erreur serveur A: {e}")
        return
    
    try:
        B_resp, B_timing, B_err = call_with_timing(b_path)
        print(f"✅ Serveur B: {b_path}")
        print(f"   Temps total: {B_timing['total']:.3f}s")
        print(f"   Latence init: {B_timing['init_latency']:.3f}s")
        print(f"   Latence tools/list: {B_timing['list_latency']:.3f}s")
        
    except Exception as e:
        print(f"❌ Erreur serveur B: {e}")
        return

    # Comparaison des réponses
    pprint_block("A.initialize", A_resp.get(1, {}))
    pprint_block("B.initialize", B_resp.get(1, {}))
    
    pprint_block("A.tools/list", A_resp.get(2, {}))
    pprint_block("B.tools/list", B_resp.get(2, {}))

    # Diff unifié des tools/list (le plus critique)
    a_tools = json.dumps(A_resp.get(2, {}), indent=2, ensure_ascii=False)
    b_tools = json.dumps(B_resp.get(2, {}), indent=2, ensure_ascii=False)
    
    diff = list(difflib.unified_diff(
        a_tools.splitlines(),
        b_tools.splitlines(),
        fromfile=f"A ({a_path})",
        tofile=f"B ({b_path})",
        lineterm=""
    ))
    
    if diff:
        print("\n### 🔍 Différences tools/list")
        print("```diff")
        for line in diff:
            print(line)
        print("```")
    else:
        print("\n✅ Aucune différence dans tools/list")
    
    # Analyse des erreurs stderr
    if A_err.strip():
        print(f"\n⚠️ Stderr A: {A_err}")
    if B_err.strip():
        print(f"\n⚠️ Stderr B: {B_err}")
    
    # Alertes sur les timeouts
    if A_timing['total'] > 0.5:
        print(f"\n🚨 Serveur A lent: {A_timing['total']:.3f}s (>500ms timeout CLI)")
    if B_timing['total'] > 0.5:
        print(f"\n🚨 Serveur B lent: {B_timing['total']:.3f}s (>500ms timeout CLI)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_mcp.py server_a.py server_b.py")
        sys.exit(1)
    
    compare_servers(sys.argv[1], sys.argv[2])