-- =============================================================
-- LearnQwik — PostgreSQL schema for Supabase
--
-- Run this FIRST in the Supabase SQL Editor, then seed.sql.
-- Safe to re-run: every object uses IF NOT EXISTS / CREATE OR REPLACE.
--
-- Security model
--   * Curriculum tables (subjects, topics, questions, resources) are world
--     readable and writable only by the service role.
--   * Every user-owned table has RLS enabled with a USING (auth.uid() =
--     user_id) policy, so one user physically cannot read another's rows —
--     even if the API layer had a bug.
--   * questions.correct_index is readable by anon on purpose ONLY because the
--     API strips it before responding; if you expose PostgREST directly to the
--     browser, tighten the questions SELECT policy first.
-- =============================================================

create extension if not exists "pgcrypto";
-- Optional. Only needed if you set USE_EMBEDDINGS=true on the backend.
-- create extension if not exists vector;

-- =============================================================
-- PROFILES
-- =============================================================
create table if not exists profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text,
  full_name   text,
  format_preference text,                        -- Article / Video / Practice ...
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

alter table profiles enable row level security;

drop policy if exists "profiles self read" on profiles;
create policy "profiles self read" on profiles
  for select using (auth.uid() = id);

drop policy if exists "profiles self write" on profiles;
create policy "profiles self write" on profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

-- =============================================================
-- CURRICULUM (public read)
-- =============================================================
create table if not exists subjects (
  id          text primary key,
  name        text not null unique,
  tagline     text,
  color       text,
  position    integer not null default 0,
  created_at  timestamptz not null default now()
);

create table if not exists topics (
  id                      text primary key,
  subject_id              text not null references subjects(id) on delete cascade,
  name                    text not null,
  description             text,
  content                 jsonb not null default '{}'::jsonb,
  position                integer not null default 0,
  estimated_minutes       integer not null default 30,
  prerequisite_topic_ids  text[] not null default '{}',
  created_at              timestamptz not null default now(),
  unique (subject_id, name)
);

create index if not exists topics_subject_idx on topics (subject_id, position);

create table if not exists questions (
  id            text primary key,
  topic_id      text not null references topics(id) on delete cascade,
  question      text not null,
  options       jsonb not null,
  correct_index integer not null check (correct_index >= 0),
  explanation   text,
  difficulty    text not null default 'Medium'
                check (difficulty in ('Easy', 'Medium', 'Hard')),
  position      integer not null default 0,
  source_page   integer,
  source_type   text,
  created_at    timestamptz not null default now()
);

create index if not exists questions_topic_idx on questions (topic_id, position);

create table if not exists resources (
  id               text primary key,
  topic_id         text references topics(id) on delete cascade,
  title            text not null,
  type             text not null,
  difficulty       text not null default 'Medium'
                   check (difficulty in ('Easy', 'Medium', 'Hard')),
  duration_minutes integer not null default 10,
  rating           numeric(2,1) not null default 4.0 check (rating >= 0 and rating <= 5),
  url              text,
  created_at       timestamptz not null default now()
);

create index if not exists resources_topic_idx on resources (topic_id);

alter table subjects  enable row level security;
alter table topics    enable row level security;
alter table questions enable row level security;
alter table resources enable row level security;

drop policy if exists "subjects public read" on subjects;
create policy "subjects public read" on subjects for select using (true);
drop policy if exists "topics public read" on topics;
create policy "topics public read" on topics for select using (true);
drop policy if exists "questions public read" on questions;
create policy "questions public read" on questions for select using (true);
drop policy if exists "resources public read" on resources;
create policy "resources public read" on resources for select using (true);

-- =============================================================
-- ASSESSMENT
-- =============================================================
create table if not exists quiz_attempts (
  id                    uuid primary key default gen_random_uuid(),
  user_id               uuid not null references auth.users(id) on delete cascade,
  subject_id            text not null references subjects(id) on delete cascade,
  topic_id              text not null references topics(id) on delete cascade,
  mode                  text not null default 'quiz' check (mode in ('quiz', 'reassess')),
  status                text not null default 'in_progress'
                        check (status in ('in_progress', 'completed', 'abandoned')),
  question_ids          text[] not null default '{}',
  started_at            timestamptz not null default now(),
  completed_at          timestamptz,
  raw_score_pct         numeric(5,2),
  weighted_score_pct    numeric(5,2),
  correct_count         integer,
  incorrect_count       integer,
  unanswered_count      integer,
  total_questions       integer,
  time_used_seconds     integer,
  fullscreen_violations integer not null default 0,
  auto_submitted        boolean not null default false,
  difficulty_breakdown  jsonb,
  before_mastery_pct    numeric(5,2),
  after_mastery_pct     numeric(5,2)
);

