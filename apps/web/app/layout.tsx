import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";
import { auth } from "@/lib/auth";
import { AppNavbar } from "@/components/navigation/AppNavbar";
import { CreditsProvider } from "@/hooks/useCredits";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "ClaimLense — Know What Your Insurance Will Pay",
  description:
    "AI-powered health insurance claim analyzer for India. Find out which hospital bill items will be rejected before it's too late.",
  keywords: ["health insurance", "claim analysis", "IRDAI", "hospital bill", "TPA", "India"],
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-background text-foreground`}>
        <CreditsProvider isAuthenticated={!!session?.user}>
          <TooltipProvider>
            <AppNavbar
              isAuthenticated={!!session?.user}
              userName={session?.user?.name ?? session?.user?.email}
            />
            <main className="max-w-6xl mx-auto px-4 w-full flex-1 flex flex-col">
              {children}
            </main>
          </TooltipProvider>
        </CreditsProvider>
      </body>
    </html>
  );
}
