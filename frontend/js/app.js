/* ============================================================
   LEARNQWIK — APPLICATION LOGIC

   Routing, views, and the quiz shell. The visual identity, markup and
   CSS class names are unchanged from the prototype.

   What changed under the hood:
     - the backend is the source of truth for every user-specific number
     - the AI Tutor calls a real model through POST /api/ai/tutor
     - documents are really parsed, really analyzed, really indexed
     - localStorage holds the session token and UI preferences only

   Scoring, mastery, recommendations and roadmap generation all happen
   server-side. The client renders what the server decided.
   ============================================================ */

/* ---------------------- Runtime config ---------------------- */
const CONFIG = {
  SECONDS_PER_QUESTION: 60,
  MAX_FULLSCREEN_VIOLATIONS: 3,
  MAX_UPLOAD_MB: 20,
  ACCEPTED_EXT: ["pdf", "pptx", "docx", "txt", "py", "java", "c", "cpp", "js", "ts", "html", "css", "sql"],
  AI_CONFIGURED: true,
};

/* UI-only preferences. No learning data is ever stored here. */
const Prefs = {
  get(key, fallback) {
    try {
      const v = localStorage.getItem("lq_pref_" + key);
      return v ? JSON.parse(v) : fallback;
    } catch (e) {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem("lq_pref_" + key, JSON.stringify(value));
    } catch (e) {}
  },
};

/* In-memory only. Wiped on refresh and rebuilt from the API. */
let State = {
  user: null,
  quiz: null,
  docQuiz: null,
  tutor: {},
  docTutor: {},
  lastResult: null,
  subjectsCache: null,
  booted: false,
};

/* ---------------------- Toasts ---------------------- */
function toast(msg, kind) {
  const host = document.getElementById("toast-host");
  if (!host) return;
  const t = document.createElement("div");
  t.className = "toast neu";
  t.style.borderLeft =
    "3px solid " +
    (kind === "error" ? "var(--magenta)" : kind === "warn" ? "var(--amber)" : "var(--cyan)");
  t.textContent = msg;
  host.appendChild(t);
  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transition = "opacity .3s";
    setTimeout(() => t.remove(), 300);
  }, 4000);
}

/* ---------------------- Shared UI helpers ---------------------- */
function escapeHtml(str) {
  return String(str === null || str === undefined ? "" : str).replace(
    /[&<>"']/g,
    (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch])
  );
}

