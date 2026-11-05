import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BLOK_TYP = Literal[
    "teoria",
    "przyklad",
    "uwaga",
    "zadanie",
    # Multimedia / interactive types
    "wideo",
    "obraz",
    "diagram",
    "audio",
    "cwiczenie",
    "quiz",
]
BLOK_STYL = Literal["V", "A", "K"]


# ==========================================
# BLOK
# ==========================================


class KrokCwiczenia(BaseModel):
    polecenie: str = Field(..., min_length=1, max_length=2000)
    podpowiedz: Optional[str] = Field(None, max_length=2000)


class CwiczenieDane(BaseModel):
    kroki: List[KrokCwiczenia] = Field(..., min_length=1, max_length=30)


class PytanieQuizu(BaseModel):
    tresc: str = Field(..., min_length=1, max_length=2000)
    odpowiedzi: List[str] = Field(..., min_length=2, max_length=6)
    poprawna: int = Field(..., ge=0)

    @model_validator(mode="after")
    def _poprawna_w_zakresie(self):
        if self.poprawna >= len(self.odpowiedzi):
            raise ValueError("Indeks poprawnej odpowiedzi jest poza listą odpowiedzi")
        if any(not o.strip() for o in self.odpowiedzi):
            raise ValueError("Odpowiedź nie może być pusta")
        return self


class QuizDane(BaseModel):
    pytania: List[PytanieQuizu] = Field(..., min_length=1, max_length=30)


_DANE_WG_TYPU = {"quiz": QuizDane, "cwiczenie": CwiczenieDane}


