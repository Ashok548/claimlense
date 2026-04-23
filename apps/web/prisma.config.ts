import { defineConfig } from "@prisma/config";
import { withRequiredTls } from "./lib/database-url";

const databaseUrl = withRequiredTls(process.env.DATABASE_URL);

if (!databaseUrl) {
  throw new Error("DATABASE_URL is not set.");
}

export default defineConfig({
  schema: "prisma/schema.prisma",
  datasource: {
    url: databaseUrl,
  },
  migrations: {
    seed: "tsx prisma/seed.ts",
  },
});