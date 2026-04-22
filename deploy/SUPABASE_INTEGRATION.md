# Supabase Integration Checklist

## Required Supabase Details

Collect these from Supabase Dashboard -> Project Settings -> Database:

1. Project reference
2. Database host
3. Database port (5432)
4. Database name (postgres)
5. Database user (postgres)
6. Database password

## Runtime Connection Strings

API (`apps/api/.env`):

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:<SUPABASE_DB_PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?sslmode=require
```

Web (`apps/web/.env.local`):

```dotenv
DATABASE_URL=postgresql://postgres:<SUPABASE_DB_PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?schema=public&sslmode=require
```

## Deploy + Validate

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm api python -m seeds.runner
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
```

## Smoke Test

1. Visit app login page.
2. Sign in and open reports/dashboard.
3. Run parse/analyze flow.
4. Confirm rows are created in DB-backed screens.

## Notes

1. Keep Firebase auth and Cloudflare R2 unchanged.
2. Keep Alembic as schema source of truth for backend.
3. If you hit connection limits later, switch to Supabase pooler endpoint for web runtime.
