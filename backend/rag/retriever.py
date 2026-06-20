import os
import sys
import re
import math
import chromadb

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import CHROMA_PATH, COLLECTION_NAME, TOP_K, MIN_SCORE, OLLAMA_BASE_URL, EMBED_MODEL


def get_normalized_embedding(text: str) -> list:
    import requests
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": f"search_query: {text}"}
        )
        embedding = response.json().get("embedding", [])
        if not embedding:
            return []
        norme = math.sqrt(sum(x**2 for x in embedding))
        return [x / norme for x in embedding] if norme else embedding
    except Exception as e:
        print(f"Erreur embedding : {str(e)}")
        return []


def retrieve(question_reformulee: str) -> list:
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(
            name     = COLLECTION_NAME,
            metadata = {"hnsw:space": "ip"}
        )

        question_embedding = get_normalized_embedding(question_reformulee)
        if not question_embedding:
            print("Embedding vide pour la question.")
            return []

        resultats = collection.query(
            query_embeddings = [question_embedding],
            n_results        = TOP_K,
            include          = ["documents", "metadatas", "distances"]
        )

        passages = []
        for doc, meta, dist in zip(
            resultats["documents"][0],
            resultats["metadatas"][0],
            resultats["distances"][0]
        ):
            score = round(dist, 4)
            print(f"  Score: {score:.4f} | {doc[:60]}")
            if score <= MIN_SCORE:
                passages.append({
                    "contenu":   doc,
                    "categorie": meta.get("categorie", "Medical"),
                    "source":    meta.get("source", "Inconnue"),
                    "score":     score
                })

        print(f"  {len(passages)} passages pertinents trouves")
        return passages

    except Exception as e:
        print(f"Erreur retriever : {str(e)}")
        return []
    import re

def detect_patient_number(text: str):
    match = re.search(r'patient\s*n?\s*(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def retrieve(question_reformulee: str, question_originale: str = "") -> list:
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(
            name     = COLLECTION_NAME,
            metadata = {"hnsw:space": "ip"}
        )

        numero = detect_patient_number(question_originale or question_reformulee)
        if numero is not None:
            resultats = collection.get(
                where={"patient_numero": numero},
                include=["documents", "metadatas"]
            )
            passages = []
            for doc, meta in zip(resultats["documents"], resultats["metadatas"]):
                passages.append({
                    "contenu":   doc,
                    "categorie": meta.get("categorie", "Medical"),
                    "source":    meta.get("source", "Inconnue"),
                    "score":     0.01
                })
            print(f"  Recherche ciblee patient {numero} : {len(passages)} consultations trouvees")
            if passages:
                return passages

        question_embedding = get_normalized_embedding(question_reformulee)
        if not question_embedding:
            print("Embedding vide pour la question.")
            return []

        resultats = collection.query(
            query_embeddings = [question_embedding],
            n_results        = TOP_K,
            include          = ["documents", "metadatas", "distances"]
        )

        passages = []
        for doc, meta, dist in zip(
            resultats["documents"][0],
            resultats["metadatas"][0],
            resultats["distances"][0]
        ):
            score = round(dist, 4)
            print(f"  Score: {score:.4f} | {doc[:60]}")
            if score <= MIN_SCORE:
                passages.append({
                    "contenu":   doc,
                    "categorie": meta.get("categorie", "Medical"),
                    "source":    meta.get("source", "Inconnue"),
                    "score":     score
                })

        print(f"  {len(passages)} passages pertinents trouves")
        return passages

    except Exception as e:
        print(f"Erreur retriever : {str(e)}")
        return []