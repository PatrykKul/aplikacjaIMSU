import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppChrome } from "@/components/AppChrome";
import { Providers } from "@/components/Providers";
import { serverFetchJson } from "@/lib/server-fetch";
import type { GlobalSearchResponse } from "@/lib/types";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "StylNauki",
  description: "Kursy dopasowane do stylu uczenia się (VAK)",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  let globalSearchIndex: GlobalSearchResponse = { dzialy: [], tematy: [] };
  try {
    globalSearchIndex = await serverFetchJson<GlobalSearchResponse>("/szukaj?q=");
  } catch {
    console.warn("Nie udało się pobrać globalnego indeksu wyszukiwania — czy backend działa?");
  }

  return (
    <html
      lang="pl"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col text-slate-900 dark:text-slate-100">
        <Providers>
          <AppChrome searchIndex={globalSearchIndex}>{children}</AppChrome>
        </Providers>
      </body>
    </html>
  );
}
