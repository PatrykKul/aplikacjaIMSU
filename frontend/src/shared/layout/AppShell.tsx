"use client";

import { LogOutIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";
import { Avatar, AvatarFallback } from "@/shared/ui/avatar";
import { Button } from "@/shared/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";

export type NavItem = { href: string; label: string };
export type ShellUser = { displayName: string; roleLabel: string };

type AppShellProps = {
  nav: NavItem[];
  user: ShellUser;
  onLogout: () => void;
  children: ReactNode;
};

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

export function AppShell({ nav, user, onLogout, children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-svh flex-col">
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
        <div className="grid h-16 grid-cols-[minmax(max-content,1fr)_minmax(0,64rem)_minmax(max-content,1fr)] items-center px-4 sm:px-6">
          <Link
            href="/dashboard"
            className="justify-self-start text-lg font-semibold tracking-tight"
          >
            IMSU
          </Link>

          <nav className="flex min-w-0 items-center gap-1 px-4 sm:px-6">
            {nav.map((item) => {
              const active =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                    active && "bg-muted text-foreground",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button
                  variant="ghost"
                  className="gap-2 justify-self-end px-2"
                />
              }
              aria-label={`Menu użytkownika: ${user.displayName}`}
            >
              <Avatar>
                <AvatarFallback>{initials(user.displayName)}</AvatarFallback>
              </Avatar>
              <span className="hidden max-w-32 truncate sm:inline">
                {user.displayName}
              </span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuGroup>
                <DropdownMenuLabel>
                  <span className="block truncate text-sm text-foreground">
                    {user.displayName}
                  </span>
                  <span className="block font-normal">{user.roleLabel}</span>
                </DropdownMenuLabel>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onLogout}>
                <LogOutIcon />
                Wyloguj
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
        {children}
      </main>
    </div>
  );
}
