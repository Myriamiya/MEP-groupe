import os
import sys
import chromadb

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import CHROMA_PATH, COLLECTION_NAME, TOP_K, MIN_SCORE
from llm.ollama_medecin import get_embedding


# ── Connexion à ChromaDB ──────────────────────────────
client     = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)


# ── Chercher les passages pertinents ──────────────────
def retrieve(question_reformulee: str) -> list:

    # Vectoriser la question
    question_embedding = get_embedding(question_reformulee)

    if not question_embedding:
        print("⚠️ Embedding vide pour la question.")
        return []

    # Chercher dans ChromaDB
    resultats = collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"]
    )

    # Formatter les résultats
    passages  = []
    documents = resultats["documents"][0]
    metadatas = resultats["metadatas"][0]
    distances = resultats["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        score = round(1 - dist, 2)

        if score >= MIN_SCORE:
            passages.append({
                "contenu":   doc,
                "categorie": meta.get("categorie", "Général"),
                "source":    meta.get("source", "Inconnue"),
                "score":     score
            })

    print(f"✅ {len(passages)} passages pertinents trouvés")
    return passages