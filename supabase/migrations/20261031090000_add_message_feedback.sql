create table if not exists public.message_feedback (
  message_id bigint primary key references public.messages(id) on delete cascade,
  rating text not null check (rating in ('helpful','unhelpful')),
  note text,
  created_at timestamptz not null default now()
);
