"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  createUserWithEmailAndPassword,
  updateProfile,
  sendEmailVerification,
} from "firebase/auth";
import { firebaseAuth, getFirebaseAuthDomain, signInWithGooglePopup } from "@/lib/firebase";
import { ShieldCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState("");
  const [verificationSent, setVerificationSent] = useState(false);

  async function loginWithNextAuth(firebaseToken: string) {
    const res = await signIn("credentials", {
      redirect: false,
      firebaseToken,
    });
    if (res?.error) {
      setError("Account created but sign-in failed. Please try logging in.");
    } else {
      router.push("/reports");
      router.refresh();
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const credential = await createUserWithEmailAndPassword(
        firebaseAuth,
        email,
        password
      );
      // Set display name in Firebase so it propagates to Prisma on upsert
      await updateProfile(credential.user, { displayName: name.trim() || email.split("@")[0] });
      // Send verification email — do NOT sign in until verified
      await sendEmailVerification(credential.user);
      await firebaseAuth.signOut();
      setVerificationSent(true);
    } catch (err: unknown) {
      const code = (err as { code?: string }).code;
      if (code === "auth/email-already-in-use") {
        setError("An account with this email already exists. Please sign in.");
      } else if (code === "auth/weak-password") {
        setError("Password must be at least 6 characters.");
      } else if (code === "auth/invalid-email") {
        setError("Please enter a valid email address.");
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setGoogleLoading(true);
    setError("");
    try {
      const credential = await signInWithGooglePopup();
      const firebaseToken = await credential.user.getIdToken();
      await loginWithNextAuth(firebaseToken);
    } catch (err: unknown) {
      const code = (err as { code?: string }).code;
      if (code === "auth/popup-blocked") {
        setError("Your browser blocked the Google sign-in popup. Allow popups and try again.");
      } else if (code === "auth/unauthorized-domain") {
        setError(
          `Google sign-in is not enabled for this domain. Add ${window.location.hostname} to Firebase authorized domains and verify NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN is set to ${getFirebaseAuthDomain()}.`
        );
      } else if (
        code !== "auth/popup-closed-by-user" &&
        code !== "auth/cancelled-popup-request"
      ) {
        setError("Google sign-in failed. Please try again.");
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[hsl(222,47%,4%)] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-500/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-[120px]" />

      <div className="relative z-10 w-full max-w-md">
        <div className="glass border border-white/10 rounded-2xl p-8 shadow-2xl">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 rounded-full bg-sky-500/10 flex items-center justify-center mb-4 border border-sky-500/20">
              <ShieldCheck className="w-8 h-8 text-sky-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">Create account</h1>
            <p className="text-slate-400 text-sm mt-2 text-center">
              Start analysing claims in seconds.
            </p>
          </div>

          {verificationSent ? (
            <div className="text-center py-4">
              <div className="mb-4 p-4 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-300 text-sm">
                A verification email has been sent to <strong>{email}</strong>.<br />
                Please check your inbox and click the link to verify your account, then{" "}
                <a href="/login" className="underline hover:text-sky-200">sign in</a>.
              </div>
            </div>
          ) : (
            <>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
              {error}
            </div>
          )}

          {/* Google Sign-Up */}
          <Button
            type="button"
            variant="outline"
            onClick={handleGoogle}
            disabled={googleLoading || loading}
            className="w-full mb-4 bg-white/5 border-white/10 text-white hover:bg-white/10"
          >
            {googleLoading ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            )}
            Continue with Google
          </Button>

          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-slate-500 text-xs">or</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          {/* Email / Password Registration */}
          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-slate-300">
                Full Name
              </Label>
              <Input
                id="name"
                type="text"
                placeholder="Dr. Ashok Kumar"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-slate-900/50 border-white/10 text-white placeholder:text-slate-600 focus-visible:ring-sky-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-300">
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@hospital.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-slate-900/50 border-white/10 text-white placeholder:text-slate-600 focus-visible:ring-sky-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-300">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Min. 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="bg-slate-900/50 border-white/10 text-white placeholder:text-slate-600 focus-visible:ring-sky-500"
              />
            </div>

            <Button
              type="submit"
              disabled={loading || googleLoading}
              className="w-full bg-sky-500 hover:bg-sky-400 text-white mt-2 shadow-lg shadow-sky-500/20"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                "Create Account"
              )}
            </Button>
          </form>

          <p className="text-sm text-slate-500 text-center mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-sky-400 hover:text-sky-300">
              Sign in
            </Link>
          </p>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
