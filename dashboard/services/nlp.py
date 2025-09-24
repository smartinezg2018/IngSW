# dashboard/services/nlp.py
import re
import math
from functools import lru_cache

import langid
from pysentimiento import create_analyzer

# ---------- Helpers de carga de modelos ----------
@lru_cache(maxsize=2)
def _get_sentiment_analyzer(lang_code: str = "es"):
    """
    Carga perezosa del analizador de sentimiento por idioma.
    'es' -> español, 'en' -> inglés. Por defecto español.
    """
    if lang_code not in ("es", "en"):
        lang_code = "es"
    return create_analyzer(task="sentiment", lang=lang_code)

# ---------- Normalización ----------
def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    # Unifica espacios
    s = re.sub(r"\s+", " ", s)
    return s

# ---------- Cálculo de 'interest_score' ----------
# Palabras/expresiones que denotan interés en una VACANTE (ES/EN). 
# Puedes ajustar pesos (w) según tu dominio.
KEYWORDS = [
    # Español
    (r"\bvacante(s)?\b", 1.0),
    (r"\b(empleo|trabajo|oportunidad|puesto)\b", 0.9),
    (r"\binteresad[oa]s?\b", 1.0),
    (r"\b(enviar|adjunto|compartir)\s+(mi\s+)?(cv|hoja\s*de\s*vida|curriculum|currículum)\b", 1.0),
    (r"\b(cv|hoja\s*de\s*vida|curriculum|currículum)\b", 0.8),
    (r"\b(cómo|como)\s+(aplic(ar|o)|postul(ar|o)|enviar)\b", 0.9),
    (r"\bpostul(ar|ación|o)\b", 0.7),
    (r"\b(dónde|donde)\s+(aplico|envío|envio|mando)\b", 0.6),
    (r"\b(contratan|contratando)\b", 0.8),
    (r"\b(sueldo|salario|pago|remuneración|beneficios)\b", 0.6),
    (r"\b(horario|horas|turnos|remoto|presencial|híbrido|hibrido)\b", 0.5),
    (r"\b(disponibilidad|experiencia|requisitos)\b", 0.4),

    # Inglés
    (r"\b(job|position|opening|vacancy)\b", 1.0),
    (r"\b(interested|interest)\b", 0.9),
    (r"\b(apply|application|applying|postulate)\b", 0.9),
    (r"\b(send|attach|share)\s+(my\s+)?(resume|cv)\b", 1.0),
    (r"\b(resume|cv)\b", 0.8),
    (r"\b(salary|pay|compensation|benefits)\b", 0.6),
    (r"\b(schedule|hours|shift|remote|onsite|hybrid)\b", 0.5),
    (r"\b(requirements|experience|availability)\b", 0.4),
]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(\+?\d{1,3}[-\s.]?)?\(?\d{2,3}\)?[-\s.]?\d{3,4}[-\s.]?\d{3,4}\b")

def keyword_interest_score(text: str) -> float:
    """
    Suma ponderada de coincidencias, normalizada a 0..1 con una función logística suave.
    """
    if not text:
        return 0.0
    t = text.lower()

    score = 0.0
    for pattern, w in KEYWORDS:
        if re.search(pattern, t):
            score += w

    # Señales fuertes: deja email o teléfono -> añade peso
    if EMAIL_RE.search(t):
        score += 1.0
    if PHONE_RE.search(t):
        score += 0.7

    # Normaliza con logística para evitar crecer sin cota:
    # interest = 1 / (1 + exp(-k*(score - x0)))
    # k controla la pendiente (2.0) y x0 el "punto medio" (~2.0)
    k = 2.0
    x0 = 2.0
    interest = 1.0 / (1.0 + math.exp(-k * (score - x0)))
    return round(interest, 4)

# ---------- API principal ----------
def analyze_comment(text: str):
    """
    Devuelve: (sentiment_label, sentiment_score, interest_score, language)
    sentiment_label ∈ {pos, neu, neg}
    sentiment_score = prob. del label predicho
    interest_score ∈ [0,1]
    """
    clean = normalize_text(text)
    if not clean:
        return "", None, 0.0, "es"

    lang, _ = langid.classify(clean)
    lang = "en" if lang.startswith("en") else "es"  # forzamos es/en

    analyzer = _get_sentiment_analyzer(lang)
    out = analyzer.predict(clean)  # tiene .output (label) y .probas (dict)

    sentiment_label = out.output  # "POS", "NEU", "NEG" en mayúsculas
    probas = out.probas or {}
    sentiment_score = probas.get(sentiment_label, None)
    # Normaliza a minúsculas:
    sentiment_label = sentiment_label.lower() if sentiment_label else ""

    interest = keyword_interest_score(clean)
    return sentiment_label, sentiment_score, interest, lang