/** Minimal markdown for AI replies: **bold**, `code`, fenced blocks, newlines. */
function renderMarkdown(text) {
  const blocks = String(text === null || text === undefined ? "" : text).split(/```/);
  return blocks
    .map((block, i) => {
      if (i % 2 === 1) {
        const firstLine = block.split("\n")[0].trim();
        const lang = /^[a-z0-9+#]+$/i.test(firstLine) ? firstLine : "";
        const code = lang ? block.slice(firstLine.length) : block;
        return `<div class="code-block"><span class="code-lang mono">${escapeHtml(
          lang || "code"
        )}</span><button class="copy-btn" onclick="copyCode(this)">⧉</button><pre>${escapeHtml(
          code.replace(/^\n/, "")
        )}</pre></div>`;
      }
      return escapeHtml(block)
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, '<code class="mono">$1</code>')
        .replace(/\n/g, "<br/>");
    })
    .join("");
}

function loadingBlock(label) {
  return `<div class="wrap empty-state">
    <div class="mono" style="color:var(--cyan); letter-spacing:2px; font-size:13px;">${escapeHtml(
      label || "LOADING"
    )}…</div>
  </div>`;
}

function errorBlock(error, retryFn) {
  const message = error && error.message ? error.message : "Something went wrong.";
  const canRetry = !error || !(error instanceof ApiError) || error.retryable;
  return `<div class="wrap empty-state">
    <div style="font-weight:600; margin-bottom:10px; color:var(--magenta);">${escapeHtml(message)}</div>
    ${
      error && error.code
        ? `<div class="mono" style="font-size:11.5px; color:var(--text-faint); margin-bottom:16px;">${escapeHtml(
            error.code
          )}</div>`
        : ""
    }
    ${
      canRetry && retryFn
        ? `<button class="btn btn-secondary btn-sm" onclick="${retryFn}">Try again</button>`
        : ""
    }
  </div>`;
}

function masteryBand(pct) {
  if (pct === null || pct === undefined) return { label: "Not assessed", color: "var(--text-faint)" };
  if (pct <= 39) return { label: "Weak", color: "#ff2e6e" };
  if (pct <= 59) return { label: "Struggling", color: "#ffb02e" };
  if (pct <= 79) return { label: "Developing", color: "#00fff5" };
  return { label: "Mastered", color: "#39ff88" };
}

function formatTime(sec) {
  const s = Math.max(0, Math.floor(sec || 0));
  const m = Math.floor(s / 60);
  return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

function copyCode(btn) {
  const pre = btn.parentElement.querySelector("pre");
  navigator.clipboard.writeText(pre.textContent).then(() => {
    btn.textContent = "✓";
    setTimeout(() => (btn.textContent = "⧉"), 1200);
  });
}

/* ---------------------- Router ---------------------- */
function nav(hash) {
  window.location.hash = hash;
}
function currentRoute() {
  return window.location.hash || "#/";
}

function requireAuth() {
  if (!Auth.isSignedIn()) {
    toast("Please sign in first", "warn");
    nav("#/auth/login");
    return false;
  }
  return true;
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", boot);

async function boot() {
  // Pull non-secret runtime rules from the backend so quiz behaviour matches
  // the server's configuration rather than a hard-coded copy.
  try {
    const cfg = await Api.runtimeConfig();
    CONFIG.SECONDS_PER_QUESTION = cfg.seconds_per_question;
    CONFIG.MAX_FULLSCREEN_VIOLATIONS = cfg.max_fullscreen_violations;
    CONFIG.MAX_UPLOAD_MB = cfg.max_upload_size_mb;
    CONFIG.ACCEPTED_EXT = cfg.allowed_extensions || CONFIG.ACCEPTED_EXT;
    CONFIG.AI_CONFIGURED = cfg.ai_configured;
    if (!cfg.ai_configured) {
      console.warn("LearnQwik: the backend has no AI credentials configured.");
    }
  } catch (e) {
    console.warn("LearnQwik: backend unreachable at boot —", e.message);
  }

  if (Auth.isSignedIn()) {
    try {
      State.user = await Auth.hydrate();
    } catch (e) {
      State.user = null;
    }
  }
  State.booted = true;
  render();
}

async function render() {
  const hash = currentRoute();
  const app = document.getElementById("app");
  if (!app) return;
  const parts = hash.replace("#/", "").split("/").filter(Boolean);

  const isQuizRoute = parts[0] === "quiz" || parts[0] === "reassess";
  const chrome = (html) =>
    `${renderNavbar(hash)}<div class="view">${html}</div>${isQuizRoute ? "" : renderFooter()}`;

  // Paint the shell immediately so navigation always feels instant, then swap
  // in the real content once the backend responds.
  let html;
  try {
    html = await routeView(parts, (label) => {
      app.innerHTML = chrome(loadingBlock(label));
    });
  } catch (error) {
    if (error instanceof ApiError && error.isAuthError) {
      Auth.clearSession();
      State.user = null;
      html = errorBlock(
        { message: "Your session expired. Please sign in again.", code: "SESSION_EXPIRED" },
        "nav('#/auth/login')"
      );
    } else {
      console.error(error);
      html = errorBlock(error, "render()");
    }
  }

  app.innerHTML = chrome(html);
  window.scrollTo(0, 0);
  afterRender(parts);
}

async function routeView(parts, showLoading) {
  if (parts.length === 0) return viewLanding(showLoading);
  if (parts[0] === "auth") return viewAuth(parts[1] || "login");
  if (parts[0] === "subjects" && parts.length === 1) return viewSubjects(showLoading);
  if (parts[0] === "subject" && parts.length === 2) return viewTopics(parts[1], showLoading);
  if (parts[0] === "subject" && parts.length === 3) return viewContent(parts[1], parts[2], showLoading);
  if (parts[0] === "quiz" && parts.length === 3) return viewQuizHost(parts[1], parts[2], "quiz", showLoading);
  if (parts[0] === "reassess" && parts.length === 3) return viewQuizHost(parts[1], parts[2], "reassess", showLoading);
  if (parts[0] === "results") return viewResults();
  if (parts[0] === "roadmap" && parts.length === 2) return viewRoadmap(parts[1], showLoading);
  if (parts[0] === "dashboard") return viewDashboard(showLoading);
  if (parts[0] === "upload" && parts.length === 1) return viewUpload(showLoading);
  if (parts[0] === "document" && parts.length === 2) return viewDocument(parts[1], showLoading);
  if (parts[0] === "profile") return viewProfile();
  return viewLanding(showLoading);
}

function afterRender(parts) {
  if ((parts[0] === "quiz" || parts[0] === "reassess") && State.quiz && State.quiz.phase === "active") {
    startTimerLoop();
  }
  if (parts[0] === "subject" && parts.length === 3) {
    const box = document.getElementById("tutor-messages");
    if (box) box.scrollTop = box.scrollHeight;
  }
  if (parts[0] === "document") {
    const box = document.getElementById("doc-tutor-messages");
    if (box) box.scrollTop = box.scrollHeight;
  }
}

/* ---------------------- Navbar / Footer ---------------------- */
function renderNavbar(hash) {
  const links = [
    ["#/subjects", "Subjects"],
    ["#/upload", "Study Your Own Material"],
    ["#/dashboard", "My Progress"],
  ];
  const isQuiz = hash.startsWith("#/quiz") || hash.startsWith("#/reassess");
  if (isQuiz && State.quiz && State.quiz.phase === "active") return ""; // hidden during assessment

  const user = Auth.user();
  return `
  <nav class="navbar">
    <div class="wrap">
      <div class="brand" onclick="nav('#/')">
        <div class="brand-mark">LQ</div>
        <div class="brand-name">Learn<span>Qwik</span></div>
      </div>
      <div class="nav-links">
        ${links
          .map(
            ([href, label]) =>
              `<div class="nav-link ${hash.startsWith(href) ? "active" : ""}" onclick="nav('${href}')">${label}</div>`
          )
          .join("")}
        ${
          user
            ? `<div class="nav-link ${hash.startsWith("#/profile") ? "active" : ""}" onclick="nav('#/profile')">${escapeHtml(
                user.full_name || user.email
              )}</div>`
            : `<div class="btn btn-primary btn-sm" onclick="nav('#/auth/login')" style="margin-left:8px;">Sign In</div>`
        }
      </div>
    </div>
  </nav>`;
}

function renderFooter() {
  return `<footer class="footer wrap">LearnQwik — Your AI-powered personalized learning companion. Built for the Quality Education track.</footer>`;
}

/* ---------------------- Landing ---------------------- */
async function viewLanding(showLoading) {
  const featured = [
    { icon: "◈", color: "var(--cyan)", title: "Personalized Learning", desc: "Every recommendation is scored against your actual mastery, not guesswork." },
    { icon: "▣", color: "var(--magenta)", title: "AI Tutor", desc: "Context-aware help on every topic — explanations, examples, and debugging support." },
    { icon: "◭", color: "var(--amber)", title: "Smart Assessments", desc: "Timed, fullscreen-monitored quizzes with real difficulty-weighted scoring." },
    { icon: "▤", color: "var(--violet)", title: "Document Intelligence", desc: "Upload your own material — a hybrid text + vision pipeline builds understanding." },
    { icon: "◫", color: "var(--green)", title: "Personalized Roadmaps", desc: "Weak concepts become a concrete, ordered study plan with real resources." },
    { icon: "◪", color: "var(--cyan)", title: "Progress Analytics", desc: "Mastery trends, topic breakdowns, and measurable before/after improvement." },
  ];

  let subjects = [];
  try {
    subjects = (await getSubjects()).subjects || [];
  } catch (e) {
    /* the landing page still renders without the subject grid */
  }

  return `
  <section class="hero wrap">
    <div class="hero-kicker"><span class="dot"></span> AI TUTOR · SMART ASSESSMENTS · PERSONALIZED ROADMAPS</div>
    <h1>Learn what you need<br/>Improve what you don't.</h1>
    <p class="hero-sub">LearnQwik assesses your knowledge, diagnoses the gaps, teaches you the exact concept you're missing, and proves — with numbers — that you improved.</p>
    <div class="hero-kicker"><span class="dot"></span> PERSONALIZED EDUCATION · BUILT AROUND YOU</div>
    <div class="hero-cta">
      <button class="btn btn-primary" onclick="nav('${Auth.isSignedIn() ? "#/subjects" : "#/auth/signup"}')">Start Your Journey</button>
      <button class="btn btn-secondary" onclick="nav('#/subjects')">Explore Subjects</button>
    </div>
    <div class="hero-loop">
      ${["Assess", "Diagnose", "Learn", "Practice", "Reassess", "Improve"]
        .map(
          (s, i, a) =>
            `<span class="loop-step mono">${s}</span>${i < a.length - 1 ? '<span class="loop-arrow">→</span>' : ""}`
        )
        .join("")}
    </div>
  </section>
  <section class="section wrap">
    <div class="section-head">
      <span class="eyebrow">WHAT'S INSIDE</span>
      <h2>Six systems, one learning loop.</h2>
      <p>Every feature below feeds the same core cycle: figure out what you don't know, then close the gap.</p>
    </div>
    <div class="feature-grid">
      ${featured
        .map(
          (f) => `
        <div class="neu feature-card">
          <div class="feature-icon" style="background:rgba(255,255,255,0.04); color:${f.color};">${f.icon}</div>
          <h3>${f.title}</h3>
          <p>${f.desc}</p>
        </div>`
        )
        .join("")}
    </div>
  </section>
  ${
    subjects.length
      ? `<section class="section wrap">
    <div class="section-head">
      <span class="eyebrow">SUBJECTS</span>
      <h2>${subjects.length} subjects, ${subjects.reduce((a, s) => a + (s.topic_count || 0), 0)} topics.</h2>
    </div>
    <div class="subject-grid">
      ${subjects.map(renderSubjectCard).join("")}
    </div>
  </section>`
      : ""
  }`;
}

/* ---------------------- Auth ---------------------- */
function viewAuth(mode) {
  const isSignup = mode === "signup";
  return `
  <div class="wrap">
    <div class="neu auth-box">
      <h2 style="margin-bottom:6px;">${isSignup ? "Create your account" : "Welcome back"}</h2>
      <p style="margin-bottom:26px; font-size:13.5px;">${
        isSignup
          ? "Your progress, mastery scores and roadmap are saved to your account."
          : "Sign in to pick up where you left off."
      }</p>
      ${isSignup ? `<label>Name</label><input id="auth-name" placeholder="Aisha Rahman" autocomplete="name"/>` : ""}
      <label>Email</label><input id="auth-email" type="email" placeholder="you@college.edu" autocomplete="email"/>
      <label>Password</label><input id="auth-pass" type="password" placeholder="••••••••" autocomplete="${
        isSignup ? "new-password" : "current-password"
      }" onkeydown="if(event.key==='Enter'){doAuth('${mode}')}"/>
      ${
        isSignup
          ? `<div class="mono" style="font-size:11.5px; color:var(--text-faint); margin:-8px 0 14px;">At least 8 characters.</div>`
          : ""
      }
      <div id="auth-error" style="display:none; color:var(--magenta); font-size:13px; margin-bottom:12px;"></div>
      <button class="btn btn-primary btn-block" id="auth-submit" style="margin-top:6px;" onclick="doAuth('${mode}')">${
        isSignup ? "Sign Up" : "Log In"
      }</button>
      <div style="text-align:center; margin-top:18px; font-size:13px; color:var(--text-faint);">
        ${
          isSignup
            ? `Already have an account? <span class="link-btn" onclick="nav('#/auth/login')">Log in</span>`
            : `New here? <span class="link-btn" onclick="nav('#/auth/signup')">Create an account</span>`
        }
      </div>
    </div>
  </div>`;
}

async function doAuth(mode) {
  const email = (document.getElementById("auth-email").value || "").trim();
  const password = document.getElementById("auth-pass").value || "";
  const nameEl = document.getElementById("auth-name");
  const fullName = nameEl ? nameEl.value.trim() : null;
  const errorEl = document.getElementById("auth-error");
  const button = document.getElementById("auth-submit");

  const showError = (msg) => {
    errorEl.textContent = msg;
    errorEl.style.display = "block";
  };
  errorEl.style.display = "none";

  if (!email) return showError("Enter your email address.");
  if (!password) return showError("Enter your password.");
  if (mode === "signup" && password.length < 8)
    return showError("Passwords need to be at least 8 characters.");

  button.disabled = true;
  button.textContent = mode === "signup" ? "Creating account…" : "Signing in…";

  try {
    if (mode === "signup") {
      const result = await Auth.signUp(email, password, fullName);
      if (!result.signedIn) {
        showError(result.message || "Check your inbox to confirm your email, then log in.");
        button.disabled = false;
        button.textContent = "Sign Up";
        return;
      }
      State.user = result.user;
      toast(`Welcome to LearnQwik, ${result.user.full_name}!`);
    } else {
      const user = await Auth.signIn(email, password);
      State.user = user;
      toast(`Welcome back, ${user.full_name}!`);
    }
    State.subjectsCache = null;
    nav("#/subjects");
  } catch (error) {
    showError(error.message || "That didn't work. Please try again.");
    button.disabled = false;
    button.textContent = mode === "signup" ? "Sign Up" : "Log In";
  }
}

async function logout() {
  await Auth.signOut();
  State.user = null;
  State.quiz = null;
  State.tutor = {};
  State.docTutor = {};
  State.lastResult = null;
  State.subjectsCache = null;
  toast("Signed out");
  nav("#/");
}

/* ---------------------- Subjects ---------------------- */
async function getSubjects() {
  if (State.subjectsCache) return State.subjectsCache;
  const data = await Api.subjects();
  State.subjectsCache = data;
  return data;
}

function renderSubjectCard(s) {
  const pct = Math.round(s.mastery_pct || 0);
  return `
  <div class="neu subject-card" style="--accent:${s.color};" onclick="nav('#/subject/${s.id}')">
    <div class="subj-name">${escapeHtml(s.name)}</div>
    <p class="subj-tagline">${escapeHtml(s.tagline || "")}</p>
    <div class="subject-meta"><span>${s.topic_count} topics</span><span>${pct}% mastery</span></div>
    <div class="progress-bar neu-inset"><div class="progress-bar-fill" style="width:${pct}%; background:${s.color};"></div></div>
  </div>`;
}

async function viewSubjects(showLoading) {
  if (showLoading) showLoading("LOADING SUBJECTS");
  State.subjectsCache = null;
  const data = await getSubjects();
  const subjects = data.subjects || [];

  if (!subjects.length) {
    return `<div class="wrap empty-state">
      <div style="font-weight:600; margin-bottom:8px;">No subjects found.</div>
      <p style="font-size:13.5px;">The curriculum hasn't been seeded yet. Run <code class="mono">database/seed.sql</code> in Supabase.</p>
    </div>`;
  }

  return `
  <section class="section wrap">
    <div class="section-head">
      <span class="eyebrow">SUBJECTS</span>
      <h2>Pick a subject to begin.</h2>
      <p>${
        Auth.isSignedIn()
          ? "Mastery percentages come from your completed assessments."
          : "Sign in to track your mastery across topics."
      }</p>
    </div>
    <div class="subject-grid">${subjects.map(renderSubjectCard).join("")}</div>
  </section>`;
}

/* ---------------------- Topics ---------------------- */
async function viewTopics(subjectId, showLoading) {
  if (showLoading) showLoading("LOADING TOPICS");
  const data = await Api.topics(subjectId);
  const subject = data.subject;
  const topics = data.topics || [];
  const assessed = topics.filter((t) => t.mastery_pct !== null && t.mastery_pct !== undefined);

  return `
  <section class="section wrap">
    <div class="section-head">
      <span class="eyebrow">${escapeHtml(subject.name.toUpperCase())}</span>
      <h2>${escapeHtml(subject.tagline || subject.name)}</h2>
      <p>${topics.length} topics${
        assessed.length ? ` · ${assessed.length} assessed` : " · none assessed yet"
      }</p>
    </div>

    <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:26px;">
      <button class="btn btn-primary" onclick="nav('#/roadmap/${subject.id}')">View My Roadmap</button>
      ${
        Auth.isSignedIn()
          ? ""
          : `<button class="btn btn-secondary" onclick="nav('#/auth/signup')">Sign in to track progress</button>`
      }
    </div>

    <div class="subject-grid">
      ${topics
        .map((t) => {
          const band = masteryBand(t.mastery_pct);
          const pct = t.mastery_pct === null || t.mastery_pct === undefined ? 0 : Math.round(t.mastery_pct);
          return `
        <div class="neu subject-card" style="--accent:${band.color};" onclick="nav('#/subject/${subject.id}/${t.id}')">
          <div class="subj-name" style="font-size:18px;">${escapeHtml(t.name)}</div>
          <p class="subj-tagline">${escapeHtml(t.description || "")}</p>
          <div class="subject-meta">
            <span style="color:${band.color};">${band.label}</span>
            <span>${t.mastery_pct === null || t.mastery_pct === undefined ? "—" : pct + "%"}</span>
          </div>
          <div class="progress-bar neu-inset"><div class="progress-bar-fill" style="width:${pct}%; background:${band.color};"></div></div>
        </div>`;
        })
        .join("")}
    </div>
  </section>`;
}

/* ---------------------- Topic content + AI Tutor ---------------------- */
async function viewContent(subjectId, topicId, showLoading) {
  if (showLoading) showLoading("LOADING TOPIC");
  const data = await Api.topic(topicId);
  const subject = data.subject;
  const topic = data.topic;
  const c = topic.content || {};
  const mastery = data.mastery;

  if (!State.tutor[topicId]) {
    State.tutor[topicId] = [
      {
        role: "assistant",
        content: `I'm the LearnQwik AI Tutor and I can see you're on **${topic.name}**. Ask me to explain a concept, walk through an example, compare two ideas, or check where your reasoning went wrong.`,
      },
    ];
  }

  const band = mastery ? masteryBand(mastery.mastery_pct) : null;

  return `
  <section class="section wrap">
    <div class="content-layout">
      <div class="neu content-panel">
        <div class="subj-crumb mono">${escapeHtml(subject.name.toUpperCase())} / ${escapeHtml(
    topic.name.toUpperCase()
  )}</div>
        <h2>${escapeHtml(topic.name)}</h2>
        <p style="margin-bottom:${band ? "12px" : "24px"};">${escapeHtml(topic.description || "")}</p>
        ${
          band
            ? `<div class="badge" style="background:rgba(255,255,255,0.05); color:${
                band.color
              }; margin-bottom:24px;">Your mastery: ${Math.round(mastery.mastery_pct)}% · ${band.label}</div>`
            : ""
        }

        ${c.intro ? `<div class="content-block"><h4>Introduction</h4><p>${escapeHtml(c.intro)}</p></div>` : ""}
        ${
          c.concepts
            ? `<div class="content-block"><h4>Key Concepts</h4><ul>${c.concepts
                .map((x) => `<li>${escapeHtml(x)}</li>`)
                .join("")}</ul></div>`
            : ""
        }
        ${
          c.practical
            ? `<div class="content-block"><h4>Practical Explanation</h4><p>${escapeHtml(c.practical)}</p></div>`
            : ""
        }
        ${
          c.examples && c.examples.length
            ? `<div class="content-block"><h4>Code Example</h4>
          ${c.examples
            .map(
              (ex) => `
          <div class="code-block">
            <span class="code-lang mono">${escapeHtml(ex.lang)}</span>
            <button class="copy-btn" onclick="copyCode(this)">⧉</button>
            <pre>${escapeHtml(ex.code)}</pre>
          </div>`
            )
            .join("")}
        </div>`
            : ""
        }
        ${
          c.mistakes
            ? `<div class="content-block"><h4>Common Mistakes</h4>
          ${c.mistakes
            .map(
              (x) =>
                `<div class="mistake-item"><span class="tick glow-magenta">✕</span><span>${escapeHtml(x)}</span></div>`
            )
            .join("")}
        </div>`
            : ""
        }
        ${
          c.important
            ? `<div class="content-block"><h4>Important Points</h4>
          ${c.important
            .map(
              (x) =>
                `<div class="important-item"><span class="tick glow-cyan">✓</span><span>${escapeHtml(x)}</span></div>`
            )
            .join("")}
        </div>`
            : ""
        }

        <div class="divider"></div>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
          <button class="btn btn-primary" onclick="nav('#/quiz/${subject.id}/${topic.id}')">Take the Quiz</button>
          <button class="btn btn-secondary" onclick="nav('#/roadmap/${subject.id}')">View Roadmap</button>
        </div>
      </div>

      <div class="neu tutor-panel">
        <div class="tutor-head">
          <span class="pip"></span>
          <div><strong>LearnQwik AI</strong><small>Context: ${escapeHtml(topic.name)}</small></div>
        </div>
        <div class="tutor-messages" id="tutor-messages">
          ${State.tutor[topicId]
            .map(
              (m) =>
                `<div class="tutor-msg ${m.role === "user" ? "user" : "bot"}">${renderMarkdown(m.content)}</div>`
            )
            .join("")}
        </div>
        <div class="tutor-quick">
          ${["Explain this simply", "Give me an example", "Common mistakes?", "Practice question"]
            .map(
              (q) => `<span class="chip" onclick="askTutor('${topicId}', '${q.replace(/'/g, "")}')">${q}</span>`
            )
            .join("")}
        </div>
        <div class="tutor-input">
          <input id="tutor-input" placeholder="Ask the AI Tutor..." onkeydown="if(event.key==='Enter'){askTutorFromInput('${topicId}')}"/>
          <button class="btn btn-primary btn-sm" id="tutor-send" onclick="askTutorFromInput('${topicId}')">Send</button>
        </div>
      </div>
    </div>
  </section>`;
}

function askTutorFromInput(topicId) {
  const input = document.getElementById("tutor-input");
  const val = (input.value || "").trim();
  if (!val) return;
  input.value = "";
  askTutor(topicId, val);
}

/**
 * Sends the question to the real model via POST /api/ai/tutor. The backend
 * grounds the reply in this topic's learning content, the student's measured
 * mastery, their weak areas, and the conversation so far.
 */
async function askTutor(topicId, message) {
  if (!Auth.isSignedIn()) {
    toast("Sign in to use the AI Tutor", "warn");
    nav("#/auth/login");
    return;
  }

  const history = State.tutor[topicId] || (State.tutor[topicId] = []);
  const priorTurns = history.slice(-12);
  history.push({ role: "user", content: message });

  const box = document.getElementById("tutor-messages");
  const sendBtn = document.getElementById("tutor-send");
  if (box) {
    box.insertAdjacentHTML("beforeend", `<div class="tutor-msg user">${escapeHtml(message)}</div>`);
    box.insertAdjacentHTML(
      "beforeend",
      `<div class="tutor-msg bot" id="tutor-thinking"><span class="mono" style="color:var(--cyan);">thinking…</span></div>`
    );
    box.scrollTop = box.scrollHeight;
  }
  if (sendBtn) sendBtn.disabled = true;

  let reply;
  try {
    const data = await Api.askTutor({ message, topic: topicId, conversation: priorTurns });
    reply = data.reply;
  } catch (error) {
    reply =
      error.code === "TUTOR_LOCKED_DURING_QUIZ"
        ? "The AI Tutor is unavailable during an active assessment. Submit your quiz first."
        : error.isAiConfigError
        ? "The AI Tutor isn't configured on this deployment yet. The backend needs AI_PROVIDER and AI_API_KEY set — see the README."
        : error.message || "The AI Tutor couldn't respond. Please try again.";
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    const thinking = document.getElementById("tutor-thinking");
    if (thinking) thinking.remove();
  }

  history.push({ role: "assistant", content: reply });

  const liveBox = document.getElementById("tutor-messages");
  if (liveBox) {
    liveBox.insertAdjacentHTML("beforeend", `<div class="tutor-msg bot">${renderMarkdown(reply)}</div>`);
    liveBox.scrollTop = liveBox.scrollHeight;
  }
}

/* ---------------------- Quiz Engine ---------------------- */
async function viewQuizHost(subjectId, topicId, mode, showLoading) {
  if (!requireAuth()) return loadingBlock("REDIRECTING");

  if (
    State.quiz &&
    State.quiz.topicId === topicId &&
    State.quiz.mode === mode &&
    State.quiz.phase === "active"
  ) {
    return renderActiveQuiz();
  }

  if (showLoading) showLoading("PREPARING ASSESSMENT");
  const data = await Api.topic(topicId);
  const topic = data.topic;

  return `
  <div class="quiz-shell wrap">
    <div class="neu quiz-intro">
      <div class="warn-icon">⛶</div>
      <h2>${mode === "reassess" ? "Targeted Reassessment" : "Assessment"}: ${escapeHtml(topic.name)}</h2>
      <p style="margin:16px 0 22px;">This assessment requires fullscreen mode. Leaving fullscreen during the assessment will trigger an integrity warning. After ${
        CONFIG.MAX_FULLSCREEN_VIOLATIONS
      } violations, the assessment auto-submits.</p>
      <p style="font-size:13.5px; color:var(--text-faint); margin-bottom:8px;">Your answers are saved to your account as you go and scored on the server. The AI Tutor is locked until you submit.</p>
      <p class="mono" style="font-size:12.5px; color:var(--text-faint);">Basic assessment integrity monitoring — not secure proctoring.</p>
      <button class="btn btn-primary" id="begin-quiz-btn" style="margin-top:10px;" onclick="beginQuiz('${subjectId}','${topicId}','${mode}')">Enter Fullscreen &amp; Begin</button>
    </div>
  </div>`;
}

async function beginQuiz(subjectId, topicId, mode) {
  const button = document.getElementById("begin-quiz-btn");
  if (button) {
    button.disabled = true;
    button.textContent = "Starting…";
  }

  try {
    const session =
      mode === "reassess"
        ? await Api.startReassessment(subjectId, topicId)
        : await Api.startQuiz(subjectId, topicId, mode);

    State.quiz = {
      attemptId: session.attempt_id,
      subjectId,
      topicId,
      subjectName: session.subject.name,
      topicName: session.topic.name,
      mode,
      questions: session.questions,
      answers: new Array(session.questions.length).fill(null),
      current: 0,
      phase: "active",
      startedAt: Date.now(),
      questionShownAt: Date.now(),
      remainingSec: session.total_seconds,
      totalSec: session.total_seconds,
      violations: 0,
      submitting: false,
    };
    CONFIG.MAX_FULLSCREEN_VIOLATIONS = session.max_fullscreen_violations;

    const el = document.documentElement;
    const req = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen;
    if (req) {
      req.call(el).catch(() => toast("Fullscreen was blocked by your browser — continuing without it.", "warn"));
    }
    document.addEventListener("fullscreenchange", onFullscreenChange);
    render();
  } catch (error) {
    if (button) {
      button.disabled = false;
      button.textContent = "Enter Fullscreen & Begin";
    }
    toast(error.message || "Couldn't start the assessment.", "error");
  }
}

function onFullscreenChange() {
  if (!State.quiz || State.quiz.phase !== "active") return;
  if (!document.fullscreenElement) {
    State.quiz.violations++;
    if (State.quiz.violations >= CONFIG.MAX_FULLSCREEN_VIOLATIONS) {
      toast("Too many fullscreen exits — assessment submitted automatically.", "error");
      submitQuiz(true);
    } else {
      toast(
        `Fullscreen exited (${State.quiz.violations}/${CONFIG.MAX_FULLSCREEN_VIOLATIONS}). Return to fullscreen to continue.`,
        "warn"
      );
      render();
    }
  }
}

function returnToFullscreen() {
  const el = document.documentElement;
  const req = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen;
  if (req) req.call(el);
}

let timerHandle = null;
function startTimerLoop() {
  clearInterval(timerHandle);
  timerHandle = setInterval(() => {
    if (!State.quiz || State.quiz.phase !== "active") {
      clearInterval(timerHandle);
      return;
    }
    State.quiz.remainingSec--;
    const el = document.getElementById("quiz-timer");
    if (el) {
      el.textContent = formatTime(State.quiz.remainingSec);
      el.classList.toggle("low", State.quiz.remainingSec < 60);
    }
    if (State.quiz.remainingSec <= 0) {
      clearInterval(timerHandle);
      toast("Time's up — submitting your assessment.", "warn");
      submitQuiz(false);
    }
  }, 1000);
}

function renderActiveQuiz() {
  const q = State.quiz;
  const question = q.questions[q.current];
  const answered = q.answers.filter((a) => a !== null).length;
  const progress = ((q.current + 1) / q.questions.length) * 100;

  return `
  <div class="quiz-shell wrap">
    <div class="quiz-topbar">
      <div class="quiz-meta">${escapeHtml(q.subjectName.toUpperCase())} / ${escapeHtml(
    q.topicName.toUpperCase()
  )}</div>
      <div class="neu timer-pill ${q.remainingSec < 60 ? "low" : ""}" id="quiz-timer">${formatTime(q.remainingSec)}</div>
      <div class="quiz-meta" style="color:${
        q.violations ? "var(--magenta)" : "var(--text-faint)"
      };">FS ${q.violations}/${CONFIG.MAX_FULLSCREEN_VIOLATIONS}</div>
    </div>

    ${
      !document.fullscreenElement
        ? `<div class="violation-banner">
        <span>You've left fullscreen. Return to it to continue the assessment.</span>
        <button class="btn btn-secondary btn-sm" style="margin-left:auto;" onclick="returnToFullscreen()">Return to Fullscreen</button>
      </div>`
        : ""
    }

    <div class="quiz-progress-track">
      <div class="quiz-progress-fill" style="width:${progress}%;"></div>
    </div>

    <div class="neu question-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
        <span class="mono" style="font-size:12.5px; color:var(--text-faint);">QUESTION ${q.current + 1} OF ${
    q.questions.length
  }</span>
        <span class="badge" style="background:rgba(255,255,255,0.05); color:${
          question.difficulty === "Hard"
            ? "var(--magenta)"
            : question.difficulty === "Medium"
            ? "var(--amber)"
            : "var(--green)"
        };">${escapeHtml(question.difficulty)}</span>
      </div>

      <h3 style="margin-bottom:22px; line-height:1.5;">${escapeHtml(question.question)}</h3>

      <div class="option-list">
        ${question.options
          .map(
            (opt, i) => `
          <div class="neu option-item ${q.answers[q.current] === i ? "selected" : ""}" onclick="selectOption(${i})">
            <span class="opt-letter mono">${String.fromCharCode(65 + i)}</span>
            <span>${escapeHtml(opt)}</span>
          </div>`
          )
          .join("")}
      </div>

      <div class="quiz-nav">
        <button class="btn btn-secondary btn-sm" onclick="prevQuestion()" ${
          q.current === 0 ? "disabled" : ""
        }>Previous</button>
        <span class="mono" style="font-size:12.5px; color:var(--text-faint);">${answered}/${
    q.questions.length
  } answered</span>
        ${
          q.current === q.questions.length - 1
            ? `<button class="btn btn-primary btn-sm" id="submit-btn" onclick="submitQuiz(false)">Submit Assessment</button>`
            : `<button class="btn btn-primary btn-sm" onclick="nextQuestion()">Next</button>`
        }
      </div>
    </div>
  </div>`;
}

function selectOption(i) {
  const q = State.quiz;
  if (!q || q.phase !== "active") return;
  q.answers[q.current] = i;

  // Persist each answer as it's made, with the response time. If the browser
  // dies mid-quiz the work isn't lost, and the server has the real timings.
  const question = q.questions[q.current];
  const elapsed = Date.now() - q.questionShownAt;
  Api.saveAnswer(q.attemptId, question.id, i, elapsed).catch(() => {
    /* reconciled by the flush in submitQuiz() */
  });

  render();
}

function nextQuestion() {
  if (State.quiz.current < State.quiz.questions.length - 1) {
    State.quiz.current++;
    State.quiz.questionShownAt = Date.now();
    render();
  }
}
function prevQuestion() {
  if (State.quiz.current > 0) {
    State.quiz.current--;
    State.quiz.questionShownAt = Date.now();
    render();
  }
}

/**
 * Submits to the backend, which scores the attempt, recalculates mastery,
 * regenerates the roadmap and returns everything in one response.
 */
async function submitQuiz(fromViolation) {
  const q = State.quiz;
  if (!q || q.submitting) return;
  q.submitting = true;

  clearInterval(timerHandle);
  document.removeEventListener("fullscreenchange", onFullscreenChange);
  if (document.exitFullscreen && document.fullscreenElement) {
    document.exitFullscreen().catch(() => {});
  }

  const app = document.getElementById("app");
  if (app) {
    app.innerHTML = `<div class="view">${loadingBlock(
      "SCORING · ANALYZING MASTERY · UPDATING YOUR ROADMAP"
    )}</div>`;
  }

  // Flush any answers that failed to save during the quiz.
  for (let i = 0; i < q.questions.length; i++) {
    if (q.answers[i] === null) continue;
    try {
      await Api.saveAnswer(q.attemptId, q.questions[i].id, q.answers[i], null);
    } catch (e) {
      /* already saved, or it will be scored as unanswered */
    }
  }

  const timeUsed = Math.max(0, q.totalSec - q.remainingSec);

  try {
    const result = await Api.completeQuiz(q.attemptId, q.violations, !!fromViolation, timeUsed);
    State.lastResult = result;
    q.phase = "done";
    State.subjectsCache = null;
    if (result.roadmap_updated) {
      toast("Your roadmap has been updated based on your assessment.");
    }
    if (currentRoute() === "#/results") {
      render();
    } else {
      nav("#/results");
    }
  } catch (error) {
    q.phase = "done";
    toast(error.message || "Your assessment couldn't be submitted.", "error");
    const host = document.getElementById("app");
    if (host) {
      host.innerHTML = `<div class="view">${errorBlock(
        error,
        `nav('#/subject/${q.subjectId}/${q.topicId}')`
      )}</div>`;
    }
  }
}

/* ---------------------- Results ---------------------- */
function viewResults() {
  const result = State.lastResult;
  if (!result) {
    return `<div class="wrap empty-state">No results to show. <span class="link-btn" onclick="nav('#/subjects')">Take a quiz</span></div>`;
  }

  const score = result.score;
  const band = masteryBand(result.mastery.mastery_pct);
  const isReassess = result.mode === "reassess";
  const cmp = result.comparison || {};
  const delta = cmp.delta;
  const hasBefore = cmp.before !== null && cmp.before !== undefined;

  return `
  <section class="wrap results-hero">
    <div class="score-ring neu-inset" style="box-shadow: inset 5px 5px 12px var(--shadow-dark), inset -4px -4px 10px var(--shadow-light), 0 0 40px ${
      band.color
    }33;">
      <div class="score-num" style="color:${band.color};">${score.raw_percentage}%</div>
    </div>
    <h2>${isReassess ? "Reassessment Complete" : "Assessment Complete"}</h2>
    <p>${escapeHtml(result.subject.name)} / ${escapeHtml(result.topic.name)}</p>
  </section>

  <section class="wrap">
    ${
      hasBefore
        ? `
    <div class="neu" style="padding:28px; text-align:center; margin-bottom:28px;">
      <div class="mono" style="color:var(--text-faint); font-size:12.5px; margin-bottom:10px;">BEFORE vs AFTER</div>
      <div style="display:flex; justify-content:center; align-items:center; gap:20px; font-family:var(--font-display); font-size:30px; flex-wrap:wrap;">
        <span style="color:var(--text-faint);">${Math.round(cmp.before)}%</span>
        <span style="color:var(--text-faint);">→</span>
        <span class="glow-cyan">${Math.round(cmp.after)}%</span>
        <span class="badge" style="background:${
          delta >= 0 ? "rgba(57,255,136,0.15)" : "rgba(255,46,110,0.15)"
        }; color:${delta >= 0 ? "var(--green)" : "var(--magenta)"};">${delta >= 0 ? "+" : ""}${delta} pts</span>
      </div>
      <p style="margin-top:12px; font-size:13.5px;">${escapeHtml(cmp.summary || "")}</p>
    </div>`
        : ""
    }

    <div class="results-grid">
      <div class="neu stat-card"><div class="stat-val">${score.correct_count}/${
    score.total_questions
  }</div><div class="stat-label">Correct</div></div>
      <div class="neu stat-card"><div class="stat-val">${
        score.weighted_percentage
      }%</div><div class="stat-label">Weighted Score</div></div>
      <div class="neu stat-card"><div class="stat-val">${formatTime(
        score.time_used_seconds
      )}</div><div class="stat-label">Time Used</div></div>
      <div class="neu stat-card"><div class="stat-val" style="color:${band.color};">${
    band.label
  }</div><div class="stat-label">Current Mastery</div></div>
    </div>

    <div class="breakdown-grid">
      <div class="neu breakdown-card">
        <h4>Difficulty Breakdown</h4>
        ${Object.entries(score.difficulty_breakdown)
          .filter(([, v]) => v.total > 0)
          .map(
            ([diff, v]) => `
          <div class="bar-row">
            <span class="bar-label">${diff}</span>
            <div class="bar-track"><div style="height:100%; width:${
              (v.correct / v.total) * 100
            }%; background:${
              diff === "Hard" ? "var(--magenta)" : diff === "Medium" ? "var(--amber)" : "var(--green)"
            }; border-radius:8px;"></div></div>
            <span class="bar-val">${v.correct}/${v.total}</span>
          </div>`
          )
          .join("")}
        <div class="mono" style="font-size:11.5px; color:var(--text-faint); margin-top:14px;">Easy ×1.0 · Medium ×1.5 · Hard ×2.0</div>
      </div>
      <div class="neu breakdown-card">
        <h4>AI Explanation</h4>
        <p style="font-size:13.5px;">${renderMarkdown(result.explanation)}</p>
      </div>
    </div>

    ${
      result.roadmap_updated
        ? `
    <div class="neu" style="padding:26px; margin-top:26px; border-left:3px solid var(--green);">
      <div class="mono" style="font-size:12px; color:var(--green); letter-spacing:1.5px; margin-bottom:10px;">ROADMAP UPDATED</div>
      <h3 style="margin-bottom:10px;">Your roadmap has been updated based on your assessment.</h3>
      <p style="font-size:13.5px; margin-bottom:16px;">${escapeHtml(result.roadmap.reason || "")}</p>
      ${renderRoadmapChanges(result.roadmap_changes)}
      <button class="btn btn-primary btn-sm" style="margin-top:16px;" onclick="nav('#/roadmap/${
        result.subject.id
      }')">See My Personalized Roadmap</button>
    </div>`
        : ""
    }

    ${
      result.recommendations && result.recommendations.length
        ? `
    <div class="divider"></div>
    <div class="section-head">
      <span class="eyebrow">RECOMMENDED NEXT STEPS</span>
      <h2 style="font-size:24px;">Close the gap in ${escapeHtml(result.topic.name)}</h2>
    </div>
    <div class="subject-grid" style="margin-bottom:30px;">
      ${result.recommendations.map(renderRecommendationCard).join("")}
    </div>`
        : ""
    }

    ${
      result.review && result.review.length
        ? `
    <div class="divider"></div>
    <div class="section-head"><span class="eyebrow">REVIEW</span><h2 style="font-size:24px;">Every question, explained</h2></div>
    <div style="display:grid; gap:14px; margin-bottom:30px;">
      ${result.review.map(renderReviewItem).join("")}
    </div>`
        : ""
    }

    <div style="display:flex; gap:12px; flex-wrap:wrap;">
      <button class="btn btn-primary" onclick="nav('#/roadmap/${
        result.subject.id
      }')">View Full Roadmap</button>
      <button class="btn btn-secondary" onclick="nav('#/subject/${result.subject.id}/${
    result.topic.id
  }')">Back to Content</button>
      <button class="btn btn-secondary" onclick="nav('#/dashboard')">Go to Dashboard</button>
    </div>
  </section>`;
}

function renderReviewItem(item) {
  const unanswered = item.selected_index === null || item.selected_index === undefined;
  const correct = !unanswered && item.selected_index === item.correct_index;
  return `
  <div class="neu" style="padding:18px 20px; border-left:3px solid ${
    correct ? "var(--green)" : unanswered ? "var(--text-faint)" : "var(--magenta)"
  };">
    <div style="display:flex; justify-content:space-between; gap:12px; margin-bottom:8px;">
      <strong style="font-size:14px;">${escapeHtml(item.question)}</strong>
      <span class="badge mono" style="background:rgba(255,255,255,0.05); flex-shrink:0;">${escapeHtml(
        item.difficulty || ""
      )}</span>
    </div>
    <div style="font-size:13px; color:var(--text-faint); margin-bottom:6px;">
      ${
        unanswered
          ? "Not answered"
          : correct
          ? "Your answer was correct"
          : `You chose: ${escapeHtml(item.options[item.selected_index])}`
      }
    </div>
    ${
      !correct
        ? `<div style="font-size:13px; color:var(--green); margin-bottom:8px;">Correct: ${escapeHtml(
            item.options[item.correct_index]
          )}</div>`
        : ""
    }
    ${item.explanation ? `<p style="font-size:13px; margin:0;">${escapeHtml(item.explanation)}</p>` : ""}
    ${
      item.source_page
        ? `<div class="mono" style="font-size:11px; color:var(--text-faint); margin-top:8px;">Source: page ${item.source_page}</div>`
        : ""
    }
  </div>`;
}

function renderRecommendationCard(r) {
  return `
  <div class="neu" style="padding:20px;">
    <div style="font-weight:600; margin-bottom:6px;">${escapeHtml(r.title)}</div>
    <div class="mono" style="font-size:11.5px; color:var(--text-faint); margin-bottom:10px;">${escapeHtml(
      r.type
    )} · ~${r.duration_minutes} min · ${escapeHtml(r.difficulty)} · ★ ${r.rating}</div>
    ${r.reason ? `<p style="font-size:12.5px; margin:0 0 10px;">${escapeHtml(r.reason)}</p>` : ""}
    <div class="progress-bar neu-inset" style="height:5px;"><div class="progress-bar-fill" style="width:${
      r.score_percent
    }%; background:var(--cyan);"></div></div>
    <div class="mono" style="font-size:10.5px; color:var(--text-faint); margin-top:6px;">match ${
      r.score_percent
    }%</div>
  </div>`;
}

function renderRoadmapChanges(changes) {
  if (!changes) return "";
  if (changes.is_first_version) {
    return `<div class="mono" style="font-size:12.5px; color:var(--text-faint);">This is your first personalized roadmap.</div>`;
  }
  const added = (changes.added || []).map(
    (t) => `<div style="color:var(--green); font-size:13px;">+ ${escapeHtml(t)}</div>`
  );
  const removed = (changes.removed || []).map(
    (t) => `<div style="color:var(--magenta); font-size:13px;">− ${escapeHtml(t)}</div>`
  );
  if (!added.length && !removed.length && !changes.reordered) return "";
  return `
  <div class="neu-inset" style="padding:16px 18px; border-radius:12px;">
    <div class="mono" style="font-size:11.5px; color:var(--text-faint); letter-spacing:1.5px; margin-bottom:10px;">WHAT CHANGED</div>
    ${added.join("")}
    ${removed.join("")}
    ${
      changes.reordered
        ? `<div style="color:var(--cyan); font-size:13px;">↕ Existing steps reordered by priority</div>`
        : ""
    }
  </div>`;
}

/* ---------------------- Roadmap ---------------------- */
async function viewRoadmap(subjectId, showLoading) {
  if (!requireAuth()) return loadingBlock("REDIRECTING");
  if (showLoading) showLoading("LOADING YOUR ROADMAP");

  const [data, topicsData] = await Promise.all([Api.roadmap(subjectId), Api.topics(subjectId)]);
  const roadmap = data.roadmap;
  const isDefault = data.state === "default";
  const topicNames = {};
  (topicsData.topics || []).forEach((t) => (topicNames[t.id] = t.name));
  const subject = topicsData.subject;

  const priorities = roadmap.priority_topics || [];
  const weakest = priorities.find((p) => p.mastery !== null && p.mastery !== undefined);
  const first = roadmap.steps && roadmap.steps[0];
  const totalMinutes = data.total_estimated_minutes || 0;

  return `
  <section class="section wrap">
    <div class="section-head">
      <span class="eyebrow" style="color:${isDefault ? "var(--text-faint)" : "var(--green)"};">
        ${isDefault ? "DEFAULT ROADMAP" : "PERSONALIZED ROADMAP"}
      </span>
      <h2>${escapeHtml(roadmap.title)}</h2>
      <p>${
        isDefault
          ? "Your personalized roadmap will adapt after your first assessment."
          : `Updated based on your latest assessment${
              data.version_number ? ` · version ${data.version_number}` : ""
            }${data.generated_by === "fallback" ? " · deterministic planner" : ""}`
      }</p>
    </div>

    ${
      isDefault
        ? `<div class="neu" style="padding:22px 24px; margin-bottom:26px; border-left:3px solid var(--cyan);">
        <h4 style="margin:0 0 8px;">Take an assessment to personalize your roadmap.</h4>
        <p style="font-size:13.5px; margin:0 0 14px;">Right now this is the standard curriculum order for ${escapeHtml(
          subject.name
        )}. Once LearnQwik measures what you actually know, the order changes to put your biggest gap first.</p>
        <button class="btn btn-primary btn-sm" onclick="nav('#/subject/${subjectId}')">Start an Assessment</button>
      </div>`
        : `<div class="neu" style="padding:22px 24px; margin-bottom:26px; border-left:3px solid var(--green);">
        <h4 style="margin:0 0 8px;">Why your roadmap looks like this</h4>
        <p style="font-size:13.5px; margin:0 0 14px;">${escapeHtml(roadmap.reason || "")}</p>
        <div class="results-grid" style="margin:0;">
          ${
            weakest
              ? `<div class="neu-inset" style="padding:14px; border-radius:12px;">
              <div class="mono" style="font-size:10.5px; color:var(--text-faint);">HIGHEST PRIORITY</div>
              <div style="font-weight:600; margin-top:4px;">${escapeHtml(weakest.topic_name || "")}</div>
              <div style="font-size:12.5px; color:${masteryBand(weakest.mastery).color};">${Math.round(
                  weakest.mastery
                )}% · ${escapeHtml(weakest.band || "")}</div>
            </div>`
              : ""
          }
          ${
            first
              ? `<div class="neu-inset" style="padding:14px; border-radius:12px;">
              <div class="mono" style="font-size:10.5px; color:var(--text-faint);">NEXT STEP</div>
              <div style="font-weight:600; margin-top:4px;">${escapeHtml(first.title)}</div>
              <div style="font-size:12.5px; color:var(--text-faint);">~${first.estimated_minutes} min</div>
            </div>`
              : ""
          }
          <div class="neu-inset" style="padding:14px; border-radius:12px;">
            <div class="mono" style="font-size:10.5px; color:var(--text-faint);">TOTAL STUDY TIME</div>
            <div style="font-weight:600; margin-top:4px;">${Math.floor(totalMinutes / 60)}h ${
            totalMinutes % 60
          }m</div>
            <div style="font-size:12.5px; color:var(--text-faint);">${roadmap.steps.length} steps</div>
          </div>
        </div>
      </div>`
    }

    ${
      priorities.length
        ? `<div class="neu" style="padding:22px 24px; margin-bottom:26px;">
      <h4 style="margin:0 0 14px;">Priority order</h4>
      ${priorities
        .slice(0, 6)
        .map((p) => {
          const band = masteryBand(p.mastery);
          const pct = p.mastery === null || p.mastery === undefined ? 0 : Math.round(p.mastery);
          return `<div class="bar-row">
            <span class="bar-label" style="min-width:180px;">${escapeHtml(p.topic_name || "")}</span>
            <div class="bar-track"><div style="height:100%; width:${pct}%; background:${
            band.color
          }; border-radius:8px;"></div></div>
            <span class="bar-val" style="color:${band.color};">${
            p.mastery === null || p.mastery === undefined ? "—" : pct + "%"
          }</span>
          </div>`;
        })
        .join("")}
    </div>`
        : ""
    }

    <div class="roadmap-list">
      ${roadmap.steps
        .map((s, i) => {
          const kindColor =
            s.kind === "reassess"
              ? "var(--green)"
              : s.kind === "practice"
              ? "var(--amber)"
              : s.kind === "resource"
              ? "var(--violet)"
              : "var(--cyan)";
          return `
        <div class="roadmap-item">
          <div class="roadmap-num" style="border-color:${kindColor};">${i + 1}</div>
          <div class="neu roadmap-body">
            <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start; flex-wrap:wrap;">
              <h4 style="margin:0;">${escapeHtml(s.title)}</h4>
              <span class="badge mono" style="background:rgba(255,255,255,0.05); color:${kindColor};">${escapeHtml(
            (s.kind || "learn").toUpperCase()
          )} · ${s.estimated_minutes}m</span>
            </div>
            ${s.reason ? `<p style="margin:8px 0 0; font-size:13px;">${escapeHtml(s.reason)}</p>` : ""}
            <div style="display:flex; gap:8px; margin-top:12px; flex-wrap:wrap;">
              ${
                s.kind === "reassess"
                  ? `<button class="btn btn-primary btn-sm" onclick="nav('#/reassess/${subjectId}/${s.topic_id}')">Reassess Me</button>`
                  : `<button class="btn btn-secondary btn-sm" onclick="nav('#/subject/${subjectId}/${
                      s.topic_id
                    }')">Open ${escapeHtml(topicNames[s.topic_id] || "topic")}</button>`
              }
            </div>
          </div>
        </div>`;
        })
        .join("")}
    </div>

    ${
      !isDefault
        ? `<div style="margin-top:26px; display:flex; gap:12px; flex-wrap:wrap;">
      <button class="btn btn-secondary btn-sm" id="regen-btn" onclick="regenerateRoadmap('${subjectId}')">Regenerate Roadmap</button>
      <button class="btn btn-secondary btn-sm" onclick="nav('#/dashboard')">View Progress</button>
    </div>`
        : ""
    }
  </section>`;
}

