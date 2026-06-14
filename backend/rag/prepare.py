import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configuration import SUPPORTED_LANGS, DEFAULT_LANG


def detect_language(text: str) -> str:
    french_words  = ["le", "la", "les", "de", "du", "des", "est", "sont",
                     "que", "qui", "quels", "quelle", "quelles", "avec",
                     "pour", "dans", "sur", "quel", "comment", "combien"]
    english_words = ["the", "is", "are", "what", "which", "who", "how",
                     "many", "much", "with", "for", "in", "on", "where"]
    text_lower    = text.lower()
    words         = text_lower.split()
    french_score  = sum(1 for w in words if w in french_words)
    english_score = sum(1 for w in words if w in english_words)
    return "fr" if french_score >= english_score else "en"


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\?\!\.\,\-éèêëàâùûüîïôçÉÈÊËÀÂÙÛÜÎÏÔÇ]', '', text)
    return text


def reformulate(text: str, lang: str) -> str:
    stopwords_fr = ["le", "la", "les", "de", "du", "des", "un", "une",
                    "est", "sont", "avec", "pour", "dans", "sur", "qui",
                    "que", "quoi", "cest", "cette", "ces", "mon", "ma",
                    "mes", "notre", "votre", "leur", "leurs", "moi", "toi"]
    stopwords_en = ["the", "is", "are", "a", "an", "of", "in", "on",
                    "for", "with", "this", "that", "these", "those",
                    "my", "your", "our", "their", "me", "you"]

    stopwords = stopwords_fr if lang == "fr" else stopwords_en
    words     = text.split()

    filtered = []
    for w in words:
        if w.isupper() and len(w) > 1:
            filtered.append(w)
        elif w.lower() not in stopwords and len(w) > 2:
            filtered.append(w.lower())

    return " ".join(filtered)


def prepare(question: str) -> dict:
    cleaned      = clean_text(question)
    lang         = detect_language(cleaned)
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    reformulated = reformulate(cleaned, lang)
    return {
        "original":     question,
        "cleaned":      cleaned,
        "lang":         lang,
        "reformulated": reformulated
    }