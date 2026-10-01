import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Uzytkownik } from "@/lib/types";

type AuthState = {
  token: string | null;
  user: Uzytkownik | null;
  /** True once the persisted session has been read from localStorage. */
  hydrated: boolean;
  setSession: (token: string, user: Uzytkownik) => void;
  setUser: (user: Uzytkownik) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      hydrated: false,
      setSession: (token, user) => set({ token, user }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: "stylnauki-auth",
      partialize: (s) => ({ token: s.token, user: s.user }),
      // Hydrated manually on the client (see AuthGate) to avoid SSR mismatches
      skipHydration: true,
    }
  )
);