async function regenerateRoadmap(subjectId) {
  const btn = document.getElementById("regen-btn");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Regenerating…";
  }
  try {
    await Api.recomputeRoadmap(subjectId);
    toast("Roadmap regenerated.");
    render();
  } catch (error) {
    toast(error.message || "Couldn't regenerate the roadmap.", "error");
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Regenerate Roadmap";
    }
  }
}

/* ---------------------- Dashboard ---------------------- */
async function viewDashboard(showLoading) {
  if (!requireAuth()) return loadingBlock("REDIRECTING");
  if (showLoading) showLoading("LOADING YOUR PROGRESS");

  const [overview, topicData, improvement, recs] = await Promise.all([
    Api.overview(),
    Api.topicAnalytics(),
    Api.improvement().catch(() => ({ improvements: [] })),
    Api.recommendations({ limit: 4 }).catch(() => ({ recommendations: [] })),
  ]);

  if (!overview.has_data) {
    return `
    <section class="section wrap">
      <div class="section-head"><span class="eyebrow">MY PROGRESS</span><h2>Nothing measured yet.</h2></div>
      <div class="neu" style="padding:40px; text-align:center;">
        <div style="font-size:40px; margin-bottom:14px; color:var(--cyan);">◪</div>
        <h3 style="margin-bottom:10px;">${escapeHtml(overview.empty_state)}</h3>
        <button class="btn btn-primary" style="margin-top:14px;" onclick="nav('#/subjects')">Browse Subjects</button>
      </div>
    </section>`;
  }

  const topics = topicData.topics || [];
  const assessed = topics.filter((t) => t.assessed);

  return `
  <section class="section wrap">
    <div class="section-head">
      <span class="eyebrow">MY PROGRESS</span>
      <h2>Where you actually stand.</h2>
      <p>Every number here comes from your completed assessments.</p>
    </div>

    <div class="results-grid">
      <div class="neu stat-card"><div class="stat-val glow-cyan">${
        overview.overall_mastery
      }%</div><div class="stat-label">Overall Mastery</div></div>
      <div class="neu stat-card"><div class="stat-val">${
        overview.total_quizzes
      }</div><div class="stat-label">Assessments Taken</div></div>
      <div class="neu stat-card"><div class="stat-val">${
        overview.subjects_studied
      }</div><div class="stat-label">Subjects Studied</div></div>
      <div class="neu stat-card"><div class="stat-val" style="color:var(--green);">${
        overview.topics_mastered
      }</div><div class="stat-label">Topics Mastered</div></div>
    </div>

    ${
      improvement.improvements && improvement.improvements.length
        ? `
    <div class="divider"></div>
    <div class="section-head"><span class="eyebrow">MEASURED IMPROVEMENT</span><h2 style="font-size:24px;">Proof that it worked</h2></div>
    <div class="subject-grid" style="margin-bottom:10px;">
      ${improvement.improvements
        .slice(0, 4)
        .map(
          (imp) => `
        <div class="neu" style="padding:20px; border-left:3px solid ${
          imp.improved ? "var(--green)" : "var(--amber)"
        };">
          <div style="font-weight:600; margin-bottom:10px;">${escapeHtml(imp.topic_name)}</div>
          <div style="display:flex; align-items:center; gap:12px; font-family:var(--font-display); font-size:22px;">
            <span style="color:var(--text-faint);">${Math.round(imp.before)}%</span>
            <span style="color:var(--text-faint);">→</span>
            <span class="glow-cyan">${Math.round(imp.after)}%</span>
            <span class="badge" style="background:${
              imp.improved ? "rgba(57,255,136,0.15)" : "rgba(255,176,46,0.15)"
            }; color:${imp.improved ? "var(--green)" : "var(--amber)"};">${imp.delta >= 0 ? "+" : ""}${
            imp.delta
          }</span>
          </div>
        </div>`
        )
        .join("")}
    </div>`
        : ""
    }

    ${
      overview.weak_topics && overview.weak_topics.length
        ? `
    <div class="divider"></div>
    <div class="section-head"><span class="eyebrow">YOUR GAPS</span><h2 style="font-size:24px;">Weakest topics first</h2></div>
    <div class="neu" style="padding:24px; margin-bottom:26px;">
      ${overview.weak_topics
        .map((w) => {
          const band = masteryBand(w.mastery_pct);
          return `<div class="bar-row">
          <span class="bar-label" style="min-width:200px;">${escapeHtml(w.topic_name)}</span>
          <div class="bar-track"><div style="height:100%; width:${Math.round(
            w.mastery_pct
          )}%; background:${band.color}; border-radius:8px;"></div></div>
          <span class="bar-val" style="color:${band.color};">${Math.round(w.mastery_pct)}%</span>
        </div>`;
        })
        .join("")}
    </div>`
        : ""
    }

    <div class="divider"></div>
    <div class="section-head"><span class="eyebrow">KNOWLEDGE MAP</span><h2 style="font-size:24px;">${
      assessed.length
    } of ${topics.length} topics assessed</h2></div>
    <div class="neu knowledge-map">
      ${renderKnowledgeMap(topics)}
    </div>

    ${
      overview.recent_scores && overview.recent_scores.length
        ? `
    <div class="divider"></div>
    <div class="section-head"><span class="eyebrow">RECENT ACTIVITY</span><h2 style="font-size:24px;">Your last assessments</h2></div>
    <div style="display:grid; gap:10px; margin-bottom:26px;">
      ${overview.recent_scores
        .map(
          (a) => `
        <div class="neu upload-file-card">
          <div>
            <div class="f-name">${escapeHtml(a.topic_name)}</div>
            <div class="f-meta">${escapeHtml(a.subject_name || "")} · ${
            a.mode === "reassess" ? "Reassessment" : "Assessment"
          } · ${a.completed_at ? new Date(a.completed_at).toLocaleDateString() : ""}</div>
          </div>
          <div class="mono" style="font-size:18px; color:${masteryBand(a.weighted_pct).color};">${
            a.score_pct
          }%</div>
        </div>`
        )
        .join("")}
    </div>`
        : ""
    }

    ${
      recs.recommendations && recs.recommendations.length
        ? `
    <div class="divider"></div>
    <div class="section-head"><span class="eyebrow">RECOMMENDED FOR YOU</span><h2 style="font-size:24px;">Scored against your mastery</h2></div>
    <div class="subject-grid">${recs.recommendations.map(renderRecommendationCard).join("")}</div>`
        : ""
    }
  </section>`;
}


