"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight, LogOut, ShieldCheck, User, Coins } from "lucide-react";
import { signOut } from "next-auth/react";
import { signOut as firebaseSignOut } from "firebase/auth";
import { firebaseAuth } from "@/lib/firebase";
import { useEffect, useRef, useState } from "react";

type AppNavbarProps = {
  isAuthenticated: boolean;
  userName?: string | null;
  credits?: number;
};

export function AppNavbar({ isAuthenticated, userName, credits }: AppNavbarProps) {
  const pathname = usePathname();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!pathname || pathname.startsWith("/login")) {
    return null;
  }

  const isLanding = pathname === "/";
  const isReport = pathname.startsWith("/results") || pathname.startsWith("/report");
  const isReports = pathname.startsWith("/reports") || pathname.startsWith("/dashboard");

  return (
    <header className="sticky top-0 z-50 border-b border-white/8 bg-[hsl(222,47%,4%)]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">

        {/* Left: logo always visible */}
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2 text-white">
            <ShieldCheck className="h-5 w-5 text-sky-400" />
            <span className="text-base font-semibold tracking-tight">ClaimSmart</span>
          </Link>
        </div>

        {/* Right */}
        <div className="flex items-center gap-2">

          {/* Landing secondary links (desktop only) */}
          {isLanding && !isAuthenticated && (
            <Link
              href="/#example"
              className="hidden md:inline-flex h-10 items-center rounded-xl px-2 text-sm font-medium text-slate-300 transition-colors hover:text-white"
            >
              See Example
            </Link>
          )}
          {isLanding && isAuthenticated && (
            <Link
              href="/reports"
              className="hidden md:inline-flex h-10 items-center rounded-xl px-2 text-sm font-medium text-slate-300 transition-colors hover:text-white"
            >
              My Reports
            </Link>
          )}

          {/* Results: New Analysis CTA */}
          {isReport && (
            <Link
              href="/analyze"
              className="inline-flex h-10 items-center justify-center rounded-xl bg-sky-500 px-4 text-sm font-semibold text-white shadow-lg shadow-sky-500/20 transition-all hover:bg-sky-400 hover:shadow-sky-500/30 active:scale-[0.98]"
            >
              New Analysis
            </Link>
          )}

          {/* Reports: Analyze CTA */}
          {isReports && (
            <Link
              href="/analyze"
              className="inline-flex h-10 items-center justify-center rounded-xl bg-sky-500 px-4 text-sm font-semibold text-white shadow-lg shadow-sky-500/20 transition-all hover:bg-sky-400 hover:shadow-sky-500/30 active:scale-[0.98]"
            >
              Analyze
            </Link>
          )}

          {/* User avatar + sign-out dropdown */}
          {isAuthenticated && (
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setUserMenuOpen((p) => !p)}
                className="flex h-9 w-9 items-center justify-center rounded-full border border-sky-500/30 bg-sky-500/20 text-sky-300 transition-colors hover:bg-sky-500/30"
                aria-label="User menu"
              >
                <User className="h-4 w-4" />
              </button>
              {userMenuOpen && (
                <div className="absolute right-0 top-11 z-50 w-44 overflow-hidden rounded-xl border border-white/10 bg-[hsl(222,47%,7%)] shadow-xl shadow-black/40">
                  <div className="border-b border-white/5 flex flex-col gap-1 px-3 py-2.5">
                    <p className="truncate text-xs font-semibold text-white">{userName}</p>
                  </div>
                  
                  <Link
                    href="/credits"
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <Coins className="h-4 w-4 text-emerald-400" />
                    <span>Credits:</span>
                    <span className="font-bold text-emerald-400 ml-auto">{credits ?? '-'}</span>
                  </Link>

                  <button
                    type="button"
                    onClick={() => {
                      setUserMenuOpen(false);
                      firebaseSignOut(firebaseAuth).finally(() => {
                        signOut({ callbackUrl: "/" });
                      });
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Mobile: sticky CTA strip on report pages */}
      {isReport && (
        <div className="border-t border-white/5 px-4 py-3 md:hidden">
          <Link
            href="/analyze"
            className="mx-auto flex h-12 max-w-7xl items-center justify-center rounded-2xl bg-sky-500 text-sm font-semibold text-white shadow-2xl shadow-sky-500/25 transition-all hover:bg-sky-400 active:scale-[0.98]"
          >
            Start Another Analysis
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>
      )}
    </header>
  );
}