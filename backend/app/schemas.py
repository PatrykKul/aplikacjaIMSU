import re
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BLOK_TYP = Literal["teoria", "przyklad", "uwaga", "zadanie", "wideo"]


# ==========================================
# BLOK
# ==========================================


class BlokBase(BaseModel):
    typ: BLOK_TYP
    tresc: str
    odpowiedz: Optional[str] = None
    rozwiazanie: Optional[str] = None
    kolejnosc: int = 0
    image_url: Optional[str] = None


class BlokCreate(BaseModel):
    typ: BLOK_TYP
    tresc: str
    odpowiedz: Optional[str] = None
    rozwiazanie: Optional[str] = None
    kolejnosc: Optional[int] = None
    image_url: Optional[str] = None


class BlokUpdate(BaseModel):
    typ: Optional[BLOK_TYP] = None
    tresc: Optional[str] = None
    odpowiedz: Optional[str] = None
    rozwiazanie: Optional[str] = None
    kolejnosc: Optional[int] = None
    image_url: Optional[str] = None


class Blok(BlokBase):
    id: int
    temat_id: int
    model_config = ConfigDict(from_attributes=True)


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
