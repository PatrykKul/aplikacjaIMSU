"use client";

import { useEffect, useState } from "react";
import { ChevronDown, Square, Volume2 } from "lucide-react";
import { mediaSrc } from "@/lib/api";

type Props = {
  tresc: string;
  mediaUrl?: string | null;
  /** Called once when playback starts (recording or text-to-speech). */
  onPlay?: () => void;
};

/** Nagranie (jeśli jest) + lektor przeglądarki czytający treść + rozwijana transkrypcja. */
export function AudioBlock({ tresc, mediaUrl, onPlay }: Props) {
  const [mowi, setMowi] = useState(false);
  const [transkrypcja, setTranskrypcja] = useState(false);
  const [lektorDostepny, setLektorDostepny] = useState(false);

  useEffect(() => {
    // Web Speech API exists only in the browser
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLektorDostepny(typeof window !== "undefined" && "speechSynthesis" in window);
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const czytaj = () => {
    const synth = window.speechSynthesis;
    synth.cancel();
    const u = new SpeechSynthesisUtterance(tresc);
    u.lang = "pl-PL";
    const glos = synth.getVoices().find((v) => v.lang.toLowerCase().startsWith("pl"));
    if (glos) u.voice = glos;
    u.onend = () => setMowi(false);
    u.onerror = () => setMowi(false);
    setMowi(true);
    synth.speak(u);
    onPlay?.();
  };

  const stop = () => {
    window.speechSynthesis.cancel();
    setMowi(false);
  };

  return (
    <div>
      {mediaUrl ? (
        <audio controls src={mediaSrc(mediaUrl)} className="mb-3 w-full" onPlay={() => onPlay?.()} />
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        {lektorDostepny &&
          (mowi ? (
            <button
              type="button"
              onClick={stop}
              className="inline-flex items-center gap-2 rounded-xl border border-violet-400/60 bg-violet-500/10 px-4 py-2 text-sm font-semibold text-violet-700 transition hover:bg-violet-500/20 dark:text-violet-200"
            >
              <Square className="h-4 w-4" aria-hidden />
              Zatrzymaj
            </button>
          ) : (
            <button
              type="button"
              onClick={czytaj}
              className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-500"
            >
              <Volume2 className="h-4 w-4" aria-hidden />
              {mediaUrl ? "Odsłuchaj lektora" : "Odsłuchaj"}
            </button>
          ))}
        <button
          type="button"
          onClick={() => setTranskrypcja((t) => !t)}
          aria-expanded={transkrypcja}
          className="inline-flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
        >
          <ChevronDown
            className={`h-4 w-4 transition-transform ${transkrypcja ? "rotate-180" : ""}`}
            aria-hidden
          />
          {transkrypcja ? "Ukryj transkrypcję" : "Pokaż transkrypcję"}
        </button>
      </div>
      {!lektorDostepny && !mediaUrl && (
        <p className="mt-2 text-xs text-slate-500">
          Ta przeglądarka nie obsługuje lektora — skorzystaj z transkrypcji.
        </p>
      )}
      {transkrypcja && (
        <p className="mt-3 whitespace-pre-line rounded-xl border border-slate-200 bg-white/70 p-4 text-sm leading-relaxed text-slate-700 dark:border-white/10 dark:bg-slate-950/40 dark:text-slate-300">
          {tresc}
        </p>
      )}
    </div>
  );
}
