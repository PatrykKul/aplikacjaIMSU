"""Slug URL z polskimi znakami (np. do folderów kursy-materialy)."""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text or not str(text).strip():
        return "x"
    s = str(text).strip()
    # NFKD + usuń znaki diakrytyczne (ł -> l przez translację)
    pl = str.maketrans(
        "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
        "acelnoszzACELNOSZZ",
    )
    s = s.translate(pl)
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_only = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    s = ascii_only.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "x"