/** Knowledge map, grouped by subject — uses the prototype's km-* row styles. */
function renderKnowledgeMap(topics) {
  const bySubject = {};
  topics.forEach((t) => {
    (bySubject[t.subject_id] = bySubject[t.subject_id] || {
      name: t.subject_name,
      color: t.subject_color,
      rows: [],
    }).rows.push(t);
  });

  return Object.values(bySubject)
    .map(
      (group) => `
    <div class="km-subject">
      <div class="km-subject-name" style="color:${group.color || "var(--text-primary)"};">${escapeHtml(
        group.name || ""
      )}</div>
      ${group.rows
        .map((t) => {
          const band = masteryBand(t.assessed ? t.mastery_pct : null);
          const pct = t.assessed ? Math.round(t.mastery_pct) : 0;
          return `
        <div class="km-row" style="cursor:pointer;" onclick="nav('#/subject/${t.subject_id}/${t.topic_id}')">
          <span class="km-name">${escapeHtml(t.topic_name)}</span>
          <div class="km-track"><div class="km-fill" style="width:${pct}%; background:${
            band.color
          };"></div></div>
          <span class="km-pct" style="color:${band.color};">${t.assessed ? pct + "%" : "—"}</span>
          <span class="km-tag badge" style="background:rgba(255,255,255,0.05); color:${band.color};">${
            band.label
          }</span>
        </div>`;
        })
        .join("")}
    </div>`
    )
    .join("");
}

