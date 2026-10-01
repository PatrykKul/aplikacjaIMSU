export type BlokTyp =
  | "teoria"
  | "przyklad"
  | "uwaga"
  | "zadanie"
  | "wideo"
  | "obraz"
  | "diagram"
  | "audio"
  | "cwiczenie"
  | "quiz";

export type Styl = "V" | "A" | "K";

export interface KrokCwiczenia {
  polecenie: string;
  podpowiedz: string | null;
}

export interface CwiczenieDane {
  kroki: KrokCwiczenia[];
}

export interface PytanieQuizu {
  tresc: string;
  odpowiedzi: string[];
  /** Present only for teachers; students never receive the answer key. */
  poprawna?: number;
}

export interface QuizDane {
  pytania: PytanieQuizu[];
}

export interface Rekomendacja {
  typ: "nastepny" | "powtorka" | "koniec" | "powtorz";
  tytul: string;
  dlaczego: string;
  styl: Styl | null;
  temat_id: number | null;
}

export interface PropozycjaStylu {
  styl: Styl;
  komunikat: string;
  dlaczego: string;
}

export interface QuizWynik {
  poprawne: number;
  liczba_pytan: number;
  procent: number;
  trafienia: boolean[];
  poprawne_odpowiedzi: number[];
  /** Adaptation fields — present for students only. */
  zaliczony: boolean | null;
  rekomendacja: Rekomendacja | null;
  propozycja_stylu: PropozycjaStylu | null;
  wagi: Record<Styl, number> | null;
}

export interface Personalizacja {
  styl: string | null;
  /** 1 = easier examples, 2 = standard, 3 = extensions. */
  poziom: number;
  dlaczego: string[];
}

export type TypZdarzenia =
  | "otwarcie_tematu"
  | "odtworzenie_wideo"
  | "odtworzenie_audio"
  | "ukonczenie_cwiczenia"
  | "czas_w_temacie";

export interface SciezkaTemat {
  id: number;
  tytul: string;
  dzial: string;
  zaliczony: boolean;
  najlepszy_wynik: number | null;
  ostatni_wynik: number | null;
  liczba_prob: number;
}

export interface SciezkaKurs {
  id: number;
  nazwa: string;
  zaliczone: number;
  tematy: SciezkaTemat[];
}

export interface Sciezka {
  styl_uczenia: string | null;
  styl_zrodlo: string | null;
  styl_ankiety: string | null;
  wagi: Record<Styl, number>;
  poziom: number;
  poziom_dlaczego: string | null;
  kursy: SciezkaKurs[];
  nastepny_krok: { temat_id: number; tytul: string; kurs: string; dlaczego: string } | null;
  propozycja_stylu: PropozycjaStylu | null;
}

export interface Blok {
  id: number;
  temat_id: number;
  typ: BlokTyp;
  tresc: string;
  odpowiedz: string | null;
  rozwiazanie: string | null;
  kolejnosc: number;
  image_url?: string | null;
  /** Learning style; null = shared block. */
  styl: Styl | null;
  media_url?: string | null;
  dane?: QuizDane | CwiczenieDane | null;
  /** 1 = easier extra, 2 / null = standard, 3 = extension. */
  poziom?: number | null;
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
  /** Style used to pick the blocks; null = all blocks (editor view). */
  styl_widoku?: string | null;
  /** Why the student sees this set of blocks (students only). */
  personalizacja?: Personalizacja | null;
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
