import { auth } from "@/lib/auth";

export function isProAdmin(plan: string | null | undefined) {
  return plan === "PRO";
}

export async function requireProApiUser() {
  const session = await auth();

  if (!session?.user?.id) {
    return { error: "Unauthorized", status: 401 } as const;
  }

  const userPlan = (session.user as typeof session.user & { plan?: string | null }).plan;

  if (!isProAdmin(userPlan)) {
    return { error: "Forbidden", status: 403 } as const;
  }

  return { session } as const;
}