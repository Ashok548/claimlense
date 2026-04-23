import { PrismaClient } from '@prisma/client';
import { Pool } from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';
import { getPgSslConfig, toPgPoolConnectionString, withRequiredTls } from './database-url';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

const connectionString = withRequiredTls(process.env.DATABASE_POOL_URL ?? process.env.DATABASE_URL);

if (!connectionString) {
  throw new Error('DATABASE_POOL_URL or DATABASE_URL is not set.');
}

const ssl = getPgSslConfig(connectionString);
const pool = new Pool({
  connectionString: toPgPoolConnectionString(connectionString),
  ...(ssl ? { ssl } : {}),
});
const adapter = new PrismaPg(pool);

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    adapter,
    log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
  });

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
