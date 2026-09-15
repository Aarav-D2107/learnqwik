#!/usr/bin/env node
/**
 * Generates database/seed.sql from the prototype's js/data.js.
 *
 * The educational content is the most valuable thing in this repo and it was
 * authored by hand, so it is never retyped. This script reads the original
 * SUBJECTS / RESOURCES arrays and emits SQL, which means the seed file can be
 * regenerated any time the content is edited:
 *
 *     node tools/generate-seed.js
 *
 * No dependencies — plain Node.
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const DATA_JS = path.join(ROOT, "frontend", "js", "data.js");
const OUT = path.join(ROOT, "database", "seed.sql");

const source = fs.readFileSync(DATA_JS, "utf8");
const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(source + "\n;globalThis.__out = { SUBJECTS, RESOURCES };", sandbox);
const { SUBJECTS, RESOURCES } = sandbox.__out;

/** Postgres string literal. Doubles single quotes; nothing else is interpolated. */
function q(value) {
  if (value === null || value === undefined) return "NULL";
  return "'" + String(value).replace(/'/g, "''") + "'";
}

/** JSON as a jsonb literal. */
function j(value) {
  return q(JSON.stringify(value)) + "::jsonb";
}

/** text[] literal. */
function arr(values) {
  if (!values || !values.length) return "'{}'";
  return "ARRAY[" + values.map(q).join(", ") + "]::text[]";
}

/**
 * Curriculum prerequisites. Each topic depends on the one before it in its
 * subject — this is what stops the roadmap engine from recommending advanced
 * Collections material to someone with a fundamentals gap.
 */
function prerequisitesFor(subject, index) {
  return index === 0 ? [] : [subject.topics[index - 1].id];
}

const lines = [];
lines.push(`-- =============================================================
-- LearnQwik — seed data
--
-- GENERATED FILE. Do not edit by hand.
-- Regenerate with:  node tools/generate-seed.js
--
-- Source of truth: frontend/js/data.js
-- Run this AFTER database/schema.sql in the Supabase SQL editor.
-- Idempotent: re-running updates rows rather than duplicating them.
-- =============================================================

begin;
`);

// ---------------------------------------------------------------- subjects
lines.push("-- ---------- SUBJECTS ----------");
SUBJECTS.forEach((s, i) => {
  lines.push(
    `insert into subjects (id, name, tagline, color, position) values
  (${q(s.id)}, ${q(s.name)}, ${q(s.tagline)}, ${q(s.color)}, ${i})
on conflict (id) do update set
  name = excluded.name, tagline = excluded.tagline,
  color = excluded.color, position = excluded.position;`
  );
});
lines.push("");

// ---------------------------------------------------------------- topics
lines.push("-- ---------- TOPICS (content preserved verbatim from data.js) ----------");
SUBJECTS.forEach((s) => {
  s.topics.forEach((t, i) => {
    const minutes = 25 + i * 5;
    lines.push(
      `insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  (${q(t.id)}, ${q(s.id)}, ${q(t.name)}, ${q(t.desc)},
   ${j(t.content)},
   ${i}, ${minutes}, ${arr(prerequisitesFor(s, i))})
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;`
    );
  });
});
lines.push("");

// ---------------------------------------------------------------- questions
lines.push("-- ---------- QUESTIONS ----------");
let questionCount = 0;
SUBJECTS.forEach((s) => {
  s.topics.forEach((t) => {
    (t.quiz || []).forEach((item, i) => {
      const id = `${t.id}-q${i + 1}`;
      questionCount += 1;
      lines.push(
        `insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  (${q(id)}, ${q(t.id)}, ${q(item.q)}, ${j(item.options)}, ${item.correct},
   ${q(item.explanation)}, ${q(item.difficulty)}, ${i})
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;`
      );
    });
  });
});
lines.push("");

// ---------------------------------------------------------------- resources
lines.push("-- ---------- RESOURCES (recommendation engine pool) ----------");
RESOURCES.forEach((r) => {
  lines.push(
    `insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  (${q(r.id)}, ${q(r.topicId)}, ${q(r.title)}, ${q(r.type)}, ${q(r.difficulty)},
   ${r.duration}, ${r.rating}, ${q(r.url || null)})
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;`
  );
});

lines.push("");
lines.push("commit;");
lines.push("");
lines.push(`-- Verify the seed loaded:
--   select (select count(*) from subjects)  as subjects,
--          (select count(*) from topics)    as topics,
--          (select count(*) from questions) as questions,
--          (select count(*) from resources) as resources;
-- Expected: ${SUBJECTS.length} subjects, ${SUBJECTS.reduce((a, s) => a + s.topics.length, 0)} topics, ${questionCount} questions, ${RESOURCES.length} resources.`);

fs.writeFileSync(OUT, lines.join("\n"), "utf8");

const topicCount = SUBJECTS.reduce((a, s) => a + s.topics.length, 0);
console.log(`Wrote ${path.relative(ROOT, OUT)}`);
console.log(`  subjects:  ${SUBJECTS.length}`);
console.log(`  topics:    ${topicCount}`);
console.log(`  questions: ${questionCount}`);
console.log(`  resources: ${RESOURCES.length}`);

// Guard rails — a silent content loss here would be invisible until demo day.
const problems = [];
if (SUBJECTS.length !== 5) problems.push(`expected 5 subjects, found ${SUBJECTS.length}`);
if (topicCount !== 30) problems.push(`expected 30 topics, found ${topicCount}`);
SUBJECTS.forEach((s) => {
  if (s.topics.length !== 6) problems.push(`${s.name} has ${s.topics.length} topics, expected 6`);
  s.topics.forEach((t) => {
    if (!t.quiz || t.quiz.length < 3) problems.push(`${t.id} has too few questions`);
    if (!t.content || !t.content.intro) problems.push(`${t.id} is missing content.intro`);
    (t.quiz || []).forEach((item, i) => {
      if (!Array.isArray(item.options) || item.options.length < 2)
        problems.push(`${t.id} q${i + 1} has bad options`);
      if (item.correct < 0 || item.correct >= item.options.length)
        problems.push(`${t.id} q${i + 1} correct index out of range`);
    });
  });
});
const topicIds = new Set(SUBJECTS.flatMap((s) => s.topics.map((t) => t.id)));
RESOURCES.forEach((r) => {
  if (!topicIds.has(r.topicId)) problems.push(`resource ${r.id} points at unknown topic ${r.topicId}`);
});

if (problems.length) {
  console.error("\nSEED VALIDATION FAILED:");
  problems.forEach((p) => console.error("  - " + p));
  process.exit(1);
}
console.log("\nSeed validation passed.");
