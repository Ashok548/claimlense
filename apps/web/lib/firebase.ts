import { initializeApp, getApps, getApp } from "firebase/app";
import {
  GoogleAuthProvider,
  browserLocalPersistence,
  browserPopupRedirectResolver,
  getAuth,
  initializeAuth,
  onAuthStateChanged,
  signInWithPopup,
} from "firebase/auth";

const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
const authDomain =
  process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN ||
  (projectId ? `${projectId}.firebaseapp.com` : undefined);

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY!,
  authDomain: authDomain!,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID!,
};

// Lazy singleton — safe in Next.js client components
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

function createFirebaseAuth() {
  if (typeof window === "undefined") {
    return getAuth(app);
  }

  try {
    return initializeAuth(app, {
      persistence: browserLocalPersistence,
      popupRedirectResolver: browserPopupRedirectResolver,
    });
  } catch {
    return getAuth(app);
  }
}

export const firebaseAuth = createFirebaseAuth();

if (typeof window !== "undefined") {
  firebaseAuth.useDeviceLanguage();
}

const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: "select_account" });

export async function signInWithGooglePopup() {
  return signInWithPopup(firebaseAuth, googleProvider);
}

export function getFirebaseAuthDomain() {
  return authDomain;
}

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
