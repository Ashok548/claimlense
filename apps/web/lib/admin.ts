import { auth } from "@/lib/auth";

export function isProAdmin(plan: string | null | undefined) {
  return plan === "PRO";
}

export async function requireProApiUser() {
  const session = await auth();

  if (!session?.user?.id) {
    return { error: "Unauthorized", status: 401 } as const;
  }

  if (!isProAdmin(session.user.plan)) {
    return { error: "Forbidden", status: 403 } as const;
  }

  return { session } as const;
}