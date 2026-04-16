import { PrismaClient, payability_status, billing_mode, policy_type, hospital_type, Plan, ReportStatus, FileType, JobStatus } from '@prisma/client';
import { Pool } from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';
import * as dotenv from 'dotenv';
import { randomUUID } from 'crypto';

dotenv.config({ path: '.env.local' });

// Ensure DATABASE_URL is available
const connectionString = `${process.env.DATABASE_URL}`;
const pool = new Pool({ connectionString });
const adapter = new PrismaPg(pool);

const prisma = new PrismaClient({ adapter });

async function main() {
  console.log('🌱 Starting seeding...');

  // 1. Seed Insurers (Sync with API default insurers)
  const insurers = [
    { code: 'STAR_HEALTH', name: 'Star Health & Allied Insurance', room_rent_default: 3000 },
    { code: 'HDFC_ERGO', name: 'HDFC ERGO General Insurance', room_rent_default: 4000 },
    { code: 'ICICI_LOMBARD', name: 'ICICI Lombard General Insurance', room_rent_default: 3500 },
    { code: 'BAJAJ_ALLIANZ', name: 'Bajaj Allianz General Insurance', room_rent_default: 3000 },
    { code: 'NIVA_BUPA', name: 'Niva Bupa Health Insurance', room_rent_default: 5000 },
    { code: 'NEW_INDIA', name: 'New India Assurance', room_rent_default: 2500 },
    { code: 'CARE_HEALTH', name: 'Care Health Insurance', room_rent_default: 4000 },
  ];

  console.log('Creating/Updating Insurers...');
  const seededInsurers = [];
  for (const ins of insurers) {
    const insurer = await prisma.insurers.upsert({
      where: { code: ins.code },
      update: {
        name: ins.name,
        room_rent_default: ins.room_rent_default,
      },
      create: {
        id: randomUUID(),
        code: ins.code,
        name: ins.name,
        room_rent_default: ins.room_rent_default,
        is_active: true,
      },
    });
    seededInsurers.push(insurer);
  }

  // 2. Seed Test User
  console.log('Creating Test User...');
  const testUser = await prisma.user.upsert({
    where: { email: 'test@example.com' },
    update: {},
    create: {
      name: 'Test User',
      email: 'test@example.com',
      image: 'https://api.dicebear.com/7.x/avataaars/svg?seed=test',
      plan: Plan.PRO,
      credits: 10,
    },
  });

  // 3. Seed Sample Upload Jobs
  console.log('Creating Sample Upload Jobs...');
  const jobs = [
    {
      userId: testUser.id,
      r2Key: 'sample-bill-1.pdf',
      originalFilename: 'Hospital_Bill_Jan.pdf',
      fileType: FileType.PDF,
      status: JobStatus.ANALYZED,
    },
    {
      userId: testUser.id,
      r2Key: 'sample-bill-2.jpg',
      originalFilename: 'Pharmacy_Invoice.jpg',
      fileType: FileType.IMAGE,
      status: JobStatus.PARSED,
    }
  ];

  for (const job of jobs) {
    await prisma.uploadJob.create({
      data: job
    });
  }

  // 4. Seed Sample Reports
  console.log('Creating Sample Reports...');
  const starHealth = seededInsurers.find(i => i.code === 'STAR_HEALTH');
  
  if (starHealth) {
    await prisma.report.create({
      data: {
        userId: testUser.id,
        analysisId: randomUUID(), // Mock FastAPI analysis ID
        insurerName: starHealth.name,
        insurerCode: starHealth.code,
        diagnosis: 'Dengue Fever with Thrombocytopenia',
        totalBilled: 85000,
        totalPayable: 72000,
        totalAtRisk: 13000,
        rejectionPct: 15.2,
        status: ReportStatus.COMPLETE,
      }
    });
  }

  console.log('✅ Seeding completed successfully!');
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
