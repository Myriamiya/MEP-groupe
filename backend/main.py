import sys
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(__file__))

from configuration              import API_HOST, API_PORT
from routes.chat                import router as chat_router
from llm.ollama_medecin         import check_ollama
from rag.embedder               import build_vectorstore


# ── Création de l'application FastAPI ─────────────────
app = FastAPI(
    title       = "Medic IA",
    description = "Assistant médical interne intelligent",
    version     = "1.0.0"
)


# ── CORS — autorise le frontend à appeler le backend ──
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"]
)


# ── Inclure les routes ────────────────────────────────
app.include_router(chat_router)


# ── Démarrage du serveur ──────────────────────────────
@app.on_event("startup")
async def startup():
    print("\n" + "="*50)
    print("    Medic IA — Assistant Medical Interne")
    print("="*50)

    # Vérifier Ollama
    print("\n[1/3] Verification d'Ollama...")
    ollama_ok = check_ollama()
    if not ollama_ok:
        print("Ollama non disponible → lance : ollama serve")
    else:
        print("Ollama operationnel")

    # Vérifier ChromaDB sans reconstruire
    print("\n[2/3] Verification de la base vectorielle...")
    try:
        import chromadb
        from configuration import CHROMA_PATH, COLLECTION_NAME
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        col = client.get_or_create_collection(
            name     = COLLECTION_NAME,
            metadata = {"hnsw:space": "ip"}
        )
        count = col.count()
        if count == 0:
            print("Base vectorielle vide → lance : python rag/embedder.py")
        else:
            print(f"Base vectorielle prete : {count} chunks")
    except Exception as e:
        print(f"Erreur base vectorielle : {str(e)}")

    print(f"\n[3/3] Demarrage de l'API...")
    print(f"Medic IA disponible sur http://localhost:{API_PORT}")
    print(f"Documentation sur http://localhost:{API_PORT}/docs")
    print("\n" + "="*50 + "\n")
# ── Point d'entrée ────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host    = API_HOST,
        port    = API_PORT,
        reload  = True
    )