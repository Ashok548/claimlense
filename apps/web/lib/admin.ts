import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export function isProAdmin(plan: string | null | undefined) {
  return plan === "PRO";
}

export async function requireProApiUser() {
  const session = await auth();

  if (!session?.user?.id) {
    return { error: "Unauthorized", status: 401 } as const;
  }

  const dbUser = await prisma.user.findUnique({
    where: { id: session.user.id },
    select: { plan: true }
  });

  if (!dbUser || !isProAdmin(dbUser.plan)) {
    return { error: "Forbidden", status: 403 } as const;
  }

  return { session } as const;
}