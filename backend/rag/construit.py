import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import FALLBACK_MESSAGE, MIN_SCORE


# ── Construire le contexte a partir des passages ──────
def build_context(passages: list) -> str:
    if not passages:
        return None

    contexte = []
    for p in passages:
        bloc = (
            f"[Source: {p['source']} | "
            f"Categorie: {p['categorie']}]\n"
            f"{p['contenu']}"
        )
        contexte.append(bloc)

    return "\n\n".join(contexte)


# ── Construire le prompt complet pour Mistral ─────────
def build_prompt(question: str, passages: list, lang: str = "fr") -> str:
    contexte = build_context(passages)

    if not contexte:
        return None

    if lang == "fr":
        prompt = f"""Tu es Medic IA, un assistant medical interne professionnel.

REGLES STRICTES :
1. Reponds UNIQUEMENT en te basant sur le contexte fourni ci-dessous
2. Si plusieurs patients correspondent, cite-les tous
3. Inclus toujours le numero du patient dans ta reponse
4. Si l'information est absente, dis-le clairement
5. Sois precis, professionnel et concis

CONTEXTE :
{contexte}

QUESTION :
{question}

REPONSE :"""

    else:
        prompt = f"""You are Medic IA, an intelligent internal medical assistant.
You must answer ONLY based on the context provided below.
If the information is not in the context, say so clearly.
Respond professionally and concisely in English.

CONTEXT:
{contexte}

QUESTION:
{question}

ANSWER:"""

    return prompt


# ── Verifier si le contexte est suffisant ─────────────
def is_context_sufficient(passages: list) -> bool:
    if not passages:
        return False
    meilleur_score = min([p["score"] for p in passages])
    return meilleur_score <= MIN_SCORE