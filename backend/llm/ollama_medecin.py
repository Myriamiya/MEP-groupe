import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import OLLAMA_BASE_URL, MODEL, EMBED_MODEL

GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
EMBED_URL    = f"{OLLAMA_BASE_URL}/api/embeddings"


def ask_ollama_medecin(prompt: str) -> str:
    try:
        response = requests.post(GENERATE_URL, json={
            "model":  MODEL,
            "prompt": prompt,
            "stream": False
        })
        data = response.json()
        return data.get("response", "Pas de reponse du modele.")
    except Exception as e:
        return f"Erreur Ollama : {str(e)}"


def get_embedding(text: str) -> list:
    try:
        response = requests.post(EMBED_URL, json={
            "model":  EMBED_MODEL,
            "prompt": text
        })
        embedding = response.json().get("embedding", [])
        
        if not embedding:
            return []
        
        # Normalisation L2 pour que la distance euclidienne
        # soit equivalente a la distance cosinus
        import math
        norme = math.sqrt(sum(x**2 for x in embedding))
        if norme == 0:
            return embedding
        return [x / norme for x in embedding]
        
    except Exception as e:
        print(f"Erreur embedding : {str(e)}")
        return []

def check_ollama() -> bool:
    try:
        response    = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        models      = response.json().get("models", [])
        model_names = [m["name"] for m in models]
        mistral_ok  = any("mistral" in n for n in model_names)
        embed_ok    = any("nomic" in n for n in model_names)
        if not mistral_ok:
            print("Mistral non trouve → ollama pull mistral")
        if not embed_ok:
            print("nomic-embed-text non trouve → ollama pull nomic-embed-text")
        return mistral_ok and embed_ok
    except Exception:
        print("Ollama n'est pas lance sur localhost:11434")
        return False