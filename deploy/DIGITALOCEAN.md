# DigitalOcean Deployment Runbook

## 1) Provision

1. Create a Droplet (Ubuntu 24.04, minimum 2 vCPU / 4 GB RAM).
2. Create a Supabase project (if not already created).
3. Point DNS records:
   - @ -> Droplet public IP
   - www -> Droplet public IP
   - api -> Droplet public IP
4. Open firewall ports: `22`, `80`, `443`.

## 2) Install Docker on Droplet

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Log out and log back in once.

## 3) Clone Project

```bash
git clone <YOUR_REPO_URL> claimAnalyse
cd claimAnalyse
```

## 4) Configure Deploy Domain Variables

```bash
cp .env.prod.example .env
```

Edit `.env` and set:

- `APP_DOMAIN` (example: `claimsmart.in`)
- `ACME_EMAIL` (Let's Encrypt email)

## 5) Configure App Env Files

Create `apps/api/.env` and set:

```dotenv
# Supabase direct connection (FastAPI runtime)
DATABASE_URL=postgresql+asyncpg://postgres:<SUPABASE_DB_PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?sslmode=require
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o
R2_ENDPOINT_URL=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=claimsmart-bills
FIREBASE_PROJECT_ID=...
FIREBASE_CLIENT_EMAIL=...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
APP_ENV=production
INTERNAL_API_SECRET=<LONG_RANDOM_SECRET>
```

Create `apps/web/.env.local` and set:

```dotenv
NODE_ENV=production
# Supabase direct connection (Web runtime)
DATABASE_URL=postgresql://postgres:<SUPABASE_DB_PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?schema=public&sslmode=require
FASTAPI_INTERNAL_URL=http://api:8000
FASTAPI_INTERNAL_SECRET=<SAME_INTERNAL_API_SECRET>
INTERNAL_API_SECRET=<SAME_INTERNAL_API_SECRET>
R2_ENDPOINT_URL=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=claimsmart-bills
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
NEXT_PUBLIC_RAZORPAY_KEY_ID=...
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...
FIREBASE_PROJECT_ID=...
FIREBASE_CLIENT_EMAIL=...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=<LONG_RANDOM_SECRET>
AUTH_TRUST_HOST=true
```

Supabase details needed:

- Project reference
- Database host
- Database password
- Port (5432)
- Database name (postgres)

## 6) Build and Start Services

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## 7) Run Migrations + Seed Data

```bash
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm api python -m seeds.runner
```

## 8) Verify

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f caddy
```

Health check (from server):

```bash
curl http://localhost:8000/health
```

Optional DB connectivity checks:

```bash
docker compose -f docker-compose.prod.yml run --rm api python - <<'PY'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os

async def main():
   engine = create_async_engine(os.environ["DATABASE_URL"])
   async with engine.connect() as conn:
      result = await conn.execute(__import__("sqlalchemy").text("select 1"))
      print("DB OK:", result.scalar())
   await engine.dispose()

asyncio.run(main())
PY
```

## 9) Update Deployment After New Commits

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
```
