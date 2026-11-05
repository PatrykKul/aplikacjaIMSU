import { create } from "zustand";

type AdminState = {
  isAdmin: boolean;
  setIsAdmin: (value: boolean) => void;
  toggleAdmin: () => void;
};

export const useAdminStore = create<AdminState>((set) => ({
  isAdmin: false,
  setIsAdmin: (value) => set({ isAdmin: value }),
  toggleAdmin: () => set((s) => ({ isAdmin: !s.isAdmin })),
}));