def waliduj_dane_bloku(typ: str, dane: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Zwraca oczyszczone `dane` dla typów strukturalnych; dla pozostałych typów None."""
    model = _DANE_WG_TYPU.get(typ)
    if model is None:
        return None
    if not dane:
        raise ValueError(f"Blok typu „{typ}” wymaga pola dane")
    return model.model_validate(dane).model_dump()


class BlokBase(BaseModel):
    typ: BLOK_TYP
    tresc: str
    odpowiedz: Optional[str] = None
    rozwiazanie: Optional[str] = None
    kolejnosc: int = 0
    image_url: Optional[str] = None
    styl: Optional[BLOK_STYL] = None
    media_url: Optional[str] = None
    dane: Optional[Dict[str, Any]] = None
    poziom: Optional[int] = Field(None, ge=1, le=3)


class BlokCreate(BaseModel):
    typ: BLOK_TYP
    tresc: str
    odpowiedz: Optional[str] = None
    rozwiazanie: Optional[str] = None
    kolejnosc: Optional[int] = None
    image_url: Optional[str] = None
    styl: Optional[BLOK_STYL] = None
    media_url: Optional[str] = None
    dane: Optional[Dict[str, Any]] = None
    poziom: Optional[int] = Field(None, ge=1, le=3)


class BlokUpdate(BaseModel):
    typ: Optional[BLOK_TYP] = None
    tresc: Optional[str] = None
    odpowiedz: Optional[str] = None
    rozwiazanie: Optional[str] = None
    kolejnosc: Optional[int] = None
    image_url: Optional[str] = None
    styl: Optional[BLOK_STYL] = None
    media_url: Optional[str] = None
    dane: Optional[Dict[str, Any]] = None
    poziom: Optional[int] = Field(None, ge=1, le=3)


class Blok(BlokBase):
    id: int
    temat_id: int
    model_config = ConfigDict(from_attributes=True)


class QuizOdpowiedziIn(BaseModel):
    # One entry per question: index of the chosen answer or null
    odpowiedzi: List[Optional[int]] = Field(..., min_length=1, max_length=30)
    # Style in which the student went through the topic (default: the student's own style)
    styl: Optional[BLOK_STYL] = None


class RekomendacjaOut(BaseModel):
    typ: Literal["nastepny", "powtorka", "koniec", "powtorz"]
    tytul: str
    dlaczego: str
    styl: Optional[str] = None
    temat_id: Optional[int] = None


class PropozycjaStyluOut(BaseModel):
    styl: BLOK_STYL
    komunikat: str
    dlaczego: str


class QuizWynikOut(BaseModel):
    poprawne: int
    liczba_pytan: int
    procent: int
    trafienia: List[bool]
    poprawne_odpowiedzi: List[int]
    # Filled in for students only (adaptation)
    zaliczony: Optional[bool] = None
    rekomendacja: Optional[RekomendacjaOut] = None
    propozycja_stylu: Optional[PropozycjaStyluOut] = None
    wagi: Optional[Dict[str, int]] = None


class PersonalizacjaOut(BaseModel):
    """Dlaczego uczeń widzi akurat taki zestaw bloków."""

    styl: Optional[str] = None
    poziom: int
    dlaczego: List[str]


class BlokReorder(BaseModel):
    ids: List[int] = Field(..., min_length=0)


class ItemReorder(BaseModel):
    ids: List[int] = Field(..., min_length=0)


# ==========================================
# TEMAT
# ==========================================


class TematBase(BaseModel):
    tytul: str
    kolejnosc: int = 0


class TematCreate(TematBase):
    pass


class TematUpdate(BaseModel):
    tytul: Optional[str] = None


class TematSummary(BaseModel):
    id: int
    tytul: str
    dzial_id: int
    kolejnosc: int = 0
    model_config = ConfigDict(from_attributes=True)


class Temat(TematBase):
    id: int
    dzial_id: int
    bloki: List[Blok] = []
    # Style used to pick the blocks (None = all blocks, editor view)
    styl_widoku: Optional[str] = None
    personalizacja: Optional[PersonalizacjaOut] = None
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# DZIAŁ
# ==========================================


class DzialBase(BaseModel):
    nazwa: str
    kolejnosc: int = 0


class DzialCreate(DzialBase):
    pass


class DzialUpdate(BaseModel):
    nazwa: Optional[str] = None


class Dzial(DzialBase):
    id: int
    kurs_id: int
    tematy: List[TematSummary] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# KURS
# ==========================================


class KursBase(BaseModel):
    nazwa: str
    opis: str
    kolejnosc: int = 0
    is_published: bool = False
    etykieta_dzial: str = "Działy"
    etykieta_temat: str = "Tematy lekcyjne"


class KursCreate(KursBase):
    pass


class KursUpdate(BaseModel):
    nazwa: Optional[str] = None
    opis: Optional[str] = None
    is_published: Optional[bool] = None
    etykieta_dzial: Optional[str] = None
    etykieta_temat: Optional[str] = None


class Kurs(KursBase):
    id: int
    dzialy: List[Dzial] = []
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# WYSZUKIWARKA
# ==========================================


class DzialSearchHit(BaseModel):
    id: int
    nazwa: str
    kurs_id: int
    model_config = ConfigDict(from_attributes=True)


class GlobalSearchResponse(BaseModel):
    dzialy: List[DzialSearchHit] = []
    tematy: List[TematSummary] = []


# ==========================================
# UŻYTKOWNICY / AUTH
# ==========================================

ROLA = Literal["admin", "nauczyciel", "uczen"]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalizuj_email(v: str) -> str:
    v = v.strip().lower()
    if len(v) > 254 or not _EMAIL_RE.match(v):
        raise ValueError("Nieprawidłowy adres e-mail")
    return v


class RejestracjaIn(BaseModel):
    email: str
    imie: str = Field(..., min_length=1, max_length=80)
    # bcrypt uses at most 72 bytes of the password
    haslo: str = Field(..., min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _normalizuj_email(v)

    @field_validator("imie")
    @classmethod
    def _imie(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Imię nie może być puste")
        return v

    @field_validator("haslo")
    @classmethod
    def _haslo(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Hasło jest za długie")
        return v


class LogowanieIn(BaseModel):
    email: str
    haslo: str = Field(..., max_length=200)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


class UzytkownikOut(BaseModel):
    id: int
    email: str
    imie: str
    rola: ROLA
    aktywny: bool
    ankieta_wypelniona: bool
    styl_uczenia: Optional[str] = None
    styl_zrodlo: Optional[str] = None
    utworzono: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    uzytkownik: UzytkownikOut


class ZmianaRoliIn(BaseModel):
    rola: ROLA


# ==========================================
# ANKIETA VAK
# ==========================================

STYL = Literal["V", "A", "K"]

ANKIETA_WYMAGANA_DETAIL = {
    "kod": "ANKIETA_WYMAGANA",
    "komunikat": "Najpierw wypełnij ankietę stylu uczenia się",
}


class OdpowiedzAnkietyOut(BaseModel):
    """Odpowiedź widziana przez wypełniającego — bez przypisanego stylu."""

    id: int
    tresc: str
    model_config = ConfigDict(from_attributes=True)


class PytanieAnkietyOut(BaseModel):
    id: int
    tresc: str
    kolejnosc: int
    odpowiedzi: List[OdpowiedzAnkietyOut]
    model_config = ConfigDict(from_attributes=True)


class WyborOdpowiedzi(BaseModel):
    pytanie_id: int
    odpowiedz_id: int


class AnkietaOdpowiedziIn(BaseModel):
    odpowiedzi: List[WyborOdpowiedzi] = Field(..., min_length=1, max_length=200)


class WynikAnkietyOut(BaseModel):
    id: int
    punkty_v: int
    punkty_a: int
    punkty_k: int
    styl_dominujacy: str
    data: datetime
    model_config = ConfigDict(from_attributes=True)


class ProfilOut(BaseModel):
    uzytkownik: UzytkownikOut
    wynik_ankiety: Optional[WynikAnkietyOut] = None


class StylRecznyIn(BaseModel):
    styl: STYL


class OdpowiedzAnkietyIn(BaseModel):
    tresc: str = Field(..., min_length=1, max_length=500)
    styl: STYL

    @field_validator("tresc")
    @classmethod
    def _tresc(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Treść odpowiedzi nie może być pusta")
        return v


class PytanieAnkietyIn(BaseModel):
    tresc: str = Field(..., min_length=1, max_length=500)
    aktywne: bool = True
    odpowiedzi: List[OdpowiedzAnkietyIn]

    @field_validator("tresc")
    @classmethod
    def _tresc(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Treść pytania nie może być pusta")
        return v

    @model_validator(mode="after")
    def _po_jednej_odpowiedzi_na_styl(self):
        if sorted(o.styl for o in self.odpowiedzi) != ["A", "K", "V"]:
            raise ValueError("Pytanie musi mieć dokładnie po jednej odpowiedzi dla stylu V, A i K")
        return self


class OdpowiedzAnkietyEdycjaOut(BaseModel):
    id: int
    tresc: str
    styl: STYL
    model_config = ConfigDict(from_attributes=True)


class PytanieAnkietyEdycjaOut(BaseModel):
    id: int
    tresc: str
    kolejnosc: int
    aktywne: bool
    odpowiedzi: List[OdpowiedzAnkietyEdycjaOut]
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# NAUKA / ADAPTACJA
# ==========================================

TYP_ZDARZENIA = Literal[
    "otwarcie_tematu",
    "odtworzenie_wideo",
    "odtworzenie_audio",
    "ukonczenie_cwiczenia",
    "czas_w_temacie",
]


class ZdarzenieIn(BaseModel):
    temat_id: int
    blok_id: Optional[int] = None
    typ: TYP_ZDARZENIA
    styl: Optional[BLOK_STYL] = None
    czas_s: Optional[int] = Field(None, ge=0, le=24 * 3600)


class PostepOut(BaseModel):
    temat_id: int
    zaliczony: bool
    najlepszy_wynik: Optional[int] = None
    ostatni_wynik: Optional[int] = None
    liczba_prob: int
    model_config = ConfigDict(from_attributes=True)


class SciezkaTematOut(BaseModel):
    id: int
    tytul: str
    dzial: str
    zaliczony: bool
    najlepszy_wynik: Optional[int] = None
    ostatni_wynik: Optional[int] = None
    liczba_prob: int


class SciezkaKursOut(BaseModel):
    id: int
    nazwa: str
    zaliczone: int
    tematy: List[SciezkaTematOut]


class NastepnyKrokOut(BaseModel):
    temat_id: int
    tytul: str
    kurs: str
    dlaczego: str


class SciezkaOut(BaseModel):
    styl_uczenia: Optional[str] = None
    styl_zrodlo: Optional[str] = None
    styl_ankiety: Optional[str] = None
    wagi: Dict[str, int]
    poziom: int
    poziom_dlaczego: Optional[str] = None
    kursy: List[SciezkaKursOut]
    nastepny_krok: Optional[NastepnyKrokOut] = None
    propozycja_stylu: Optional[PropozycjaStyluOut] = None


class DecyzjaPropozycjiIn(BaseModel):
    styl: BLOK_STYL
    akceptuj: bool


# ==========================================
# PANELE: NAUCZYCIEL / ADMIN
# ==========================================


class UczenOut(BaseModel):
    """Uczeń widziany przez nauczyciela: styl z ankiety i styl aktualny (ręczny / z adaptacji)."""

    id: int
    imie: str
    email: str
    aktywny: bool
    ankieta_wypelniona: bool
    styl_uczenia: Optional[str] = None
    styl_zrodlo: Optional[str] = None
    styl_ankiety: Optional[str] = None
    punkty_ankiety: Optional[Dict[str, int]] = None
    wagi: Dict[str, int]
    zaliczone_tematy: int
    liczba_prob: int
    ostatnia_aktywnosc: Optional[datetime] = None


class ZdarzenieOut(BaseModel):
    typ: str
    temat: str
    styl: Optional[str] = None
    wartosc: Optional[int] = None
    czas_s: Optional[int] = None
    data: datetime


class UczenSzczegolyOut(BaseModel):
    uczen: UczenOut
    sciezka: SciezkaOut
    historia_ankiet: List[WynikAnkietyOut]
    zdarzenia: List[ZdarzenieOut]


class ZmianaAktywnosciIn(BaseModel):
    aktywny: bool
