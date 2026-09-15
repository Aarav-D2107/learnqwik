#!/usr/bin/env node
/**
 * Generates js/env.js from environment variables at build time.
 *
 * This is what lets a plain static frontend read configuration without
 * hard-coding a backend URL. Vercel runs it via the buildCommand in
 * vercel.json; locally you can run `node build.js` yourself.
 *
 * Accepts either API_BASE_URL or NEXT_PUBLIC_API_URL, so the same variable
 * name works if this is ever migrated to Next.js.
 *
 * No dependencies.
 */
const fs = require("fs");
const path = require("path");

const apiBase = (
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  ""
).replace(/\/+$/, "");

if (!apiBase) {
  console.error(
    "\nBUILD FAILED: no backend URL configured.\n\n" +
      "Set API_BASE_URL (or NEXT_PUBLIC_API_URL) to your deployed FastAPI URL,\n" +
      "for example https://learnqwik-api.onrender.com\n\n" +
      "On Vercel: Project Settings -> Environment Variables.\n"
  );
  process.exit(1);
}

if (/localhost|127\.0\.0\.1/.test(apiBase) && process.env.VERCEL) {
  console.error(
    "\nBUILD FAILED: API_BASE_URL points at localhost on a Vercel build.\n" +
      "A deployed frontend cannot reach your laptop. Set it to your Render URL.\n"
  );
  process.exit(1);
}

// Guard against a secret being pasted into a browser-visible variable.
const forbidden = ["SERVICE_ROLE", "AI_API_KEY", "sk-", "sk-ant-"];
for (const marker of forbidden) {
  if (apiBase.includes(marker)) {
    console.error("\nBUILD FAILED: API_BASE_URL looks like it contains a secret.\n");
    process.exit(1);
  }
}

const contents = `/* GENERATED AT BUILD TIME by frontend/build.js — do not edit. */
window.LEARNQWIK_ENV = {
  API_BASE_URL: ${JSON.stringify(apiBase)}
};
`;

fs.writeFileSync(path.join(__dirname, "js", "env.js"), contents, "utf8");
console.log("Wrote js/env.js with API_BASE_URL=" + apiBase);
