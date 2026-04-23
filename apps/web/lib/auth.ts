import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { prisma } from "@/lib/prisma";
import { adminAuth } from "@/lib/firebase-admin";
import { authConfig } from "./auth.config";
import { Plan } from "@prisma/client";

const VALID_PLANS = new Set<string>(Object.values(Plan));
function toPlan(value: unknown): Plan {
  return typeof value === "string" && VALID_PLANS.has(value)
    ? (value as Plan)
    : Plan.FREE;
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  session: { strategy: "jwt", maxAge: 60 * 60 }, // 1 hour — aligns with Firebase token expiry
  providers: [
    CredentialsProvider({
      name: "Firebase",
      credentials: {
        firebaseToken: { label: "Firebase Token", type: "text" },
      },
      async authorize(credentials) {
        const token = credentials?.firebaseToken as string | undefined;
        if (!token) return null;

        // Verify token with Firebase Admin — throws if invalid/expired
        let decoded: Awaited<ReturnType<typeof adminAuth.verifyIdToken>>;
        try {
          decoded = await adminAuth.verifyIdToken(token);
        } catch {
          return null;
        }

        const { uid, email, name, picture } = decoded;
        // Read plan from Firebase custom claims — set via seed script or admin API.
        // Falls back to FREE for users who haven't been assigned a plan yet.
        const claimPlan = toPlan(decoded["plan"]);

        // Mirror / update user in PostgreSQL on every sign-in.
        // If a row already exists for the same email (seeded or legacy auth),
        // attach the Firebase UID instead of trying to create a duplicate.
        try {
          const existingUser = await prisma.user.findFirst({
            where: {
              OR: [
                { firebaseUid: uid },
                ...(email ? [{ email }] : []),
              ],
            },
          });

          const user = existingUser
            ? await prisma.user.update({
                where: { id: existingUser.id },
                data: {
                  firebaseUid: uid,
                  email: email ?? existingUser.email,
                  name: name ?? existingUser.name,
                  image: picture ?? existingUser.image,
                  plan: claimPlan,
                },
              })
            : await prisma.user.create({
                data: {
                  firebaseUid: uid,
                  email: email ?? null,
                  name: name ?? email?.split("@")[0] ?? null,
                  image: picture ?? null,
                  plan: claimPlan,
                  // credits default to 200 from schema
                },
              });

          return {
            id: user.id,
            email: user.email,
            name: user.name,
            plan: user.plan,
          };
        } catch (error) {
          console.error("NextAuth authorize() failed to sync Firebase user", error);
          return null;
        }
      },
    }),
  ],
});

