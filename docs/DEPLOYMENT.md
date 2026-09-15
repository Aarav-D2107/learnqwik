# Deployment

Three services: **Supabase** (database, auth, storage), **Render** (FastAPI
backend), **Vercel** (static frontend). All three have free tiers that are
enough for a hackathon demo.

Do them in this order. The backend needs Supabase; the frontend needs the
backend's URL.

---

## 1. Supabase

1. Create a project at [supabase.com](https://supabase.com). Save the database
   password somewhere — you won't be shown it again.
2. **SQL Editor** → New query → paste all of `database/schema.sql` → **Run**.
3. New query → paste all of `database/seed.sql` → **Run**.
4. Verify:
   ```sql
   select (select count(*) from subjects)  as subjects,
          (select count(*) from topics)    as topics,
          (select count(*) from questions) as questions,
          (select count(*) from resources) as resources;
   ```
   Expect **5 / 30 / 100 / 14**.
5. **Storage** → confirm the `learnqwik-documents` bucket exists (schema.sql
   creates it). It must be **private**.
6. **Settings → API** → copy three values:
   - Project URL → `SUPABASE_URL`
   - `anon` `public` key → `SUPABASE_ANON_KEY`
   - `service_role` `secret` key → `SUPABASE_SERVICE_ROLE_KEY`

> The `service_role` key bypasses Row Level Security. It goes on the backend
> only. It must never appear in Vercel, in the frontend, or in git.

**For the fastest demo**, turn off email confirmation:
Authentication → Providers → Email → disable *Confirm email*. Otherwise every
new signup has to click a link before they can log in.

---

## 2. Render (backend)

### Blueprint (recommended)
1. Push this repo to GitHub.
2. Render → **New** → **Blueprint** → select the repo. It reads `render.yaml`.
3. Fill in the values marked `sync: false`:

| Variable | Value |
|---|---|
| `SUPABASE_URL` | from step 1 |
| `SUPABASE_ANON_KEY` | from step 1 |
| `SUPABASE_SERVICE_ROLE_KEY` | from step 1 |
| `AI_API_KEY` | your Anthropic or OpenAI key |
| `FRONTEND_URL` | your Vercel URL — **set this after step 3** |

4. Deploy. First build takes 3–5 minutes (PyMuPDF compiles).
5. Check `https://<service>.onrender.com/health` → `"status": "healthy"`.

### Manual
- **Root Directory**: `backend`
- **Build**: `pip install -r requirements.txt`
- **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health check path**: `/health`

`--host 0.0.0.0` and `$PORT` are both required. Binding `127.0.0.1` or a fixed
port makes Render's health check fail and the deploy will be marked unhealthy.

### Free tier: the cold start
Render's free web services sleep after ~15 minutes idle and take 30–60 seconds
to wake. **Hit your `/health` URL a few minutes before demoing.** A judge
watching a spinner for a minute will assume it's broken.

---

## 3. Vercel (frontend)

1. Vercel → **Add New** → **Project** → import the repo.
2. **Root Directory**: `frontend`
3. Framework preset: **Other**. Vercel reads `frontend/vercel.json` for the
   rest (`buildCommand: node build.js`).
4. Environment variable:

| Variable | Value |
|---|---|
| `API_BASE_URL` | `https://<your-service>.onrender.com` — **no trailing slash** |

5. Deploy.

`build.js` generates `js/env.js` from that variable. It **fails the build** if
the variable is missing, or if it points at localhost during a Vercel build —
a frontend on the internet cannot reach your laptop, and failing loudly beats
shipping a site whose every request errors.

---

## 4. Close the CORS loop

Go back to Render and set `FRONTEND_URL` to your exact Vercel origin:

```
FRONTEND_URL=https://learnqwik.vercel.app
```

No trailing slash, no path. Redeploy.

For preview deployments, add them to `EXTRA_CORS_ORIGINS` as a comma-separated
list. CORS is never `*` in production — `test_cors_never_uses_wildcard_in_production`
enforces that.

---

## 5. Smoke test

```bash
curl https://<service>.onrender.com/health
curl https://<service>.onrender.com/api/config
curl https://<service>.onrender.com/api/subjects | head -c 300
```

Then in the browser, with devtools open on the Network tab:

- [ ] Landing page loads, subject cards appear (proves the API is reachable)
- [ ] Sign up → you land on Subjects
- [ ] Open a topic → content renders
- [ ] Ask the AI Tutor something unscripted → a real answer, not a template
- [ ] Roadmap says `DEFAULT ROADMAP`
- [ ] Take a quiz → fullscreen prompt → timer runs
- [ ] Submit → weighted score differs from raw on a mixed quiz
- [ ] Roadmap now says `PERSONALIZED ROADMAP`, weakest topic first
- [ ] Reassess → before/after delta appears
- [ ] Upload a PDF → real pipeline stages → ask about a diagram → cited page
- [ ] No CORS errors and no 4xx/5xx in the console

---

## Troubleshooting

**CORS error in the browser console**
`FRONTEND_URL` on Render doesn't exactly match the origin. Check for a trailing
slash, `http` vs `https`, or a preview URL that isn't in `EXTRA_CORS_ORIGINS`.

**Every API call returns 503 `SUPABASE_NOT_CONFIGURED`**
`SUPABASE_URL` or `SUPABASE_SERVICE_ROLE_KEY` is missing on Render. Check for
whitespace pasted around the key.

**The AI Tutor returns 503 `AI_NOT_CONFIGURED`**
Working as designed — `AI_API_KEY` isn't set. It refuses rather than faking an
answer. Set the key and redeploy.

**Signup says "check your inbox" and nothing arrives**
Supabase email confirmation is on and the free tier's built-in mailer is
rate-limited. Turn confirmation off for the demo.

**Uploads fail with `UNSUPPORTED_FILE_TYPE` on a real PDF**
The file is probably corrupt or renamed — `document_parser.sniff_mime()` checks
magic numbers, not just the extension.

**Render build fails on PyMuPDF**
Confirm `PYTHON_VERSION` is `3.12.8`. PyMuPDF wheels lag on very new Python
releases.

**The frontend loads but every request 404s**
`API_BASE_URL` has a trailing slash, producing `//api/subjects`. Remove it and
redeploy.

**Everything is slow on the first request after a break**
Render free-tier cold start. Expected. Warm it before demoing.
