import { useEffect } from "react";

/**
 * Asks the browser to confirm closing or reloading the tab while `dirty`.
 * The App Router cannot block in-app navigation through <Link>, so buttons
 * that leave the page should confirm on their own (see `confirmLeave`).
 */
export function useUnsavedChangesWarning(dirty: boolean) {
  useEffect(() => {
    if (!dirty) {
      return;
    }
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);
}

export const UNSAVED_CHANGES_MESSAGE =
  "Masz niezapisane zmiany. Czy na pewno chcesz wyjść bez zapisywania?";

/** For in-app links: true when the user may leave. */
export function confirmLeave(dirty: boolean): boolean {
  return !dirty || window.confirm(UNSAVED_CHANGES_MESSAGE);
}
