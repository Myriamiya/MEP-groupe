import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import SOURCES_PATH


def read_json(path: str, start_offset: int = 0):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        if isinstance(data, list):
            for i, patient in enumerate(data):
                numero        = start_offset + i + 1
                sexe          = patient.get("sex", "Inconnu")
                ddn           = patient.get("DDN", "Inconnue")
                consultations = patient.get("Consultations", [])

                for c in consultations:
                    date         = c.get("Date_consultation", "")
                    texte        = c.get("Text", "")
                    resultat     = c.get("Resultat_consultation", "")
                    prescription = c.get("Prescription", "")
                    accident     = c.get("Accident_travail", "")
                    biologie     = c.get("Biologie", "")
                    biometrie    = c.get("Biometrie", "")

                    contenu = f"Patient {numero} - {sexe} - ne(e) le {ddn}. Consultation du {date} :"
                    if texte:        contenu += f" {texte}"
                    if resultat:     contenu += f" Resultat : {resultat}"
                    if prescription: contenu += f" Prescription : {prescription}"
                    if accident:     contenu += f" Accident travail : {accident}"
                    if biologie:     contenu += f" Biologie : {biologie}"
                    if biometrie:    contenu += f" Biometrie : {biometrie}"

                    documents.append({
                        "nom":               os.path.basename(path),
                        "type":              "JSON",
                        "chemin":            path,
                        "categorie":         "Medical",
                        "source":            os.path.basename(path),
                        "patient_numero":    numero,
                        "date_consultation": date,
                        "contenu":           contenu
                    })

        print(f"  {len(documents)} consultations lues depuis {os.path.basename(path)} ({len(data)} patients, numeros {start_offset+1} a {start_offset+len(data)})")
        return documents, len(data)

    except Exception as e:
        print(f"Erreur JSON {path} : {str(e)}")
        return [], 0


def ingest_all() -> list:
    tous_les_docs = []
    dossier = os.path.join(SOURCES_PATH, "documents")

    if not os.path.exists(dossier):
        print(f"Dossier introuvable : {dossier}")
        return []

    offset = 0
    for fichier in sorted(os.listdir(dossier)):
        if fichier.endswith(".json"):
            path = os.path.join(dossier, fichier)
            docs, nb_patients = read_json(path, start_offset=offset)
            tous_les_docs.extend(docs)
            offset += nb_patients

    print(f"\nTotal : {len(tous_les_docs)} consultations ingerees, {offset} patients uniques")
    return tous_les_docs