"use client";

import { ClockIcon, UserXIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useCurrentUser, useLogout } from "../hooks";
import { isUnapprovedTeacher } from "../roles";

/** "/pending": a teacher account waiting for (or refused) the admin's approval. */
export function PendingApprovalPage() {
  const router = useRouter();
  const { data: user, refetch, isFetching } = useCurrentUser();
  const logout = useLogout();
  const waiting = !!user && isUnapprovedTeacher(user);

  useEffect(() => {
    // Approved meanwhile (or not a teacher at all): nothing to wait for
    if (user && !waiting) {
      router.replace("/dashboard");
    }
  }, [user, waiting, router]);

  if (!user || !waiting) {
    return <PageSpinner />;
  }

  const rejected = user.approval_status === "rejected";
  const logoutButton = (
    <Button
      variant={rejected ? "default" : "outline"}
      disabled={logout.isPending}
      onClick={() =>
        logout.mutate(undefined, { onSettled: () => router.replace("/") })
      }
    >
      {logout.isPending && <Spinner data-icon="inline-start" />}
      Wyloguj
    </Button>
  );

  return (
    <PageMessage
      icon={rejected ? UserXIcon : ClockIcon}
      title={
        rejected
          ? "Konto nauczyciela nie zostało zatwierdzone"
          : "Konto czeka na zatwierdzenie przez administratora"
      }
      description={
        rejected
          ? "Administrator odrzucił prośbę o konto nauczyciela, więc nie możesz tworzyć kursów. Jeśli to pomyłka, skontaktuj się z administratorem szkoły."
          : "Kursy utworzysz, gdy administrator zatwierdzi Twoje konto. Zajrzyj tu później albo sprawdź teraz, czy coś się zmieniło."
      }
      action={
        <div className="flex flex-wrap justify-center gap-3">
          {!rejected && (
            <Button disabled={isFetching} onClick={() => void refetch()}>
              {isFetching && <Spinner data-icon="inline-start" />}
              Sprawdź ponownie
            </Button>
          )}
          {logoutButton}
        </div>
      }
    />
  );
}