/* ---------------------- Study Your Own Material ---------------------- */
async function viewUpload(showLoading) {
  if (!requireAuth()) return loadingBlock("REDIRECTING");
  if (showLoading) showLoading("LOADING YOUR MATERIAL");

  const data = await Api.uploads();
  const uploads = data.uploads || [];

  return `
  <section class="section wrap">
    <div class="section-head">
      <span class="eyebrow">STUDY YOUR OWN MATERIAL</span>
      <h2>Upload a document, get a document-grounded quiz.</h2>
      <p>Supports PDF, PPTX, DOCX, TXT and common source files. Max ${
        CONFIG.MAX_UPLOAD_MB
      }MB per file. Pages with diagrams, tables or screenshots are analyzed by a vision model.</p>
    </div>

    <div class="neu dropzone" id="dropzone" onclick="document.getElementById('file-input').click()"
         ondragover="event.preventDefault(); this.classList.add('drag');"
         ondragleave="this.classList.remove('drag');"
         ondrop="handleDrop(event)">
      <div class="dz-icon">⇪</div>
      <div style="font-weight:600; margin-bottom:6px;">Drag &amp; drop a file, or click to browse</div>
      <div class="mono" style="font-size:12px; color:var(--text-faint);">${CONFIG.ACCEPTED_EXT.join(
        " · "
      )}</div>
      <input id="file-input" type="file" style="display:none;" onchange="handleFilePick(event)"/>
    </div>

    <div id="pipeline-host" style="margin-top:24px;"></div>
    <div id="uploads-host" style="margin-top:24px;">${renderUploadsList(uploads)}</div>
  </section>`;
}

