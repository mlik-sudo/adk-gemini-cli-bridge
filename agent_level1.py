# agent_level1.py

# Importations des modules nécessaires
from pathlib import Path
import sys 
import subprocess
import os 
import google.generativeai as genai 

# --- Configuration Clé API ---
# Lire la clé API depuis la variable d'environnement
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Variable globale pour savoir si l'API est configurée
api_configured_ok = False 

# Configuration du modèle si la clé a été trouvée dans l'environnement
if GEMINI_API_KEY:
     try:
         genai.configure(api_key=GEMINI_API_KEY)
         print("INFO: Clé API Gemini chargée depuis l'environnement.")
         api_configured_ok = True # Marquer comme configuré
     except Exception as e:
         print(f"ERREUR: Erreur lors de la configuration de l'API Gemini : {e}", file=sys.stderr)
         # GEMINI_API_KEY reste None ou la valeur initiale, api_configured_ok reste False
else:
     print("ATTENTION: Variable d'environnement GOOGLE_API_KEY non définie.", file=sys.stderr)
     print("           Vous devez la définir dans le terminal avant de lancer le script:", file=sys.stderr)
     print("           export GOOGLE_API_KEY=\"VOTRE_CLE_API_ICI\"", file=sys.stderr)


# --- Définition des Fonctions de l'Agent ---

def read_local_file(file_path_str):
    """Lit le contenu textuel d'un fichier local."""
    try:
        file_path = Path(file_path_str)
        if not file_path.is_file():
            print(f"Erreur : Le fichier '{file_path_str}' n'a pas été trouvé ou n'est pas un fichier.", file=sys.stderr)
            return None
        try:
            content = file_path.read_text(encoding='utf-8')
            # Commenter le print de succès si trop verbeux pour l'usage final
            # print(f"Fichier '{file_path_str}' lu avec succès.")
            return content
        except PermissionError:
            print(f"Erreur : Permission refusée pour lire le fichier '{file_path_str}'.", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Erreur inattendue lors de la lecture de '{file_path_str}': {e}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Erreur lors de la manipulation du chemin '{file_path_str}': {e}", file=sys.stderr)
        return None


def run_local_script(script_path):
    """Exécute un script local et capture sa sortie."""
    try:
        # Assurer que le script est exécutable (important sur Mac/Linux)
        script_obj = Path(script_path)
        if not script_obj.is_file() or not os.access(script_obj, os.X_OK):
             # Essayer de le rendre exécutable si ce n'est pas le cas
             try:
                 subprocess.run(["chmod", "+x", script_path], check=True)
                 print(f"INFO: Ajout permission d'exécution pour '{script_path}'.")
             except Exception as chmod_e:
                  print(f"Erreur: Impossible de rendre le script '{script_path}' exécutable : {chmod_e}", file=sys.stderr)
                  return -1, "", f"Permission d'exécution manquante ou erreur chmod: {script_path}"

        # Exécuter le script avec bash
        result = subprocess.run(["bash", script_path], capture_output=True, text=True, check=False, encoding='utf-8')
        # Commenter les prints si trop verbeux
        # print(f"Script '{script_path}' exécuté avec code retour {result.returncode}.")
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        print(f"Erreur : Le script '{script_path}' est introuvable.", file=sys.stderr)
        return -1, "", f"Script non trouvé : {script_path}"
    except Exception as e:
        print(f"Erreur inattendue lors de l'exécution de '{script_path}' : {e}", file=sys.stderr)
        return -1, "", str(e)


def call_gemini(prompt_text):
    """Envoie un prompt à l'API Gemini et retourne la réponse textuelle."""
    global api_configured_ok # Utilise la variable globale définie lors de la configuration
    if not api_configured_ok:
        error_msg = "Erreur: Clé API non configurée ou configuration échouée."
        # print(error_msg, file=sys.stderr) # Déjà affiché lors de la config
        return error_msg

    try:
        model = genai.GenerativeModel('gemini-1.5-flash') 
        response = model.generate_content(prompt_text)
        # Gestion plus robuste de la réponse
        if response and response.parts:
             return "".join(part.text for part in response.parts if hasattr(part, 'text'))
        elif hasattr(response, 'text'): # Fallback pour les modèles plus anciens/simples
             return response.text
        else:
             # Tenter d'inspecter les erreurs potentielles ou retourner un message générique
             # print(f"DEBUG: Réponse API brute: {response}", file=sys.stderr) # Pour déboguer si besoin
             if response.prompt_feedback:
                 print(f"WARN: Prompt bloqué ou problème de feedback: {response.prompt_feedback}", file=sys.stderr)
                 return f"Erreur API: Prompt bloqué ({response.prompt_feedback})"
             return "Réponse vide ou format inattendu de l'API."

    except Exception as e:
        error_msg = f"Erreur lors de l'appel à l'API Gemini : {e}"
        print(error_msg, file=sys.stderr)
        return error_msg


# --- Section principale pour tester les fonctions ---
if __name__ == "__main__":
    print("--- Début des tests de l'agent ---")

    # Test 1 & 2: Lecture Fichier
    print("\n--- Test 1 & 2 : Lecture Fichiers ---")
    test_file_path_ok = "/Users/sahebmlik/node_modules/basic-ftp/dist/test.txt"
    test_file_path_notfound = "/Users/sahebmlik/node_modules/basic-ftp/dist/fichier_qui_n_existe_pas.txt"
    
    content_ok = read_local_file(test_file_path_ok)
    print(f"Test 1 (fichier existant): {'Succès (contenu lu)' if content_ok is not None else 'ÉCHEC'}")
    
    content_notfound = read_local_file(test_file_path_notfound)
    print(f"Test 2 (fichier inexistant): {'Succès (retourne None)' if content_notfound is None else 'ÉCHEC'}")

    # Test 3: Exécution Script
    print("\n--- Test 3 : Exécution Script ---")
    test_script_path = "/Users/sahebmlik/node_modules/basic-ftp/dist/test_script.sh"
    code, out, err = run_local_script(test_script_path)
    print(f"Test 3 (exécution script): {'Succès (code 0)' if code == 0 else 'ÉCHEC (code ' + str(code) + ')'}")
    if code == 0:
         print(f"   Sortie: '{out}'")
         print(f"   Erreur: '{err}'")

    # Test 4: Appel API Gemini
    print("\n--- Test 4 : Appel API Gemini ---")
    # Vérifier si l'API a été configurée avec succès au début
    if api_configured_ok:
        test_prompt = "Explique la différence entre une API REST et une API SOAP en une phrase."
        print(f"   Prompt envoyé : \"{test_prompt}\"")
        gemini_response = call_gemini(test_prompt)
        print(f"   Réponse de Gemini reçue: {'Oui' if not gemini_response.startswith('Erreur:') else 'NON (Voir erreurs ci-dessus)'}")
        if not gemini_response.startswith('Erreur:'):
            print(f"   >>> {gemini_response}")
    else:
        print("   Test sauté - Clé API non disponible ou configuration échouée.")
    
    print("\n--- Fin des tests ---")