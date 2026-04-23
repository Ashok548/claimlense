import { PrismaClient, Plan } from '@prisma/client';
import { Pool } from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';
import * as dotenv from 'dotenv';
import * as admin from 'firebase-admin';

// Load env vars
dotenv.config({ path: '.env.local' });
dotenv.config({ path: '.env' });

const connectionString = `${process.env.DATABASE_URL}`;
const pool = new Pool({ connectionString });
const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

// Initialise Firebase Admin SDK (inline — scripts can't use Next.js path aliases)
if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert({
      projectId: process.env.FIREBASE_PROJECT_ID,
      clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
      // Replace escaped \n sequences with real newlines (common in .env files)
      privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
    }),
  });
}
const adminAuth = admin.auth();

// NOTE: Authentication is handled by Firebase.
// Users are created automatically in PostgreSQL on first sign-in via the
// NextAuth credentials provider (auth.ts). This seed file pre-creates the
// Prisma rows for known accounts AND sets Firebase custom claims so that
// plan/role is embedded in the ID token (tamper-proof, server-set).
async function main() {
  console.log('👤 Seeding users...');

  const users: { name: string; email: string; plan: Plan; credits: number }[] = [
    {
      name: 'Ashok Admin',
      email: 'ashok.pdcs@gmail.com',
      plan: Plan.PRO,
      credits: 1000,
    }

  ];

  for (const u of users) {
    // ── 1. Resolve Firebase UID ──────────────────────────────────────────
    let firebaseUid: string;
    try {
      const fbUser = await adminAuth.getUserByEmail(u.email);
      firebaseUid = fbUser.uid;
      console.log(`  🔥 Firebase user found for ${u.email} (uid: ${firebaseUid})`);
    } catch {
      // User doesn't exist in Firebase yet — create them
      const fbUser = await adminAuth.createUser({
        email: u.email,
        displayName: u.name,
        emailVerified: true,
      });
      firebaseUid = fbUser.uid;
      console.log(`  🔥 Firebase user created for ${u.email} (uid: ${firebaseUid})`);
    }

    // ── 2. Set custom claims — plan is embedded in every ID token ────────
    await adminAuth.setCustomUserClaims(firebaseUid, { plan: u.plan });
    console.log(`  🏷️  Custom claims set: { plan: "${u.plan}" } for ${u.email}`);

    // ── 3. Upsert Postgres row with real firebaseUid ─────────────────────
    const user = await prisma.user.upsert({
      where: { email: u.email },
      update: {
        firebaseUid,
        plan: u.plan,
        credits: u.credits,
      },
      create: {
        name: u.name,
        email: u.email,
        firebaseUid,
        plan: u.plan,
        credits: u.credits,
        image: `https://api.dicebear.com/7.x/avataaars/svg?seed=${u.name.replace(/\s/g, '')}`,
      },
    });
    console.log(`  ✅ DB user ${user.email} upserted (plan: ${user.plan})\n`);
  }

  console.log('✨ User seeding complete!');
}

main()
  .then(async () => {
    await prisma.$disconnect();
    await pool.end();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    await pool.end();
    process.exit(1);
  });
