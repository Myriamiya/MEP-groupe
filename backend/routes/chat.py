import sys
import os
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from rag.prepare        import prepare
from rag.retriever      import retrieve
from rag.construit      import build_prompt, is_context_sufficient
from rag.postprocessor  import postprocess
from llm.ollama_medecin import ask_ollama_medecin


# ── Routeur FastAPI ───────────────────────────────────
router = APIRouter()


# ── Modèle de la requête entrante ─────────────────────
class ChatRequest(BaseModel):
    question:   str
    user_id:    str = "anonyme"
    historique: list = []


# ── Modèle de la réponse sortante ─────────────────────
class ChatResponse(BaseModel):
    reponse:  str
    sources:  list
    fallback: bool


# ── Endpoint principal POST /chat ─────────────────────
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    t_debut = time.perf_counter()

    print(f"\n{'='*50}")
    print(f"Question reçue : {request.question}")
    print(f"User ID        : {request.user_id}")

    # ── Étape 2 : Prétraitement ───────────────────────
    t0 = time.perf_counter()
    print("\n[Étape 2] Prétraitement...")
    donnees = prepare(request.question)
    print(f"  Langue détectée  : {donnees['lang']}")
    print(f"  Question nettoyée: {donnees['cleaned']}")
    print(f"  Reformulée       : {donnees['reformulated']}")
    print(f"  ⏱ Temps pretraitement : {time.perf_counter() - t0:.2f}s")

    # ── Étape 3 : Recherche vectorielle ───────────────
    t0 = time.perf_counter()
    print("\n[Étape 3] Recherche dans ChromaDB...")
    passages = retrieve(donnees["reformulated"], donnees["cleaned"])
    print(f"  ⏱ Temps recherche ChromaDB : {time.perf_counter() - t0:.2f}s")

    if not passages:
        print("  Aucun passage trouvé → fallback activé")
        print(f"  ⏱ TEMPS TOTAL : {time.perf_counter() - t_debut:.2f}s")
        return ChatResponse(
            reponse  = "Je n'ai pas trouvé cette information dans la base de données interne. Veuillez contacter le service concerné.",
            sources  = [],
            fallback = True
        )

    # ── Étape 4 : Construction du contexte ────────────
    t0 = time.perf_counter()
    print("\n[Étape 4] Construction du contexte...")
    if not is_context_sufficient(passages):
        print("  Contexte insuffisant → fallback activé")
        print(f"  ⏱ TEMPS TOTAL : {time.perf_counter() - t_debut:.2f}s")
        return ChatResponse(
            reponse  = "Je n'ai pas trouvé cette information dans la base de données interne. Veuillez contacter le service concerné.",
            sources  = [],
            fallback = True
        )

    prompt = build_prompt(
        question = request.question,
        passages = passages,
        lang     = donnees["lang"]
    )
    print(f"  ⏱ Temps construction contexte : {time.perf_counter() - t0:.2f}s")
    print(f"  Taille du prompt : {len(prompt)} caracteres")

    # ── Étapes 5+6 : Appel LLM + Génération ──────────
    t0 = time.perf_counter()
    print("\n[Étapes 5+6] Envoi à Mistral...")
    reponse_brute = ask_ollama_medecin(prompt)
    print(f"  Réponse reçue : {reponse_brute[:80]}...")
    print(f"  ⏱ Temps Mistral (le plus lourd) : {time.perf_counter() - t0:.2f}s")

    # ── Étapes 7+8 : Post-traitement + Retour ─────────
    t0 = time.perf_counter()
    print("\n[Étapes 7+8] Post-traitement...")
    resultat = postprocess(reponse_brute, passages)
    print(f"  ⏱ Temps post-traitement : {time.perf_counter() - t0:.2f}s")

    print(f"\n✅ Réponse finale prête")
    print(f"⏱ TEMPS TOTAL DE LA REQUETE : {time.perf_counter() - t_debut:.2f}s")
    print(f"{'='*50}\n")

    return ChatResponse(
        reponse  = resultat["reponse"],
        sources  = resultat["sources"],
        fallback = resultat["fallback"]
    )


# ── Endpoint de santé GET /health ─────────────────────
@router.get("/health")
def health():
    return {"status": "ok", "service": "Medic IA"}