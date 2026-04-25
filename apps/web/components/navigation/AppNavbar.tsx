"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight, LogOut, Menu, ShieldCheck, User, Coins, X } from "lucide-react";
import { signOut } from "next-auth/react";
import { signOut as firebaseSignOut } from "firebase/auth";
import { firebaseAuth } from "@/lib/firebase";
import { useEffect, useRef, useState } from "react";

type AppNavbarProps = {
  isAuthenticated: boolean;
  userName?: string | null;
};

import { useCredits } from "@/hooks/useCredits";

export function AppNavbar({ isAuthenticated, userName }: AppNavbarProps) {
  const pathname = usePathname();
  const { credits } = useCredits();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);

  // Close all menus on route change
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setUserMenuOpen(false);
      setMobileMenuOpen(false);
    }, 0);

    return () => window.clearTimeout(timer);
  }, [pathname]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(e.target as Node)) {
        setMobileMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!pathname || pathname.startsWith("/login")) {
    return null;
  }

  const isLanding = pathname === "/";

  // Secondary nav links shown in desktop header and mobile drawer
  const hasSecondaryLink =
    (isLanding && !isAuthenticated) || isAuthenticated;

  function handleSignOut() {
    setUserMenuOpen(false);
    setMobileMenuOpen(false);
    firebaseSignOut(firebaseAuth).finally(() => {
      signOut({ callbackUrl: "/" });
    });
  }

  return (
    <header className="sticky top-0 z-50 border-b border-white/8 bg-[hsl(222,47%,4%)]/80 backdrop-blur-xl">
      {/* ── Main bar ─────────────────────────────────────────── */}
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">

        {/* Left: logo */}
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2 text-white">
            <ShieldCheck className="h-5 w-5 text-sky-400" />
            <span className="text-sm font-semibold tracking-tight sm:text-base">ClaimLense</span>
          </Link>
        </div>

        {/* Right */}
        <div className="flex items-center gap-1.5 sm:gap-2">

          {/* Desktop-only secondary nav links */}
          {isLanding && !isAuthenticated && (
            <Link
              href="/#example"
              className="hidden md:inline-flex h-9 items-center rounded-lg px-2 text-sm font-medium text-slate-300 transition-colors hover:text-white"
            >
              See Example
            </Link>
          )}
          {isAuthenticated && (
            <Link
              href="/reports"
              className="hidden md:inline-flex h-9 items-center rounded-lg px-2 text-sm font-medium text-slate-300 transition-colors hover:text-white"
            >
              My Reports
            </Link>
          )}



          {/* Desktop: user avatar dropdown */}
          {isAuthenticated && (
            <div className="relative hidden md:block" ref={menuRef}>
              <button
                type="button"
                onClick={() => setUserMenuOpen((p) => !p)}
                className="flex h-9 w-9 items-center justify-center rounded-full border border-sky-500/30 bg-sky-500/20 text-sky-300 transition-colors hover:bg-sky-500/30"
                aria-label="User menu"
              >
                <User className="h-4 w-4" />
              </button>
              {userMenuOpen && (
                <div className="absolute right-0 top-11 z-50 w-48 overflow-hidden rounded-xl border border-white/10 bg-[hsl(222,47%,7%)] shadow-xl shadow-black/40">
                  <div className="border-b border-white/5 px-3 py-2.5">
                    <p className="truncate text-xs font-semibold text-white">{userName}</p>
                  </div>
                  <Link
                    href="/credits"
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <Coins className="h-4 w-4 text-emerald-400" />
                    <span>Credits</span>
                    <span className="ml-auto font-bold text-emerald-400">{credits ?? "-"}</span>
                  </Link>
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Mobile: credits pill (always-visible quick glance) */}
          {isAuthenticated && (
            <Link
              href="/credits"
              className="inline-flex md:hidden items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400"
              aria-label="Credits"
            >
              <Coins className="h-3.5 w-3.5" />
              {credits ?? "-"}
            </Link>
          )}

          {/* Mobile: hamburger — only when there are secondary links or auth actions */}
          {(hasSecondaryLink || isAuthenticated) && (
            <div className="relative md:hidden" ref={mobileMenuRef}>
              <button
                type="button"
                onClick={() => setMobileMenuOpen((p) => !p)}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
                aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              >
                {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
              </button>

              {/* Mobile dropdown drawer */}
              {mobileMenuOpen && (
                <div className="absolute right-0 top-11 z-50 w-56 overflow-hidden rounded-xl border border-white/10 bg-[hsl(222,47%,7%)] shadow-xl shadow-black/50">

                  {/* User info */}
                  {isAuthenticated && (
                    <div className="border-b border-white/5 px-3 py-2.5">
                      <p className="truncate text-xs font-semibold text-white">{userName}</p>
                    </div>
                  )}

                  {/* Context-aware nav links */}
                  {isLanding && !isAuthenticated && (
                    <Link
                      href="/#example"
                      className="flex items-center gap-2 px-3 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      See Example
                    </Link>
                  )}
                  {isAuthenticated && (
                    <Link
                      href="/reports"
                      className="flex items-center gap-2 px-3 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      My Reports
                    </Link>
                  )}

                  {isAuthenticated && (
                    <Link
                      href="/credits"
                      className="flex items-center gap-2 px-3 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Coins className="h-4 w-4 text-emerald-400" />
                      <span>Credits</span>
                      <span className="ml-auto font-bold text-emerald-400">{credits ?? "-"}</span>
                    </Link>
                  )}

                  {/* Dashboard / analyze shortcut when on landing */}
                  {isAuthenticated && (
                    <Link
                      href="/analyze"
                      className="flex items-center gap-2 px-3 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Analyze Claim
                    </Link>
                  )}

                  {/* Sign out */}
                  {isAuthenticated && (
                    <div className="border-t border-white/5">
                      <button
                        type="button"
                        onClick={handleSignOut}
                        className="flex w-full items-center gap-2 px-3 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
                      >
                        <LogOut className="h-4 w-4" />
                        Sign out
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

    </header>
  );
}