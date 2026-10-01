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
