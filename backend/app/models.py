from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Kurs(Base):
    __tablename__ = "kursy"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nazwa: Mapped[str] = mapped_column(String, unique=True, index=True)
    opis: Mapped[str] = mapped_column(String)
    kolejnosc: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    etykieta_dzial: Mapped[str] = mapped_column(String, nullable=False, default="Działy")
    etykieta_temat: Mapped[str] = mapped_column(String, nullable=False, default="Tematy lekcyjne")

    dzialy: Mapped[List["Dzial"]] = relationship(
        back_populates="kurs", cascade="all, delete-orphan", order_by="Dzial.kolejnosc"
    )


class Dzial(Base):
    __tablename__ = "dzialy"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nazwa: Mapped[str] = mapped_column(String, index=True)
    kolejnosc: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    kurs_id: Mapped[int] = mapped_column(ForeignKey("kursy.id"))
    kurs: Mapped["Kurs"] = relationship(back_populates="dzialy")

    tematy: Mapped[List["Temat"]] = relationship(
        back_populates="dzial", cascade="all, delete-orphan", order_by="Temat.kolejnosc"
    )


class Temat(Base):
    __tablename__ = "tematy"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tytul: Mapped[str] = mapped_column(String, index=True)
    kolejnosc: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    dzial_id: Mapped[int] = mapped_column(ForeignKey("dzialy.id"))
    dzial: Mapped["Dzial"] = relationship(back_populates="tematy")

    bloki: Mapped[List["Blok"]] = relationship(
        back_populates="temat",
        order_by="Blok.kolejnosc",
        cascade="all, delete-orphan",
    )


class Blok(Base):
    __tablename__ = "bloki"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    temat_id: Mapped[int] = mapped_column(ForeignKey("tematy.id"), index=True)
    typ: Mapped[str] = mapped_column(String, nullable=False)
    tresc: Mapped[str] = mapped_column(Text, nullable=False)
    odpowiedz: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rozwiazanie: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kolejnosc: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Learning style: V / A / K, NULL = shared block shown to everyone
    styl: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, index=True)
    media_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Structured content of quiz / cwiczenie blocks (JSON)
    dane_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    temat: Mapped["Temat"] = relationship(back_populates="bloki")

    @property
    def dane(self) -> Optional[dict[str, Any]]:
        return json.loads(self.dane_json) if self.dane_json else None

    @dane.setter
    def dane(self, value: Optional[dict[str, Any]]) -> None:
        self.dane_json = json.dumps(value, ensure_ascii=False) if value else None


def _teraz() -> datetime:
    return datetime.now(timezone.utc)


class Uzytkownik(Base):
    __tablename__ = "uzytkownicy"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    imie: Mapped[str] = mapped_column(String, nullable=False, default="")
    haslo_hash: Mapped[str] = mapped_column(String, nullable=False)
    rola: Mapped[str] = mapped_column(String, nullable=False, default="uczen")
    aktywny: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ankieta_wypelniona: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    styl_uczenia: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    styl_zrodlo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    utworzono: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_teraz)


class PytanieAnkiety(Base):
    __tablename__ = "pytania_ankiety"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tresc: Mapped[str] = mapped_column(Text, nullable=False)
    kolejnosc: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aktywne: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    odpowiedzi: Mapped[List["OdpowiedzAnkiety"]] = relationship(
        back_populates="pytanie", cascade="all, delete-orphan", order_by="OdpowiedzAnkiety.kolejnosc"
    )


class OdpowiedzAnkiety(Base):
    __tablename__ = "odpowiedzi_ankiety"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pytanie_id: Mapped[int] = mapped_column(ForeignKey("pytania_ankiety.id"), index=True)
    tresc: Mapped[str] = mapped_column(Text, nullable=False)
    styl: Mapped[str] = mapped_column(String(1), nullable=False)  # V / A / K
    kolejnosc: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    pytanie: Mapped["PytanieAnkiety"] = relationship(back_populates="odpowiedzi")


class WynikAnkiety(Base):
    __tablename__ = "wyniki_ankiety"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("uzytkownicy.id"), index=True)
    punkty_v: Mapped[int] = mapped_column(Integer, nullable=False)
    punkty_a: Mapped[int] = mapped_column(Integer, nullable=False)
    punkty_k: Mapped[int] = mapped_column(Integer, nullable=False)
    styl_dominujacy: Mapped[str] = mapped_column(String(3), nullable=False)
    data: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_teraz)
