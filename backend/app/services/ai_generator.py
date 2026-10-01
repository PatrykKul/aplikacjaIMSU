import json
import logging
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

# Domyślny model (nadpisywany przez GEMINI_MODEL w .env)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Łańcuch fallback - jeśli model się wyczerpie, spróbuj następnego
FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",      # 500 RPM - NAJLEPSZY limit
    "gemini-2.5-flash-lite",      # 10 RPM - second best
    "gemini-2-flash-lite",        # Alternatywa
    "gemini-2.5-flash",           # Ostateczność (może być zablokowany)
]

_api_key = os.getenv("GEMINI_API_KEY")

ALLOWED_TYPY = frozenset({"teoria", "przyklad", "uwaga", "zadanie"})


class AIConfigError(RuntimeError):
    """Generator AI nie jest skonfigurowany (brak klucza API)."""


def _tekst_z_odpowiedzi(response: Any) -> str:
    """Bezpieczne wyciągnięcie tekstu; przy blokadzie safety `response.text` może rzucać wyjątkiem."""
    try:
        t = (response.text or "").strip()
        if t:
            return t
    except Exception as e:
        block = getattr(response, "prompt_feedback", None)
        cands = getattr(response, "candidates", None) or []
        reason = getattr(block, "block_reason", None) if block else None
        raise ValueError(
            f"Brak treści odpowiedzi modelu (blokada lub pusta odpowiedź). "
            f"block_reason={reason!r}, candidates={len(cands)}. Oryginał: {e!s}"
        ) from e
    raise ValueError(
        "Pusta odpowiedź modelu (sprawdź GEMINI_API_KEY, limit API lub nazwę modelu GEMINI_MODEL)."
    )


def _oczysc_json_z_markdown(raw: str) -> str:
    s = raw.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", s, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return s


def generuj_materialy_ai(tytul_tematu: str, nazwa_dzialu: str) -> List[Dict[str, Any]]:
    if not _api_key or not str(_api_key).strip():
        raise AIConfigError(
            "Brak zmiennej GEMINI_API_KEY (plik .env w katalogu backend). "
            "Pobierz klucz z https://aistudio.google.com/apikey"
        )

    prompt = f"""
Jesteś doświadczonym nauczycielem. Wygeneruj lekcję dla tematu: {tytul_tematu} (Dział: {nazwa_dzialu}).

Zwróć WYŁĄCZNIE tablicę JSON (bez markdown, bez komentarzy), każdy element:
{{
  "typ": "teoria" | "przyklad" | "uwaga" | "zadanie",
  "tresc": "Markdown i LaTeX tam gdzie potrzeba",
  "odpowiedz": "tylko dla zadanie — krótka odpowiedź lub null",
  "rozwiazanie": "tylko dla zadanie — rozwiązanie krok po kroku lub null"
}}

Przeplataj teorię z przykładami, dodaj ważne uwagi i na końcu dokładnie 3 zadania typu "zadanie".
Pola odpowiedz i rozwiazanie ustaw na null dla typów innych niż "zadanie".
"""
    # Try the configured model first, then the fallback chain
    models_to_try = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]
    response = None
    last_error: Exception | None = None
    with genai.Client(api_key=_api_key.strip()) as client:
        for model in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                break
            except Exception as e:
                logger.warning("Model %s niedostępny: %s", model, e)
                last_error = e
    if response is None:
        raise ValueError(
            f"Wywołanie Gemini nie powiodło się dla żadnego z modeli {models_to_try!r}. "
            f"Ostatni błąd: {last_error!s}"
        ) from last_error

    raw = _tekst_z_odpowiedzi(response)
    raw = _oczysc_json_z_markdown(raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model nie zwrócił poprawnego JSON: {e!s}. Początek odpowiedzi: {raw[:400]!r}"
        ) from e
    if not isinstance(data, list):
        raise ValueError("Oczekiwano tablicy JSON")
    return [_normalizuj_blok_ai(x, i) for i, x in enumerate(data)]


def _normalizuj_blok_ai(item: Any, index: int) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"Element {index} nie jest obiektem JSON")
    typ = str(item.get("typ", "teoria")).lower()
    if typ not in ALLOWED_TYPY:
        typ = "teoria"
    tresc = item.get("tresc")
    if tresc is None or (isinstance(tresc, str) and not tresc.strip()):
        tresc = "—"
    else:
        tresc = str(tresc).strip()
    odp = item.get("odpowiedz")
    rozw = item.get("rozwiazanie")
    if typ != "zadanie":
        odp, rozw = None, None
    else:
        odp = None if odp is None else str(odp).strip() or None
        rozw = None if rozw is None else str(rozw).strip() or None
    return {
        "typ": typ,
        "tresc": tresc,
        "odpowiedz": odp,
        "rozwiazanie": rozw,
    }