create index if not exists attempts_user_idx on quiz_attempts (user_id, completed_at desc);
create index if not exists attempts_user_status_idx on quiz_attempts (user_id, status);
create index if not exists attempts_topic_idx on quiz_attempts (user_id, topic_id);

create table if not exists answers (
  id               uuid primary key default gen_random_uuid(),
  attempt_id       uuid not null references quiz_attempts(id) on delete cascade,
  user_id          uuid not null references auth.users(id) on delete cascade,
  question_id      text not null references questions(id) on delete cascade,
  selected_index   integer,
  response_time_ms integer,
  answered_at      timestamptz not null default now(),
  unique (attempt_id, question_id)
);

create index if not exists answers_attempt_idx on answers (attempt_id);

create table if not exists topic_mastery (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  topic_id       text not null references topics(id) on delete cascade,
  subject_id     text not null references subjects(id) on delete cascade,
  mastery_pct    numeric(5,2) not null default 0,
  mastery_band   text,
  attempts_count integer not null default 0,
  updated_at     timestamptz not null default now(),
  unique (user_id, topic_id)
);

create index if not exists mastery_user_idx on topic_mastery (user_id, subject_id);

create table if not exists progress_history (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  subject_id  text references subjects(id) on delete cascade,
  topic_id    text references topics(id) on delete cascade,
  attempt_id  uuid references quiz_attempts(id) on delete set null,
  mastery_pct numeric(5,2),
  score_pct   numeric(5,2),
  recorded_at timestamptz not null default now()
);

create index if not exists progress_user_idx on progress_history (user_id, recorded_at);

-- =============================================================
-- ROADMAP
-- =============================================================
create table if not exists roadmap_versions (
  id                 uuid primary key default gen_random_uuid(),
  user_id            uuid not null references auth.users(id) on delete cascade,
  subject_id         text not null references subjects(id) on delete cascade,
  version_number     integer not null,
  roadmap_json       jsonb not null,
  changes_json       jsonb,
  generated_by       text not null default 'default'
                     check (generated_by in ('default', 'ai', 'fallback')),
  trigger_attempt_id uuid references quiz_attempts(id) on delete set null,
  created_at         timestamptz not null default now(),
  unique (user_id, subject_id, version_number)
);

create index if not exists roadmap_user_idx
  on roadmap_versions (user_id, subject_id, version_number desc);

create table if not exists learning_plans (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  subject_id text references subjects(id) on delete cascade,
  plan_json  jsonb not null,
  created_at timestamptz not null default now()
);

-- =============================================================
-- DOCUMENTS
-- =============================================================
create table if not exists uploaded_files (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references auth.users(id) on delete cascade,
  filename          text not null,
  original_filename text not null,
  file_type         text not null,
  storage_path      text not null,
  file_size         bigint not null,
  status            text not null default 'uploading',
  page_count        integer,
  error_message     text,
  created_at        timestamptz not null default now(),
  processed_at      timestamptz
);

create index if not exists uploads_user_idx on uploaded_files (user_id, created_at desc);

create table if not exists document_pages (
  id                uuid primary key default gen_random_uuid(),
  uploaded_file_id  uuid not null references uploaded_files(id) on delete cascade,
  user_id           uuid not null references auth.users(id) on delete cascade,
  page_number       integer not null,
  extracted_text    text,
  visual_analysis   text,
  content_quality   text,
  important_visuals boolean not null default false,
  analysis_source   text[] not null default '{}',
  created_at        timestamptz not null default now(),
  unique (uploaded_file_id, page_number)
);

create index if not exists pages_file_idx on document_pages (uploaded_file_id, page_number);

create table if not exists document_chunks (
  id               uuid primary key default gen_random_uuid(),
  uploaded_file_id uuid not null references uploaded_files(id) on delete cascade,
  user_id          uuid not null references auth.users(id) on delete cascade,
  chunk_index      integer not null,
  page_number      integer,
  content          text not null,
  content_type     text,
  source           text,                          -- 'text' | 'vision'
  -- Uncomment together with the vector extension above if using pgvector.
  -- embedding     vector(1536),
  metadata         jsonb not null default '{}'::jsonb,
  created_at       timestamptz not null default now(),
  unique (uploaded_file_id, chunk_index)
);

