export type BlokTyp = "teoria" | "przyklad" | "uwaga" | "zadanie" | "wideo";

export interface Blok {
  id: number;
  temat_id: number;
  typ: BlokTyp;
  tresc: string;
  odpowiedz: string | null;
  rozwiazanie: string | null;
  kolejnosc: number;
  image_url?: string | null;
}

export interface Kurs {
  id: number;
  nazwa: string;
  opis: string;
  is_published: boolean;
  kolejnosc?: number;
  dzialy?: Dzial[];
}

export interface Dzial {
  id: number;
  nazwa: string;
  kurs_id: number;
  kolejnosc?: number;
  tematy?: TematSummary[];
}

export interface TematSummary {
  id: number;
  tytul: string;
  dzial_id: number;
  kolejnosc?: number;
}

export interface Temat {
  id: number;
  tytul: string;
  dzial_id: number;
  kolejnosc?: number;
  bloki?: Blok[];
}

export interface DzialSearchHit {
  id: number;
  nazwa: string;
  kurs_id: number;
}

export interface GlobalSearchResponse {
  dzialy: DzialSearchHit[];
  tematy: TematSummary[];
}

export type Rola = "admin" | "nauczyciel" | "uczen";

export interface Uzytkownik {
  id: number;
  email: string;
  imie: string;
  rola: Rola;
  aktywny: boolean;
  ankieta_wypelniona: boolean;
  styl_uczenia: string | null;
  styl_zrodlo: string | null;
  utworzono: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  uzytkownik: Uzytkownik;
}

export type Styl = "V" | "A" | "K";

export interface OdpowiedzAnkiety {
  id: number;
  tresc: string;
}

export interface PytanieAnkiety {
  id: number;
  tresc: string;
  kolejnosc: number;
  odpowiedzi: OdpowiedzAnkiety[];
}

export interface WynikAnkiety {
  id: number;
  punkty_v: number;
  punkty_a: number;
  punkty_k: number;
  /** One letter, or several for a tie (e.g. "VA"). */
  styl_dominujacy: string;
  data: string;
}

export interface Profil {
  uzytkownik: Uzytkownik;
  wynik_ankiety: WynikAnkiety | null;
}
