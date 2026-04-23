"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

type CreditsContextType = {
  credits: number | undefined;
  isLoading: boolean;
  refreshCredits: () => Promise<void>;
};

const CreditsContext = createContext<CreditsContextType | undefined>(undefined);

export function CreditsProvider({ 
  children, 
  isAuthenticated 
}: { 
  children: React.ReactNode;
  isAuthenticated: boolean;
}) {
  const [credits, setCredits] = useState<number | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(isAuthenticated);

  const refreshCredits = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      setIsLoading(true);
      const res = await fetch("/api/check-credits");
      if (res.ok) {
        const data = await res.json();
        setCredits(data.credits);
      } else {
        console.error("Failed to fetch credits. Status:", res.status);
      }
    } catch (error) {
      console.error("Failed to fetch credits", error);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshCredits();
  }, [refreshCredits]);

  return (
    <CreditsContext.Provider value={{ credits, isLoading, refreshCredits }}>
      {children}
    </CreditsContext.Provider>
  );
}

export function useCredits() {
  const context = useContext(CreditsContext);
  if (context === undefined) {
    throw new Error("useCredits must be used within a CreditsProvider");
  }
  return context;
}
