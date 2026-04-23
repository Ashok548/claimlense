const SUPABASE_HOST_SUFFIX = ".supabase.co";
const SUPABASE_POOLER_HOST_SUFFIX = ".pooler.supabase.com";

export function withRequiredTls(rawUrl: string | undefined): string | undefined {
  if (!rawUrl) {
    return rawUrl;
  }

  try {
    const url = new URL(rawUrl);
    const isPostgres =
      url.protocol === "postgres:" ||
      url.protocol === "postgresql:" ||
      url.protocol === "prisma+postgres:";

    if (!isPostgres) {
      return rawUrl;
    }

    const hasSslMode = url.searchParams.has("sslmode");
    const isSupabasePooler = url.hostname.endsWith(SUPABASE_POOLER_HOST_SUFFIX);
    const shouldRequireTls =
      url.hostname.endsWith(SUPABASE_HOST_SUFFIX) ||
      isSupabasePooler ||
      process.env.PGSSLMODE === "require";

    if (!hasSslMode && shouldRequireTls) {
      url.searchParams.set("sslmode", "require");
    }

    if (isSupabasePooler && !url.searchParams.has("sslaccept")) {
      url.searchParams.set("sslaccept", "accept_invalid_certs");
    }

    return url.toString();
  } catch {
    return rawUrl;
  }
}

export function getPgSslConfig(connectionString: string) {
  try {
    const url = new URL(connectionString);
    const sslMode = url.searchParams.get("sslmode")?.toLowerCase();

    if (sslMode !== "require") {
      return undefined;
    }

    const sslAccept = url.searchParams.get("sslaccept")?.toLowerCase();

    return {
      rejectUnauthorized: sslAccept !== "accept_invalid_certs",
    };
  } catch {
    return undefined;
  }
}

export function toPgPoolConnectionString(connectionString: string) {
  try {
    const url = new URL(connectionString);

    url.searchParams.delete("sslmode");
    url.searchParams.delete("sslaccept");
    url.searchParams.delete("uselibpqcompat");

    return url.toString();
  } catch {
    return connectionString;
  }
}