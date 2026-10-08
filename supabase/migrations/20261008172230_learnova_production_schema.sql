-- Learnova production schema. Apply with: supabase db push
-- This migration intentionally leaves the local SQLite database untouched.
create extension if not exists vector with schema extensions;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (char_length(title) between 1 and 120),
  status text not null default 'EMPTY' check (status in ('EMPTY','UPLOADED','QUEUED','EXTRACTING','ANALYZING','INDEXING','PROCESSING','READY','ERROR')),
  error text,
  created_at timestamptz not null default now(),
  revision integer not null default 0
);

create table if not exists public.files (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 200),
  mime_type text,
  byte_size bigint check (byte_size is null or byte_size >= 0),
  storage_path text unique,
  status text not null default 'UPLOADED' check (status in ('UPLOADED','QUEUED','EXTRACTING','ANALYZING','INDEXING','PROCESSING','READY','ERROR')),
  pages integer not null default 0 check (pages >= 0),
  error text,
  outline jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.chunks (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  file_id uuid not null references public.files(id) on delete cascade,
  page integer not null check (page >= 0),
  text text not null check (char_length(text) > 0),
  created_at timestamptz not null default now()
);

create table if not exists public.embeddings (
  chunk_id uuid primary key references public.chunks(id) on delete cascade,
  vector extensions.vector(768) not null,
  model text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.concepts (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  data jsonb not null,
  introduced boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  title text,
  created_at timestamptz not null default now()
);

create table if not exists public.messages (
  id bigint generated always as identity primary key,
  session_id uuid not null references public.sessions(id) on delete cascade,
  conversation_id uuid references public.conversations(id) on delete set null,
  role text not null check (role in ('user','assistant','system')),
  content text not null,
  citations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.quizzes (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  title text,
  created_at timestamptz not null default now()
);

create table if not exists public.questions (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions(id) on delete cascade,
  quiz_id uuid references public.quizzes(id) on delete set null,
  concept_id uuid references public.concepts(id) on delete set null,
  data jsonb not null,
  difficulty integer not null check (difficulty between 1 and 4),
  is_final boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.attempts (
  question_id uuid primary key references public.questions(id) on delete cascade,
  answer text not null,
  score real not null check (score between 0 and 1),
  feedback text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.mastery_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id uuid not null references public.sessions(id) on delete cascade,
  concept_id uuid references public.concepts(id) on delete set null,
  score real check (score between 0 and 100),
  evidence_count integer not null default 0 check (evidence_count >= 0),
  created_at timestamptz not null default now(),
  unique (session_id, concept_id)
);

create table if not exists public.voice_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id uuid not null references public.sessions(id) on delete cascade,
  status text not null default 'created' check (status in ('created','connecting','active','ended','failed')),
  provider_session_id text,
  started_at timestamptz,
  ended_at timestamptz,
  error text,
  created_at timestamptz not null default now()
);

create index if not exists sessions_user_created_idx on public.sessions(user_id, created_at desc);
create index if not exists files_session_idx on public.files(session_id);
create index if not exists chunks_session_idx on public.chunks(session_id);
create index if not exists concepts_session_idx on public.concepts(session_id);
create index if not exists messages_session_created_idx on public.messages(session_id, created_at);
create index if not exists questions_session_idx on public.questions(session_id);
create index if not exists voice_sessions_user_idx on public.voice_sessions(user_id, created_at desc);
create index if not exists embeddings_vector_hnsw_idx on public.embeddings using hnsw (vector extensions.vector_cosine_ops);

alter table public.profiles enable row level security;
alter table public.sessions enable row level security;
alter table public.files enable row level security;
alter table public.chunks enable row level security;
alter table public.embeddings enable row level security;
alter table public.concepts enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.quizzes enable row level security;
alter table public.questions enable row level security;
alter table public.attempts enable row level security;
alter table public.mastery_records enable row level security;
alter table public.voice_sessions enable row level security;

create policy "profiles own data" on public.profiles for all to authenticated
  using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
create policy "sessions own data" on public.sessions for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "files through owned session" on public.files for all to authenticated
  using (exists (select 1 from public.sessions s where s.id = files.session_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.sessions s where s.id = files.session_id and s.user_id = (select auth.uid())));
create policy "chunks through owned session" on public.chunks for all to authenticated
  using (exists (select 1 from public.sessions s where s.id = chunks.session_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.sessions s where s.id = chunks.session_id and s.user_id = (select auth.uid())));
create policy "embeddings through owned chunk" on public.embeddings for all to authenticated
  using (exists (select 1 from public.chunks c join public.sessions s on s.id = c.session_id where c.id = embeddings.chunk_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.chunks c join public.sessions s on s.id = c.session_id where c.id = embeddings.chunk_id and s.user_id = (select auth.uid())));
create policy "concepts through owned session" on public.concepts for all to authenticated
  using (exists (select 1 from public.sessions s where s.id = concepts.session_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.sessions s where s.id = concepts.session_id and s.user_id = (select auth.uid())));
create policy "conversations through owned session" on public.conversations for all to authenticated
  using (exists (select 1 from public.sessions s where s.id = conversations.session_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.sessions s where s.id = conversations.session_id and s.user_id = (select auth.uid())));
create policy "messages through owned session" on public.messages for all to authenticated
  using (exists (select 1 from public.sessions s where s.id = messages.session_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.sessions s where s.id = messages.session_id and s.user_id = (select auth.uid())));
create policy "quizzes through owned session" on public.quizzes for all to authenticated
  using (exists (select 1 from public.sessions s where s.id = quizzes.session_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.sessions s where s.id = quizzes.session_id and s.user_id = (select auth.uid())));
create policy "questions through owned session" on public.questions for all to authenticated
  using (exists (select 1 from public.sessions s where s.id = questions.session_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.sessions s where s.id = questions.session_id and s.user_id = (select auth.uid())));
create policy "attempts through owned question" on public.attempts for all to authenticated
  using (exists (select 1 from public.questions q join public.sessions s on s.id = q.session_id where q.id = attempts.question_id and s.user_id = (select auth.uid())))
  with check (exists (select 1 from public.questions q join public.sessions s on s.id = q.session_id where q.id = attempts.question_id and s.user_id = (select auth.uid())));
create policy "mastery own data" on public.mastery_records for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "voice sessions own data" on public.voice_sessions for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('learning-materials', 'learning-materials', false, 20971520,
  array['application/pdf','text/plain','text/markdown','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.presentationml.presentation'])
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit, allowed_mime_types = excluded.allowed_mime_types;

create policy "learning materials select own folder" on storage.objects for select to authenticated
  using (bucket_id = 'learning-materials' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "learning materials insert own folder" on storage.objects for insert to authenticated
  with check (bucket_id = 'learning-materials' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "learning materials update own folder" on storage.objects for update to authenticated
  using (bucket_id = 'learning-materials' and (storage.foldername(name))[1] = (select auth.uid())::text)
  with check (bucket_id = 'learning-materials' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "learning materials delete own folder" on storage.objects for delete to authenticated
  using (bucket_id = 'learning-materials' and (storage.foldername(name))[1] = (select auth.uid())::text);

create or replace function public.match_chunks(
  query_embedding extensions.vector(768),
  target_session uuid,
  match_count integer default 8
)
returns table (id uuid, file_id uuid, page integer, text text, similarity double precision)
language sql stable
security invoker
set search_path = public, extensions
as $$
  select c.id, c.file_id, c.page, c.text, 1 - (e.vector <=> query_embedding) as similarity
  from public.chunks c
  join public.embeddings e on e.chunk_id = c.id
  join public.sessions s on s.id = c.session_id
  where c.session_id = target_session and s.user_id = (select auth.uid())
  order by e.vector <=> query_embedding
  limit greatest(1, least(match_count, 20));
$$;

grant usage on schema public to authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;
grant execute on function public.match_chunks(extensions.vector, uuid, integer) to authenticated;

