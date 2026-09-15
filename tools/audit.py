#!/usr/bin/env python3
"""
Repository audit — fails loudly on anything that shouldn't ship.

Run before every commit and before the demo:

    python3 tools/audit.py

Three classes of check:

  1. NO FAKE AI          no canned tutor replies, no alert()-based "AI",
                         no "Local demo" text, no "wire in a real provider"
  2. NO LEAKED SECRETS   no API keys, no service-role keys, no hard-coded
                         localhost in production-sensitive frontend code
  3. NO LOCALSTORAGE     learning data (attempts, mastery, roadmap, uploads)
                         must never be the browser's responsibility

Exit code 1 if anything fails, so it can be wired into CI.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", "dist"}
# Files where a match is legitimate: tests, docs, this script, the seed source.
ALLOWED_PATHS = {
    "tools/audit.py",
    "tools/selfcheck.py",
    "README.md",
}
ALLOWED_PREFIXES = ("docs/", "backend/tests/")


def walk():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith((".py", ".js", ".html", ".css", ".json", ".yaml", ".yml", ".sql", ".md")):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            try:
                with open(path, encoding="utf-8") as handle:
                    yield rel, handle.read()
            except (UnicodeDecodeError, OSError):
                continue


def exempt(rel):
    return rel in ALLOWED_PATHS or rel.startswith(ALLOWED_PREFIXES)


# --------------------------------------------------------------- Check 1
FAKE_AI_PATTERNS = [
    (r"generateTutorReply", "the prototype's canned tutor function"),
    (r"Local demo", "a 'Local demo' notice"),
    (r"[Ww]ire in a real (AI )?provider", "a 'wire in a real provider' placeholder"),
    (r"local demo simulation", "a simulated-AI disclaimer"),
    (r"alert\(`?Summary of", "the alert()-based fake summary"),
    (r"alert\(`?Quiz for", "the alert()-based fake quiz"),
]


def check_fake_ai():
    problems = []
    for rel, content in walk():
        if exempt(rel):
            continue
        for pattern, description in FAKE_AI_PATTERNS:
            if re.search(pattern, content):
                problems.append("%s contains %s" % (rel, description))

    # alert() must not be used as a response channel anywhere in the frontend.
    for rel, content in walk():
        if rel.startswith("frontend/") and rel.endswith(".js") and not exempt(rel):
            for match in re.finditer(r"\balert\s*\(", content):
                line = content[: match.start()].count("\n") + 1
                problems.append("%s:%d uses alert() — not a valid response channel" % (rel, line))
    return problems


# --------------------------------------------------------------- Check 2
SECRET_PATTERNS = [
    (r"sk-ant-[A-Za-z0-9\-_]{20,}", "an Anthropic API key"),
    (r"\bsk-[A-Za-z0-9]{32,}", "an OpenAI API key"),
    (r"eyJ[A-Za-z0-9_\-]{30,}\.[A-Za-z0-9_\-]{30,}", "a JWT (possibly a Supabase key)"),
    (r"service_role", "a service-role reference"),
]


def check_secrets():
    problems = []
    for rel, content in walk():
        if exempt(rel) or rel.endswith(".example"):
            continue
        for pattern, description in SECRET_PATTERNS:
            for match in re.finditer(pattern, content):
                # SUPABASE_SERVICE_ROLE_KEY as a variable NAME is fine.
                snippet = content[max(0, match.start() - 40): match.end() + 10]
                if "SERVICE_ROLE_KEY" in snippet.upper() and "=" not in snippet.split(
                        "SERVICE_ROLE_KEY")[-1][:3]:
                    continue
                line = content[: match.start()].count("\n") + 1
                problems.append("%s:%d may contain %s" % (rel, line, description))

    # A secret must never be ASSIGNED a value in browser-shipped code.
    # Naming the variable is fine — build.js guards against it, and app.js tells
    # the user which variable the backend is missing. Giving it a value is not.
    assignment = re.compile(
        r"(SUPABASE_SERVICE_ROLE_KEY|SERVICE_ROLE_KEY|AI_API_KEY|ANTHROPIC_API_KEY|OPENAI_API_KEY)"
        r"\s*[:=]\s*[\"\'`][^\"\'`\s]{8,}"
    )
    for rel, content in walk():
        if rel.startswith("frontend/") and not exempt(rel) and not rel.endswith(".example"):
            for match in assignment.finditer(content):
                line = content[: match.start()].count("\n") + 1
                problems.append("%s:%d assigns a value to %s in frontend code"
                                % (rel, line, match.group(1)))
    return problems


# --------------------------------------------------------------- Check 3
def check_hardcoded_localhost():
    problems = []
    for rel, content in walk():
        if exempt(rel) or rel.endswith((".example", ".md")):
            continue
        if not rel.startswith("frontend/"):
            continue
        # env.js legitimately holds the local default; build.js overwrites it.
        if rel in ("frontend/js/env.js", "frontend/build.js"):
            continue
        for match in re.finditer(r"localhost:\d+|127\.0\.0\.1:\d+", content):
            line = content[: match.start()].count("\n") + 1
            problems.append("%s:%d hard-codes a localhost URL" % (rel, line))
    return problems


# --------------------------------------------------------------- Check 4
FORBIDDEN_STORAGE_KEYS = ["attempts", "mastery", "roadmap", "uploads", "progress",
                          "recommendations", "quiz"]


def check_localstorage():
    problems = []
    for rel, content in walk():
        if exempt(rel) or not rel.startswith("frontend/") or not rel.endswith(".js"):
            continue
        for match in re.finditer(r"localStorage\.(getItem|setItem)\(\s*([\"'`])(.*?)\2", content):
            key = match.group(3).lower()
            line = content[: match.start()].count("\n") + 1
            for forbidden in FORBIDDEN_STORAGE_KEYS:
                if forbidden in key:
                    problems.append(
                        "%s:%d stores learning data (%r) in localStorage — the backend "
                        "must be the source of truth" % (rel, line, match.group(3))
                    )
        # Dynamic keys are fine only in the Prefs/session helpers.
        for match in re.finditer(r"localStorage\.(getItem|setItem)\(\s*[^\"'`]", content):
            line = content[: match.start()].count("\n") + 1
            snippet = content[max(0, match.start() - 200): match.start()]
            if "lq_pref_" not in content[match.start(): match.start() + 200] and \
               "SESSION_KEY" not in content[match.start(): match.start() + 120]:
                problems.append("%s:%d uses a dynamic localStorage key — verify it is "
                                "UI-only" % (rel, line))
    return problems


# --------------------------------------------------------------- Check 5
def check_required_files():
    required = [
        "backend/main.py", "backend/requirements.txt", "backend/.env.example",
        "backend/.python-version", "database/schema.sql", "database/seed.sql",
        "frontend/index.html", "frontend/js/api.js", "frontend/js/auth.js",
        "frontend/js/app.js", "frontend/build.js", "frontend/vercel.json",
        "frontend/.env.example", "render.yaml", ".gitignore", "README.md",
    ]
    return ["missing required file: %s" % f
            for f in required if not os.path.exists(os.path.join(ROOT, f))]


def main():
    checks = [
        ("No fake AI in production paths", check_fake_ai),
        ("No leaked secrets", check_secrets),
        ("No hard-coded localhost in frontend", check_hardcoded_localhost),
        ("No learning data in localStorage", check_localstorage),
        ("All required files present", check_required_files),
    ]

    total = 0
    for title, check in checks:
        problems = check()
        total += len(problems)
        if problems:
            print("FAIL  %s" % title)
            for problem in problems:
                print("        - %s" % problem)
        else:
            print("PASS  %s" % title)

    print()
    if total:
        print("Audit failed with %d problem(s)." % total)
        return 1
    print("Audit clean. Nothing fake, nothing leaked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