function renderUploadsList(uploads) {
  if (!uploads.length) {
    return `<div class="empty-state" style="padding:30px 0;">
      <p style="font-size:13.5px;">Nothing uploaded yet. Your lecture slides, notes or a textbook chapter will do.</p>
    </div>`;
  }
  return `
  <div class="section-head"><span class="eyebrow">YOUR MATERIAL</span><h2 style="font-size:20px;">Uploads</h2></div>
  ${uploads
    .map((u) => {
      const ready = u.status === "ready";
      const failed = u.status === "failed";
      return `
    <div class="neu upload-file-card">
      <div style="min-width:0;">
        <div class="f-name">${escapeHtml(u.original_filename)}</div>
        <div class="f-meta">
          ${escapeHtml((u.file_type || "").toUpperCase())} ·
          ${u.page_count ? u.page_count + " pages · " : ""}
          <span style="color:${
            ready ? "var(--green)" : failed ? "var(--magenta)" : "var(--amber)"
          };">${escapeHtml(
        failed ? u.error_message || "Processing failed" : ready ? "Ready" : "Processing…"
      )}</span>
        </div>
      </div>
      <div style="display:flex; gap:8px; flex-shrink:0;">
        ${
          ready
            ? `<button class="btn btn-primary btn-sm" onclick="nav('#/document/${u.id}')">Open</button>`
            : failed
            ? `<button class="btn btn-secondary btn-sm" onclick="deleteUpload('${u.id}')">Remove</button>`
            : `<button class="btn btn-secondary btn-sm" onclick="pollUpload('${u.id}')">Check status</button>`
        }
      </div>
    </div>`;
    })
    .join("")}`;
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById("dropzone").classList.remove("drag");
  if (e.dataTransfer.files.length) processFile(e.dataTransfer.files[0]);
}
function handleFilePick(e) {
  if (e.target.files.length) processFile(e.target.files[0]);
}

