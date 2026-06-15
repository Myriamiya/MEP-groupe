# Medic IA — Assistant Medical Interne Intelligent

## Description
Chatbot IA connecte aux donnees medicales internes.
Pipeline RAG avec FastAPI + LangChain + ChromaDB + Mistral 7B.

## Stack technique
- Backend : FastAPI Python
- RAG : LangChain
- Base vectorielle : ChromaDB
- LLM : Mistral 7B via Ollama
- Frontend : HTML / CSS / JS

## Installation

### 1. Prerequis
- Python 3.10+
- Ollama installe

### 2. Installer les dependances
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

### 3. Telecharger les modeles Ollama
ollama pull mistral
ollama pull nomic-embed-text

### 4. Ingerer les donnees
python -c "from rag.embedder import build_vectorstore; build_vectorstore()"

### 5. Lancer le backend
python main.py

## Acces
- API : http://localhost:8000
- Documentation : http://localhost:8000/docs

## Equipe
Myriam
Landry
Lysa
ECE Bordeaux 