create index if not exists chunks_file_idx on document_chunks (uploaded_file_id, chunk_index);
create index if not exists chunks_page_idx on document_chunks (uploaded_file_id, page_number);
-- Lexical fallback index for the keyword retriever.
create index if not exists chunks_content_fts
  on document_chunks using gin (to_tsvector('english', content));

create table if not exists document_summaries (
  id               uuid primary key default gen_random_uuid(),
  uploaded_file_id uuid not null unique references uploaded_files(id) on delete cascade,
  user_id          uuid not null references auth.users(id) on delete cascade,
  summary_json     jsonb not null,
  created_at       timestamptz not null default now()
);

create table if not exists generated_quizzes (
  id               uuid primary key default gen_random_uuid(),
  uploaded_file_id uuid not null references uploaded_files(id) on delete cascade,
  user_id          uuid not null references auth.users(id) on delete cascade,
  questions_json   jsonb not null,
  question_count   integer not null default 0,
  created_at       timestamptz not null default now()
);

create index if not exists genquiz_file_idx on generated_quizzes (uploaded_file_id, created_at desc);

create table if not exists ai_conversations (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references auth.users(id) on delete cascade,
  topic_id          text references topics(id) on delete set null,
  uploaded_file_id  uuid references uploaded_files(id) on delete cascade,
  user_message      text not null,
  assistant_message text,
  page_context      integer,
  created_at        timestamptz not null default now()
);

create index if not exists conversations_user_idx on ai_conversations (user_id, created_at desc);

-- =============================================================
-- ROW LEVEL SECURITY on every user-owned table
-- =============================================================
do $$
declare t text;
begin
  foreach t in array array[
    'quiz_attempts', 'answers', 'topic_mastery', 'progress_history',
    'roadmap_versions', 'learning_plans', 'uploaded_files', 'document_pages',
    'document_chunks', 'document_summaries', 'generated_quizzes', 'ai_conversations'
  ]
  loop
    execute format('alter table %I enable row level security', t);
    execute format('drop policy if exists "%s owner access" on %I', t, t);
    execute format(
      'create policy "%s owner access" on %I for all
         using (auth.uid() = user_id) with check (auth.uid() = user_id)', t, t);
  end loop;
end $$;

-- =============================================================
-- STORAGE BUCKET POLICIES
-- Create the bucket first (dashboard or the statement below), keep it PRIVATE.
-- Paths are users/{user_id}/documents/{file_id}/original.{ext}, so the first
-- path segment after "users/" is the owner's UUID.
-- =============================================================
insert into storage.buckets (id, name, public)
values ('learnqwik-documents', 'learnqwik-documents', false)
on conflict (id) do nothing;

drop policy if exists "learnqwik owner read" on storage.objects;
create policy "learnqwik owner read" on storage.objects
  for select using (
    bucket_id = 'learnqwik-documents'
    and (storage.foldername(name))[2] = auth.uid()::text
  );

drop policy if exists "learnqwik owner write" on storage.objects;
create policy "learnqwik owner write" on storage.objects
  for insert with check (
    bucket_id = 'learnqwik-documents'
    and (storage.foldername(name))[2] = auth.uid()::text
  );

drop policy if exists "learnqwik owner delete" on storage.objects;
create policy "learnqwik owner delete" on storage.objects
  for delete using (
    bucket_id = 'learnqwik-documents'
    and (storage.foldername(name))[2] = auth.uid()::text
  );

-- =============================================================
-- Auto-create a profile row whenever a user signs up
-- =============================================================
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1))
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- =============================================================
-- OPTIONAL: pgvector similarity search
-- Only needed when USE_EMBEDDINGS=true. The app works fine without it.
-- =============================================================
-- create index if not exists chunks_embedding_idx
--   on document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);
--
-- create or replace function match_document_chunks(
--   p_file_id uuid, p_user_id uuid, p_embedding vector(1536), p_limit int default 6
-- ) returns setof document_chunks
-- language sql stable as $$
--   select * from document_chunks
--    where uploaded_file_id = p_file_id and user_id = p_user_id and embedding is not null
--    order by embedding <=> p_embedding
--    limit p_limit;
-- $$;
