import os
import sys
import shutil
import math
import uuid

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import CHROMA_PATH, COLLECTION_NAME, CHUNK_SIZE, CHUNK_OVERLAP
from rag.ingestor import ingest_all
import chromadb

def get_client_and_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "ip"}
    )
    return client, collection

def normalize(embedding):
    norme = math.sqrt(sum(x**2 for x in embedding))
    if norme == 0:
        return embedding
    return [x / norme for x in embedding]

def get_normalized_embedding(text):
    import requests
    from configuration import OLLAMA_BASE_URL, EMBED_MODEL
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text}
        )
        embedding = response.json().get("embedding", [])
        if not embedding:
            return []
        return normalize(embedding)
    except Exception as e:
        print(f"Erreur embedding : {str(e)}")
        return []

def chunk_text(texte):
    mots = texte.split()
    chunks = []
    current = []
    taille = 0
    for mot in mots:
        current.append(mot)
        taille += len(mot) + 1
        if taille >= CHUNK_SIZE:
            chunks.append(" ".join(current))
            overlap = current[-CHUNK_OVERLAP:] if len(current) > CHUNK_OVERLAP else current
            current = overlap.copy()
            taille = sum(len(m) + 1 for m in current)
    if current:
        chunks.append(" ".join(current))
    return chunks

def embed_and_store(document, collection):
    chunks = chunk_text(document["contenu"])
    for i, chunk in enumerate(chunks):
        print(f"    Vectorisation chunk {i+1}/{len(chunks)}...")
        embedding = get_normalized_embedding(chunk)
        if not embedding:
            print(f"    Embedding vide pour chunk {i+1}, ignore.")
            continue
        doc_id = f"{document['nom']}_{document['categorie']}_{i}_{str(uuid.uuid4())[:8]}"
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{
                "categorie": document["categorie"],
                "source": document["source"],
                "nom": document["nom"],
                "chunk": i
            }]
        )
    print(f"  {len(chunks)} chunks stockes pour [{document['categorie']}]")

def build_vectorstore():
    print("\nDemarrage de l ingestion...\n")
    documents = ingest_all()
    if not documents:
        print("Aucun document trouve dans sources/documents/")
        return
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    os.makedirs(CHROMA_PATH, exist_ok=True)
    _, collection = get_client_and_collection()
    print(f"\nVectorisation de {len(documents)} documents...\n")
    for doc in documents:
        print(f"Traitement : [{doc['categorie']}] {doc['nom']}")
        embed_and_store(doc, collection)
    total = collection.count()
    print(f"\nBase vectorielle prete : {total} chunks dans ChromaDB")

def reset_vectorstore():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    os.makedirs(CHROMA_PATH, exist_ok=True)
    print("Base vectorielle reinitialisee.")

if __name__ == "__main__":
    build_vectorstore()
