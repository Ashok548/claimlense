import type { NextAuthConfig } from "next-auth";

type AuthUserWithPlan = {
  id: string;
  plan?: string | null;
};

type SessionUserWithPlan = {
  id: string;
  plan?: string | null;
};

export const authConfig = {
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isAuthPage = nextUrl.pathname.startsWith("/login");
      const isProtectedRoute =
        nextUrl.pathname.startsWith("/dashboard") ||
        nextUrl.pathname.startsWith("/reports") ||
        nextUrl.pathname.startsWith("/results") ||
        nextUrl.pathname.startsWith("/analyze");

      if (isAuthPage) {
        if (isLoggedIn) {
          return Response.redirect(new URL("/reports", nextUrl));
        }
        return true;
      }

      if (isProtectedRoute) {
        if (!isLoggedIn) {
          return false; // Redirect to login
        }
        return true;
      }
      
      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        const authUser = user as typeof user & AuthUserWithPlan;
        token.id = user.id;
        token.plan = authUser.plan;
      }
      return token;
    },
    async session({ session, token }) {
      if (token && session.user) {
        const sessionUser = session.user as typeof session.user & SessionUserWithPlan;
        sessionUser.id = token.id as string;
        sessionUser.plan = typeof token.plan === "string" ? token.plan : undefined;
      }
      return session;
    }
  },
  providers: [], // Providers are added in auth.ts
} satisfies NextAuthConfig;
