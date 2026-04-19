import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format a number as currency using US locale (comma as thousands separator).
 * This ensures consistent rendering on both server and client to prevent hydration mismatches.
 * Always uses 'en-US' locale regardless of browser/user locale.
 */
export function formatCurrency(amount: number): string {
  return amount.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })
}