/**
 * Uploads the file, then polls the backend for the REAL processing stage.
 * Nothing here is animated on a timer — each step appears when the server
 * reports it has actually finished that step.
 */
async function processFile(file) {
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  if (!CONFIG.ACCEPTED_EXT.includes(ext)) {
    toast(`.${ext} isn't a supported file type`, "error");
    return;
  }
  if (file.size > CONFIG.MAX_UPLOAD_MB * 1024 * 1024) {
    toast(`File exceeds the ${CONFIG.MAX_UPLOAD_MB}MB limit`, "error");
    return;
  }

  renderPipelineFromStatus({
    status: "uploading",
    stages: [
      { key: "uploading", label: "Uploading", state: "active" },
      { key: "extracting_text", label: "Extracting text", state: "pending" },
      { key: "analyzing_visuals", label: "Analyzing visual content", state: "pending" },
      { key: "building_understanding", label: "Building document understanding", state: "pending" },
      { key: "indexing", label: "Indexing material", state: "pending" },
      { key: "ready", label: "Ready", state: "pending" },
    ],
  });

  let fileId;
  try {
    const result = await Api.uploadDocument(file);
    fileId = result.file_id;
  } catch (error) {
    renderPipelineError(error.message || "Upload failed.");
    toast(error.message || "Upload failed.", "error");
    return;
  }

  await pollUpload(fileId, true);
}

async function pollUpload(fileId, fromUpload) {
  const started = Date.now();
  const TIMEOUT_MS = 5 * 60 * 1000;

  while (Date.now() - started < TIMEOUT_MS) {
    let status;
    try {
      status = await Api.uploadStatus(fileId);
    } catch (error) {
      renderPipelineError(error.message || "Lost contact with the server.");
      return;
    }

    renderPipelineFromStatus(status);

    if (status.status === "ready") {
      toast("Document processed and indexed.");
      await refreshUploadsList();
      setTimeout(() => {
        const p = document.getElementById("pipeline-host");
        if (p) p.innerHTML = "";
      }, 1500);
      if (fromUpload) nav("#/document/" + fileId);
      return;
    }

    if (status.status === "failed") {
      renderPipelineError(status.error_message || "Processing failed.");
      toast(status.error_message || "Processing failed.", "error");
      await refreshUploadsList();
      return;
    }

    await new Promise((r) => setTimeout(r, 1500));
  }

  renderPipelineError("Processing is taking unusually long. Check back in a moment.");
}

async function refreshUploadsList() {
  try {
    const data = await Api.uploads();
    const host = document.getElementById("uploads-host");
    if (host) host.innerHTML = renderUploadsList(data.uploads || []);
  } catch (e) {
    /* the list will refresh on the next navigation */
  }
}

function renderPipelineFromStatus(status) {
  const host = document.getElementById("pipeline-host");
  if (!host) return;
  host.innerHTML = `<div class="neu pipeline-steps" style="padding:20px;">
    ${(status.stages || [])
      .map(
        (s) => `
      <div class="pipeline-step ${s.state === "done" ? "done" : s.state === "active" ? "active" : ""}">
        <span class="p-icon">${s.state === "done" ? "✓" : s.state === "active" ? "…" : ""}</span>
        <span>${escapeHtml(s.label)}</span>
      </div>`
      )
      .join("")}
  </div>`;
}

function renderPipelineError(message) {
  const host = document.getElementById("pipeline-host");
  if (!host) return;
  host.innerHTML = `<div class="neu" style="padding:20px; border-left:3px solid var(--magenta);">
    <div style="font-weight:600; color:var(--magenta); margin-bottom:6px;">Processing failed</div>
    <p style="font-size:13.5px; margin:0;">${escapeHtml(message)}</p>
  </div>`;
}

async function deleteUpload(fileId) {
  try {
    await Api.deleteUpload(fileId);
    toast("Document removed.");
    render();
  } catch (error) {
    toast(error.message || "Couldn't remove that document.", "error");
  }
}

/* ---------------------- Document workspace ---------------------- */
async function viewDocument(fileId, showLoading) {
  if (!requireAuth()) return loadingBlock("REDIRECTING");
  if (showLoading) showLoading("OPENING DOCUMENT");

  const data = await Api.upload(fileId);
  const doc = data.document;
  const pages = data.pages || [];
  const visionPages = pages.filter((p) => p.has_visual_analysis);

  if (!State.docTutor[fileId]) {
    State.docTutor[fileId] = [
      {
        role: "assistant",
        content: `I've read **${doc.original_filename}** — ${doc.page_count} pages${
          visionPages.length ? `, ${visionPages.length} of them analyzed visually` : ""
        }. Ask me anything about it. I'll cite the page, and I'll tell you if something isn't in your material.`,
      },
    ];
  }

  return `
  <section class="section wrap">
    <div class="section-head">
      <span class="eyebrow">YOUR MATERIAL</span>
      <h2>${escapeHtml(doc.original_filename)}</h2>
      <p>${doc.page_count} pages · ${escapeHtml((doc.file_type || "").toUpperCase())} · ${
    visionPages.length
  } page${visionPages.length === 1 ? "" : "s"} analyzed by the vision model</p>
    </div>

    <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:26px;">
      <button class="btn btn-primary" id="summary-btn" onclick="loadDocumentSummary('${fileId}')">Generate Summary</button>
      <button class="btn btn-primary" id="docquiz-btn" onclick="loadDocumentQuiz('${fileId}')">Quiz Me</button>
      <button class="btn btn-secondary btn-sm" onclick="nav('#/upload')">Back to Uploads</button>
    </div>

    <div class="content-layout">
      <div>
        <div id="doc-output"></div>

        <div class="neu" style="padding:22px 24px; margin-top:20px;">
          <h4 style="margin:0 0 14px;">Page analysis</h4>
          <div style="display:grid; gap:8px; max-height:320px; overflow:auto;">
            ${pages
              .map(
                (p) => `
              <div style="display:flex; gap:12px; align-items:center; font-size:12.5px;">
                <span class="mono" style="color:var(--text-faint); min-width:56px;">Page ${
                  p.page_number
                }</span>
                <span class="badge mono" style="background:rgba(255,255,255,0.05); color:${
                  p.content_quality === "scanned"
                    ? "var(--magenta)"
                    : p.content_quality === "mixed"
                    ? "var(--violet)"
                    : p.content_quality === "sparse"
                    ? "var(--amber)"
                    : "var(--cyan)"
                };">${escapeHtml(p.content_quality || "")}</span>
                <span style="color:var(--text-faint);">${escapeHtml(
                  (p.analysis_source || []).join(" + ")
                )}</span>
              </div>`
              )
              .join("")}
          </div>
        </div>
      </div>

      <div class="neu tutor-panel">
        <div class="tutor-head">
          <span class="pip"></span>
          <div><strong>LearnQwik AI</strong><small>Grounded in this document</small></div>
        </div>
        <div class="tutor-messages" id="doc-tutor-messages">
          ${State.docTutor[fileId]
            .map(
              (m) =>
                `<div class="tutor-msg ${m.role === "user" ? "user" : "bot"}">${renderMarkdown(m.content)}</div>`
            )
            .join("")}
        </div>
        <div class="tutor-quick">
          ${["Summarize page 1", "Explain the diagram", "What's likely on the exam?", "Give me a practice question"]
            .map(
              (q) => `<span class="chip" onclick="askDocument('${fileId}', '${q.replace(/'/g, "")}')">${q}</span>`
            )
            .join("")}
        </div>
        <div class="tutor-input">
          <input id="doc-tutor-input" placeholder="Ask about this document..." onkeydown="if(event.key==='Enter'){askDocumentFromInput('${fileId}')}"/>
          <button class="btn btn-primary btn-sm" id="doc-tutor-send" onclick="askDocumentFromInput('${fileId}')">Send</button>
        </div>
      </div>
    </div>
  </section>`;
}

async function loadDocumentSummary(fileId) {
  const btn = document.getElementById("summary-btn");
  const out = document.getElementById("doc-output");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Reading your document…";
  }
  if (out) out.innerHTML = loadingBlock("GENERATING SUMMARY FROM YOUR MATERIAL");

  try {
    const data = await Api.documentSummary(fileId);
    if (out) out.innerHTML = renderSummary(data.summary, data.cached);
  } catch (error) {
    if (out) out.innerHTML = errorBlock(error, `loadDocumentSummary('${fileId}')`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Generate Summary";
    }
  }
}

