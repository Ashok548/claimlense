import { randomBytes } from "crypto";

function promoChunk(size: number) {
  return randomBytes(size)
    .toString("base64url")
    .replace(/[^A-Z0-9]/gi, "")
    .toUpperCase()
    .slice(0, size + 2);
}

export function normalizePromoCode(code: string) {
  return code.trim().toUpperCase();
}

export function generatePromoCode(prefix = "CLAIM") {
  const safePrefix = normalizePromoCode(prefix).replace(/[^A-Z0-9]/g, "") || "CLAIM";
  const first = promoChunk(4).padEnd(4, "X").slice(0, 4);
  const second = promoChunk(4).padEnd(4, "X").slice(0, 4);
  return `${safePrefix}-${first}-${second}`;
}