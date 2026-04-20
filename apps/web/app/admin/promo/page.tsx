import { redirect } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { isProAdmin } from "@/lib/admin";
import { PromoCodeManager } from "@/components/admin/PromoCodeManager";

export const metadata = {
  title: "Admin Promo Codes | ClaimSmart",
};

export default async function AdminPromoPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/login?callbackUrl=/admin/promo");
  }

  if (!isProAdmin(session.user.plan)) {
    redirect("/dashboard");
  }

  const promoCodes = await prisma.promoCode.findMany({
    orderBy: { createdAt: "desc" },
    include: {
      _count: {
        select: { redemptions: true },
      },
    },
  });

  const initialPromoCodes = promoCodes.map((promoCode) => ({
    ...promoCode,
    expiresAt: promoCode.expiresAt?.toISOString() ?? null,
    createdAt: promoCode.createdAt.toISOString(),
  }));

  return <PromoCodeManager initialPromoCodes={initialPromoCodes} />;
}
