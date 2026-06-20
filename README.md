# Medic IA — Assistant Médical Intelligent (RAG)
Medic IA est un chatbot médical interne conçu pour aider un médecin généraliste à accéder rapidement aux informations contenues dans les dossiers patients, en posant simplement une question en langage naturel. Le système repose sur une architecture RAG (Retrieval Augmented Generation) : il ne laisse jamais le modèle d'IA inventer une réponse — il va d'abord chercher les informations pertinentes dans la base de données interne, puis génère une réponse strictement basée sur ce contexte.
MEP  ECE Bordeaux.

## Fonctionnalités

-Chat conversationnel en langage naturel (français)
-Recherche sémantique dans les dossiers patients via base vectorielle
-Recherche exacte par numéro de patient (ex: "historique du patient 9")
-Citation systématique des sources utilisées pour chaque réponse
-Mécanisme de fallback si aucune information pertinente n'est trouvée (pas d'hallucination)
-Authentification multi-utilisateurs (inscription / connexion / changement de compte)
-Historique des conversations, persistant entre les sessions (localStorage)
-Dictée vocale (Speech-to-Text) et lecture audio des réponses (Text-to-Speech)
-Paramètres personnalisables (voix, niveau de détail, sources, rétention)
-100% local : aucune donnée patient ne quitte la machine (conforme RGPD)
---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend | FastAPI (Python) |
| Base vectorielle | ChromaDB |
| Modèle de langage | Mistral 7B (via Ollama) |
| Embeddings | nomic-embed-text |
| Frontend | HTML / CSS / JS vanilla |
| Données | Fichiers JSON (dossiers patients) |

---

## Structure du projet

```
medic-ia/
├── backend/
│   ├── main.py                  # Démarre le serveur
│   ├── configuration.py         # Réglages (Ollama, ChromaDB, RAG)
│   ├── routes/chat.py            # Endpoint POST /chat
│   ├── rag/
│   │   ├── ingestor.py          # Lit les JSON, 1 chunk par consultation
│   │   ├── embedder.py          # Vectorise et stocke dans ChromaDB
│   │   ├── retriever.py         # Recherche les passages pertinents
│   │   ├── prepare.py           # Nettoyage / reformulation de la question
│   │   ├── construit.py         # Construit le prompt final
│   │   └── postprocessor.py     # Nettoyage réponse + fallback
│   ├── llm/ollama_medecin.py     # Appels à Ollama
│   └── data/chroma/              # Base vectorielle (générée)
├── frontend/
│   ├── INDEX.html
│   ├── Prog.css
│   └── Prog.js
└── sources/documents/
    ├── dossier_interne.json
    └── dossier_enrichi.json

## Installation

```powershell
cd medic-ia/backend
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn chromadb requests pydantic

ollama pull mistral
ollama pull nomic-embed-text
```

> Toujours utiliser `venv`, pas `.venv`.

---

## Lancer le projet

```powershell
# Terminal 1
ollama serve

# Terminal 2 — construire la base vectorielle (1ere fois ou apres modif des donnees)
cd backend
venv\Scripts\activate
python -c "import sys; sys.path.insert(0, '.'); from rag.embedder import build_vectorstore; build_vectorstore()"

# Terminal 2 (suite) — demarrer le backend
python main.py
```

Backend : `http://localhost:8000` — Documentation interactive : `http://localhost:8000/docs`

Ouvrir ensuite `frontend/INDEX.html` dans un navigateur (backend déjà lancé requis).

---

## API

**POST /chat**
```json
// Requête
{"question": "Quel patient a une bronchite chronique ?", "user_id": "test", "historique": []}

// Réponse
{"reponse": "Le patient 10...", "sources": [{"fichier": "dossier_enrichi.json", "categorie": "Medical"}], "fallback": false}
```

---

## Points techniques clés

- **1 chunk par consultation** (pas par patient) pour éviter de diluer le signal sémantique.
- **Vecteurs normalisés (L2) + métrique `ip`** dans ChromaDB — sans ça, les scores sont faussés.
- **Filtre de pertinence** : avec la métrique `ip`, plus petit = plus proche → garder les passages avec `score <= MIN_SCORE`.
- **Préfixes nomic-embed-text** : `search_query: ` pour les questions, `search_document: ` pour les chunks stockés.
- **Recherche par numéro de patient** : pour "historique du patient X", le retriever interroge ChromaDB directement par métadonnées plutôt que par similarité (le chiffre est sinon perdu lors de la reformulation).
- **Numérotation des patients globale** entre les fichiers JSON, pour éviter les collisions.


## Exemples de questions

```
Quel patient souffre de bronchite chronique ?
Quel patient prend du PROZAC ?
Quels patients ont un diabète de type 2 ?
Quel est l'historique médical du patient 9 ?
```
