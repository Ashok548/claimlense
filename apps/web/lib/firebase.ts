import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, onAuthStateChanged } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY!,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN!,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID!,
};

// Lazy singleton — safe in Next.js client components
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

export const firebaseAuth = getAuth(app);

export async function getFirebaseIdToken(): Promise<string> {
  // Wait for Firebase to restore auth state from local storage (handles page refreshes)
  await new Promise<void>((resolve) => {
    const unsub = onAuthStateChanged(firebaseAuth, () => {
      unsub();
      resolve();
    });
  });

  const user = firebaseAuth.currentUser;
  if (!user) {
    throw new Error("You must be signed in to continue.");
  }

  return user.getIdToken();
}
