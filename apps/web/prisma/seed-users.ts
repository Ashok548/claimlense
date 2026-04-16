import { PrismaClient, Plan } from '@prisma/client';
import { Pool } from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';
import * as dotenv from 'dotenv';
import bcrypt from 'bcryptjs';

// Load env vars
dotenv.config({ path: '.env.local' });
dotenv.config({ path: '.env' });

const connectionString = `${process.env.DATABASE_URL}`;
const pool = new Pool({ connectionString });
const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

async function main() {
  console.log('👤 Seeding users...');

  const users = [
    {
      name: 'Ashok Admin',
      email: 'ashok@example.com',
      password: 'password123',
      plan: Plan.PRO,
      credits: 100,
    },
    {
      name: 'Rupa User',
      email: 'rupa@example.com',
      password: 'password123',
      plan: Plan.FREE,
      credits: 5,
    },
    {
      name: 'Demo Account',
      email: 'demo@claimsmart.ai',
      password: 'demo-password',
      plan: Plan.B2B,
      credits: 999,
    }
  ];

  for (const u of users) {
    const hashedPassword = await bcrypt.hash(u.password, 10);

    const user = await prisma.user.upsert({
      where: { email: u.email },
      update: {
        password: hashedPassword,
        plan: u.plan,
        credits: u.credits,
      },
      create: {
        name: u.name,
        email: u.email,
        password: hashedPassword,
        plan: u.plan,
        credits: u.credits,
        image: `https://api.dicebear.com/7.x/avataaars/svg?seed=${u.name.replace(/\s/g, '')}`,

      },
    });
    console.log(`✅ User ${user.email} seeded.`);
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
