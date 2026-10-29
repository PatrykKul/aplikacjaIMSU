"use client";

import { useEffect, useState } from "react";

import { getHealth, type Health } from "../api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; health: Health }
  | { kind: "error" };

export function HealthStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((health) => {
        if (!cancelled) setState({ kind: "ok", health });
      })
      .catch(() => {
        if (!cancelled) setState({ kind: "error" });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.kind === "loading") {
    return <p>Sprawdzanie połączenia z serwerem...</p>;
  }
  if (state.kind === "error") {
    return <p className="text-red-600">Brak połączenia z serwerem.</p>;
  }

  const databaseOk = state.health.database === "ok";
  return (
    <ul className="space-y-1">
      <li>
        Serwer: <strong className="text-green-600">działa</strong>
      </li>
      <li>
        Baza danych:{" "}
        <strong className={databaseOk ? "text-green-600" : "text-red-600"}>
          {databaseOk ? "działa" : "błąd"}
        </strong>
      </li>
    </ul>
  );
}
