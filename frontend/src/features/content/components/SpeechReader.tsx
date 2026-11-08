"use client";

import { PauseIcon, Volume2Icon } from "lucide-react";
import { useEffect, useState, useSyncExternalStore } from "react";

import { Button } from "@/shared/ui/button";

function subscribeNothing() {
  return () => {};
}

/** Speech synthesis exists only in the browser; false while rendering on the server. */
function useSpeechSupported(): boolean {
  return useSyncExternalStore(
    subscribeNothing,
    () => "speechSynthesis" in window,
    () => false,
  );
}

/** Polish voice if the browser has one; otherwise the default voice reads the text. */
function polishVoice(): SpeechSynthesisVoice | undefined {
  return window.speechSynthesis
    .getVoices()
    .find((voice) => voice.lang.toLowerCase().startsWith("pl"));
}

/** Reads a text aloud with the browser's speech synthesis (Web Speech API). */
export function SpeechReader({ text }: { text: string }) {
  const supported = useSpeechSupported();
  const [speaking, setSpeaking] = useState(false);

  // Stop reading when the lesson is left
  useEffect(() => {
    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  if (!supported) {
    return (
      <p className="text-sm text-muted-foreground">
        Ta przeglądarka nie potrafi czytać na głos. Przeczytaj tekst poniżej.
      </p>
    );
  }

  function speak() {
    const synth = window.speechSynthesis;
    synth.cancel(); // only one text at a time
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "pl-PL";
    utterance.voice = polishVoice() ?? null;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    setSpeaking(true);
    synth.speak(utterance);
  }

  function stop() {
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }

  return speaking ? (
    <Button variant="outline" onClick={stop}>
      <PauseIcon data-icon="inline-start" />
      Zatrzymaj
    </Button>
  ) : (
    <Button variant="outline" onClick={speak}>
      <Volume2Icon data-icon="inline-start" />
      Posłuchaj
    </Button>
  );
}
