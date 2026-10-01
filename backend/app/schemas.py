from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional

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
