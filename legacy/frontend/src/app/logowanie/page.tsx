import type { Metadata } from "next";
import { AuthForm } from "@/components/auth/AuthForm";

export const metadata: Metadata = { title: "Logowanie – StylNauki" };

export default function LogowaniePage() {
  return <AuthForm mode="logowanie" />;
}
