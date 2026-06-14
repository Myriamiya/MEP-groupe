import os

# ── Ollama 
OLLAMA_BASE_URL  = "http://localhost:11434"
MODEL            = "mistral"
EMBED_MODEL      = "nomic-embed-text"

# ── ChromaDB 
CHROMA_PATH      = os.path.join(os.path.dirname(__file__), "data", "chroma")
COLLECTION_NAME  = "medic_ia"

# ── RAG 
CHUNK_SIZE    = 3000
CHUNK_OVERLAP = 150
TOP_K         = 8
MIN_SCORE     = 0.4
# ── Prétraitement 
SUPPORTED_LANGS  = ["fr", "en"]
DEFAULT_LANG     = "fr"

# ── Post-traitement 
SHOW_SOURCES     = True
SHOW_SCORE       = False
FALLBACK_MESSAGE = "Je n'ai pas trouvé cette information dans la base de données interne. Veuillez contacter le service concerné."

# ── API
API_HOST         = "0.0.0.0"
API_PORT         = 8000

# ── Sources 
SOURCES_PATH     = os.path.join(os.path.dirname(__file__), "..", "sources")