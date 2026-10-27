-- File rows are server-managed metadata. Browser clients may read metadata for
-- their sessions, but cannot repoint a file at another object they own.
drop policy if exists "files through owned session" on public.files;

create policy "files select through owned session" on public.files
  for select to authenticated
  using (exists (
    select 1 from public.sessions s
    where s.id = files.session_id and s.user_id = (select auth.uid())
  ));

revoke insert, update, delete on public.files from authenticated;
grant select on public.files to authenticated;
