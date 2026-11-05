"use client";

import { usePathname } from "next/navigation";
import { AuthGate, PUBLIC_PATHS } from "@/components/auth/AuthGate";
import { Navbar } from "@/components/Navbar";

function AmbientBackground() {
  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-slate-100 dark:bg-slate-950"
      aria-hidden
    >
      <div
        className="absolute inset-0 opacity-[0.35] [background-image:linear-gradient(rgba(14,165,233,0.07)_1px,transparent_1px),linear-gradient(90deg,rgba(14,165,233,0.07)_1px,transparent_1px)] [background-size:48px_48px] [mask-image:linear-gradient(180deg,transparent,black_35%,black)]"
      />
      <div className="absolute -left-[20%] -top-[30%] h-[min(100vh,920px)] w-[min(140vw,920px)] bg-glow-purple blur-[100px]" />
      <div className="absolute -right-[25%] top-[10%] h-[min(90vh,800px)] w-[min(100vw,800px)] bg-glow-magenta blur-[90px]" />
      <div className="absolute bottom-0 left-0 h-[50vh] w-[70vw] bg-glow-orchid blur-[80px]" />
    </div>
  );
}

export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showNavbar = !PUBLIC_PATHS.includes(pathname);

  return (
    <>
      <AmbientBackground />
      <AuthGate>
        {showNavbar ? <Navbar /> : null}
        <div className="relative z-0 flex flex-1 flex-col">{children}</div>
      </AuthGate>
    </>
  );
}