function renderSummary(summary, cached) {
  const page = (item) =>
    item && item.page
      ? `<span class="mono" style="color:var(--text-faint); font-size:11px;"> (page ${item.page})</span>`
      : "";

  const section = (title, items, render) =>
    items && items.length
      ? `<div class="content-block"><h4>${title}</h4>${items.map(render).join("")}</div>`
      : "";

  return `
  <div class="neu content-panel">
    <div class="subj-crumb mono">DOCUMENT SUMMARY${cached ? " · CACHED" : ""}</div>
    <div class="content-block"><h4>Overview</h4><p>${escapeHtml(summary.overview)}</p></div>
    ${section(
      "Key Concepts",
      summary.key_concepts,
      (i) =>
        `<div class="important-item"><span class="tick glow-cyan">✓</span><span><strong>${escapeHtml(
          i.concept || ""
        )}</strong> — ${escapeHtml(i.explanation || "")}${page(i)}</span></div>`
    )}
    ${section(
      "Definitions",
      summary.definitions,
      (i) =>
        `<div class="important-item"><span class="tick glow-cyan">≡</span><span><strong>${escapeHtml(
          i.term || ""
        )}</strong>: ${escapeHtml(i.definition || "")}${page(i)}</span></div>`
    )}
    ${section(
      "Formulas",
      summary.formulas,
      (i) =>
        `<div class="important-item"><span class="tick glow-cyan">ƒ</span><span><code class="mono">${escapeHtml(
          i.formula || ""
        )}</code> — ${escapeHtml(i.meaning || "")}${page(i)}</span></div>`
    )}
    ${section(
      "Diagrams",
      summary.diagrams,
      (i) =>
        `<div class="important-item"><span class="tick" style="color:var(--violet);">◫</span><span><strong>${escapeHtml(
          i.title || ""
        )}</strong> — ${escapeHtml(i.explanation || "")}${page(i)}</span></div>`
    )}
    ${section(
      "Tables &amp; Charts",
      summary.tables_and_charts,
      (i) =>
        `<div class="important-item"><span class="tick" style="color:var(--violet);">▦</span><span><strong>${escapeHtml(
          i.title || ""
        )}</strong> — ${escapeHtml(i.explanation || "")}${page(i)}</span></div>`
    )}
    ${section(
      "Code",
      summary.code,
      (i) =>
        `<div class="important-item"><span class="tick glow-cyan">&lt;/&gt;</span><span><strong>${escapeHtml(
          i.language || ""
        )}</strong> — ${escapeHtml(i.what_it_does || "")}${page(i)}</span></div>`
    )}
    ${section(
      "Common Mistakes",
      summary.common_mistakes,
      (i) => `<div class="mistake-item"><span class="tick glow-magenta">✕</span><span>${escapeHtml(i)}</span></div>`
    )}
    ${section(
      "Exam Focus",
      summary.exam_focus,
      (i) =>
        `<div class="important-item"><span class="tick" style="color:var(--amber);">★</span><span>${escapeHtml(
          i
        )}</span></div>`
    )}
    ${
      summary.revision_notes && summary.revision_notes.length
        ? `<div class="content-block"><h4>Revision Notes</h4><ul>${summary.revision_notes
            .map((i) => `<li>${escapeHtml(i)}</li>`)
            .join("")}</ul></div>`
        : ""
    }
  </div>`;
}

async function loadDocumentQuiz(fileId) {
  const btn = document.getElementById("docquiz-btn");
  const out = document.getElementById("doc-output");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Writing questions…";
  }
  if (out) out.innerHTML = loadingBlock("GENERATING QUESTIONS FROM YOUR MATERIAL");

  try {
    const data = await Api.documentQuiz(fileId, 8);
    State.docQuiz = {
      fileId,
      quizId: data.quiz_id,
      questions: data.questions,
      answers: new Array(data.questions.length).fill(null),
      current: 0,
    };
    renderDocQuiz();
  } catch (error) {
    if (out) out.innerHTML = errorBlock(error, `loadDocumentQuiz('${fileId}')`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Quiz Me";
    }
  }
}

function renderDocQuiz() {
  const out = document.getElementById("doc-output");
  const q = State.docQuiz;
  if (!out || !q) return;
  const question = q.questions[q.current];
  const answered = q.answers.filter((a) => a !== null).length;

  out.innerHTML = `
  <div class="neu question-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; gap:10px; flex-wrap:wrap;">
      <span class="mono" style="font-size:12.5px; color:var(--text-faint);">DOCUMENT QUIZ · QUESTION ${
        q.current + 1
      } OF ${q.questions.length}</span>
      <span class="badge mono" style="background:rgba(255,255,255,0.05);">${escapeHtml(
        question.difficulty || ""
      )}${question.source_page ? " · page " + question.source_page : ""}${
    question.source_type && question.source_type !== "text" ? " · " + escapeHtml(question.source_type) : ""
  }</span>
    </div>
    <h3 style="margin-bottom:22px; line-height:1.5;">${escapeHtml(question.question)}</h3>
    <div class="option-list">
      ${question.options
        .map(
          (opt, i) => `
        <div class="neu option-item ${q.answers[q.current] === i ? "selected" : ""}" onclick="selectDocOption(${i})">
          <span class="opt-letter mono">${String.fromCharCode(65 + i)}</span>
          <span>${escapeHtml(opt)}</span>
        </div>`
        )
        .join("")}
    </div>
    <div class="quiz-nav">
      <button class="btn btn-secondary btn-sm" onclick="docQuizNav(-1)" ${
        q.current === 0 ? "disabled" : ""
      }>Previous</button>
      <span class="mono" style="font-size:12.5px; color:var(--text-faint);">${answered}/${
    q.questions.length
  } answered</span>
      ${
        q.current === q.questions.length - 1
          ? `<button class="btn btn-primary btn-sm" onclick="submitDocQuiz()">Submit</button>`
          : `<button class="btn btn-primary btn-sm" onclick="docQuizNav(1)">Next</button>`
      }
    </div>
  </div>`;
}

function selectDocOption(i) {
  State.docQuiz.answers[State.docQuiz.current] = i;
  renderDocQuiz();
}
function docQuizNav(delta) {
  const q = State.docQuiz;
  const next = q.current + delta;
  if (next >= 0 && next < q.questions.length) {
    q.current = next;
    renderDocQuiz();
  }
}

async function submitDocQuiz() {
  const q = State.docQuiz;
  const out = document.getElementById("doc-output");
  if (out) out.innerHTML = loadingBlock("GRADING");
  try {
    const data = await Api.gradeDocumentQuiz(q.fileId, q.quizId, q.answers);
    const score = data.score;
    if (out) {
      out.innerHTML = `
      <div class="neu content-panel">
        <div class="subj-crumb mono">DOCUMENT QUIZ RESULT</div>
        <div style="display:flex; align-items:center; gap:20px; margin-bottom:22px; flex-wrap:wrap;">
          <div class="score-num" style="color:${masteryBand(score.raw_percentage).color};">${
        score.raw_percentage
      }%</div>
          <div>
            <div style="font-weight:600;">${score.correct_count} of ${
        score.total_questions
      } correct</div>
            <div class="mono" style="font-size:12px; color:var(--text-faint);">Weighted: ${
              score.weighted_percentage
            }%</div>
          </div>
        </div>
        <div style="display:grid; gap:14px;">
          ${data.review.map(renderReviewItem).join("")}
        </div>
        <div style="margin-top:20px; display:flex; gap:10px; flex-wrap:wrap;">
          <button class="btn btn-secondary btn-sm" onclick="loadDocumentQuiz('${
            q.fileId
          }')">New Questions</button>
        </div>
      </div>`;
    }
  } catch (error) {
    if (out) out.innerHTML = errorBlock(error, "submitDocQuiz()");
  }
}

function askDocumentFromInput(fileId) {
  const input = document.getElementById("doc-tutor-input");
  const val = (input.value || "").trim();
  if (!val) return;
  input.value = "";
  askDocument(fileId, val);
}

/** Document-grounded tutor. Retrieval happens server-side before the model answers. */
async function askDocument(fileId, message) {
  const history = State.docTutor[fileId] || (State.docTutor[fileId] = []);
  const priorTurns = history.slice(-12);
  history.push({ role: "user", content: message });

  const box = document.getElementById("doc-tutor-messages");
  const sendBtn = document.getElementById("doc-tutor-send");
  if (box) {
    box.insertAdjacentHTML("beforeend", `<div class="tutor-msg user">${escapeHtml(message)}</div>`);
    box.insertAdjacentHTML(
      "beforeend",
      `<div class="tutor-msg bot" id="doc-thinking"><span class="mono" style="color:var(--cyan);">searching your document…</span></div>`
    );
    box.scrollTop = box.scrollHeight;
  }
  if (sendBtn) sendBtn.disabled = true;

  let reply;
  let sources = [];
  try {
    const data = await Api.askDocument(fileId, message, priorTurns);
    reply = data.reply;
    sources = data.sources || [];
  } catch (error) {
    reply = error.isAiConfigError
      ? "The AI isn't configured on this deployment yet — the backend needs AI_PROVIDER and AI_API_KEY set."
      : error.message || "I couldn't answer that just now. Please try again.";
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    const thinking = document.getElementById("doc-thinking");
    if (thinking) thinking.remove();
  }

  history.push({ role: "assistant", content: reply });

  const liveBox = document.getElementById("doc-tutor-messages");
  if (liveBox) {
    const pages = [...new Set(sources.map((s) => s.page_number).filter(Boolean))];
    const citation = pages.length
      ? `<div class="mono" style="font-size:10.5px; color:var(--text-faint); margin-top:6px;">sources: page ${pages.join(
          ", "
        )}</div>`
      : "";
    liveBox.insertAdjacentHTML(
      "beforeend",
      `<div class="tutor-msg bot">${renderMarkdown(reply)}${citation}</div>`
    );
    liveBox.scrollTop = liveBox.scrollHeight;
  }
}

/* ---------------------- Profile ---------------------- */
function viewProfile() {
  const user = Auth.user();
  if (!user) return `<div class="wrap empty-state">Not signed in.</div>`;
  const initial = (user.full_name || user.email || "?").charAt(0).toUpperCase();
  return `
  <section class="wrap" style="padding:60px 0;">
    <div class="neu auth-box" style="text-align:center;">
      <div style="width:64px; height:64px; border-radius:50%; margin:0 auto 16px; background:linear-gradient(135deg, var(--cyan), var(--magenta)); display:flex; align-items:center; justify-content:center; font-family:var(--font-display); font-size:22px; font-weight:700; color:#04101a;">${escapeHtml(
        initial
      )}</div>
      <h2>${escapeHtml(user.full_name || "")}</h2>
      <p>${escapeHtml(user.email || "")}</p>
      <button class="btn btn-secondary btn-block" onclick="nav('#/dashboard')" style="margin-top:20px;">View My Progress</button>
      <button class="btn btn-secondary btn-block" onclick="nav('#/upload')" style="margin-top:10px;">My Uploaded Material</button>
      <button class="btn btn-ghost btn-block" onclick="logout()" style="margin-top:10px;">Sign Out</button>
    </div>
  </section>`;
}
