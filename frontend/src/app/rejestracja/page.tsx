import type { Metadata } from "next";
import { AuthForm } from "@/components/auth/AuthForm";

export const metadata: Metadata = { title: "Rejestracja – StylNauki" };

export default function RejestracjaPage() {
  return <AuthForm mode="rejestracja" />;
}
