/* ============================================================
   RUNTIME ENVIRONMENT

   In production this file is overwritten at build time by
   frontend/build.js from the Vercel environment variables.
   The value below is the LOCAL DEVELOPMENT default, which is
   why this file IS committed — a fresh clone needs it to run.

   Only non-secret, browser-safe values ever appear here.
   The AI API key and the Supabase service-role key live on the
   backend and must never be written into this file.
   ============================================================ */
window.LEARNQWIK_ENV = {
  API_BASE_URL: "http://localhost:8000"
};
