import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import SHOW_SOURCES, FALLBACK_MESSAGE, MIN_SCORE


# ── Nettoyer la réponse de Mistral ────────────────────
def clean_response(reponse: str) -> str:
    # Retire les espaces en trop
    reponse = reponse.strip()
    reponse = re.sub(r'\n{3,}', '\n\n', reponse)

    # Retire les artefacts du modèle
    artefacts = [
        "RÉPONSE :", "ANSWER :", "Réponse :",
        "En tant qu'assistant", "As an assistant"
    ]
    for a in artefacts:
        reponse = reponse.replace(a, "").strip()

    return reponse


# ── Formater les sources ──────────────────────────────
def format_sources(passages: list) -> list:
    if not SHOW_SOURCES or not passages:
        return []

    sources_vues = set()
    sources      = []

    for p in passages:
        source    = p.get("source", "Inconnue")
        categorie = p.get("categorie", "Général")

        # Évite les doublons
        cle = f"{source}_{categorie}"
        if cle not in sources_vues:
            sources_vues.add(cle)
            sources.append({
                "fichier":   source,
                "categorie": categorie
            })

    return sources


# ── Calculer le score de confiance (interne) ──────────
def compute_confidence(passages: list) -> float:
    if not passages:
        return 0.0

    scores = [p["score"] for p in passages]
    return round(sum(scores) / len(scores), 2)


# ── Vérifier si fallback nécessaire ───────────────────
def needs_fallback(passages: list) -> bool:
    if not passages:
        return True
    meilleur_score = min([p["score"] for p in passages])
    return meilleur_score > MIN_SCORE


# ── Pipeline complet de post-traitement ───────────────
def postprocess(reponse: str, passages: list) -> dict:

    # Fallback si contexte insuffisant
    if needs_fallback(passages):
        return {
            "reponse":  FALLBACK_MESSAGE,
            "sources":  [],
            "fallback": True
        }

    # Nettoyage de la réponse
    reponse_nette = clean_response(reponse)

    # Formatage des sources
    sources = format_sources(passages)

    # Score de confiance (interne uniquement)
    confidence = compute_confidence(passages)
    print(f"  Score de confiance interne : {confidence}")

    return {
        "reponse":  reponse_nette,
        "sources":  sources,
        "fallback": False
    }