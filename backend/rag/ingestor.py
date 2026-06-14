import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import SOURCES_PATH


# ── Lire un fichier JSON ──────────────────────────────
def read_json(path: str) -> list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []

        if isinstance(data, list):
            for i, patient in enumerate(data):

                # Récupérer les infos du patient
                sexe = patient.get("sex", "Inconnu")
                ddn  = patient.get("DDN", "Inconnue")
                consultations = patient.get("Consultations", [])

                # Construire le texte de toutes les consultations
                texte_consultations = []
                for c in consultations:
                    date    = c.get("Date_consultation", "")
                    texte   = c.get("Text", "")
                    resultat = c.get("Resultat_consultation", "")
                    prescription = c.get("Prescription", "")
                    accident = c.get("Accident_travail", "")
                    biologie = c.get("Biologie", "")
                    biometrie = c.get("Biometrie", "")

                    ligne = f"Consultation du {date} :"
                    if texte:
                        ligne += f" {texte}"
                    if resultat:
                        ligne += f" Résultat : {resultat}"
                    if prescription:
                        ligne += f" Prescription : {prescription}"
                    if accident:
                        ligne += f" Accident travail : {accident}"
                    if biologie:
                        ligne += f" Biologie : {biologie}"
                    if biometrie:
                        ligne += f" Biométrie : {biometrie}"

                    texte_consultations.append(ligne)

                # Assembler le contenu complet du patient
                contenu = (
                    f"Patient {i+1} · {sexe} · né(e) le {ddn}. "
                    + " | ".join(texte_consultations)
                )

                documents.append({
                    "nom":       os.path.basename(path),
                    "type":      "JSON",
                    "chemin":    path,
                    "categorie": "Médical",
                    "source":    os.path.basename(path),
                    "contenu":   contenu
                })

        print(f"  ✅ {len(documents)} patients lus depuis {os.path.basename(path)}")
        return documents

    except Exception as e:
        print(f"Erreur JSON {path} : {str(e)}")
        return []

# ── Ingérer tous les fichiers JSON du dossier ─────────
def ingest_all() -> list: #parcourt tous les fichiers .json
    tous_les_docs = []
    dossier = os.path.join(SOURCES_PATH, "documents")

    if not os.path.exists(dossier):
        print(f"⚠️ Dossier introuvable : {dossier}")
        return []

    for fichier in os.listdir(dossier): #appelle read_json() pour chacun
        if fichier.endswith(".json"):
            path = os.path.join(dossier, fichier)
            docs = read_json(path)
            tous_les_docs.extend(docs)

    print(f"\n✅ Total : {len(tous_les_docs)} entrées ingérées")
    return tous_les_docs #rassemble tous les documents