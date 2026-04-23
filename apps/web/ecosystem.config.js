/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require("node:fs");
const path = require("node:path");

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  return fs
    .readFileSync(filePath, "utf8")
    .split(/\r?\n/)
    .reduce((env, line) => {
      const trimmed = line.trim();

      if (!trimmed || trimmed.startsWith("#")) {
        return env;
      }

      const match = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
      if (!match) {
        return env;
      }

      const [, key, rawValue] = match;
      let value = rawValue;

      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1);
      }

      env[key] = value
        .replace(/\\n/g, "\n")
        .replace(/\\r/g, "\r")
        .replace(/\\t/g, "\t")
        .replace(/\\"/g, '"')
        .replace(/\\\\/g, "\\");

      return env;
    }, {});
}

const appRoot = __dirname;
const productionEnv = parseEnvFile(path.join(appRoot, ".env.production"));

module.exports = {
  apps: [
    {
      name: "claimsmart-web",
      script: ".next/standalone/apps/web/server.js",
      interpreter: "node",
      cwd: appRoot,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "512M",

      env_production: {
        ...process.env,
        ...productionEnv,
        NODE_ENV: "production",
        PORT: "3000",
        HOSTNAME: "0.0.0.0",
      },
    },
  ],
};
