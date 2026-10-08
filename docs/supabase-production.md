# Supabase production deployment

Learnova keeps the existing SQLite database as an offline development fallback. Setting both `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` switches API authentication to Supabase bearer tokens. Setting `SUPABASE_DATABASE_URL` switches learning persistence to Postgres. Do not set only the first pair in a production deployment: authentication would work while the application still writes learning data locally.

## Configure the project

1. Create a Supabase project and add its URL, publishable key, database URL, and service-role key to the server secret store. The service-role key is used only by the FastAPI process to move already-authorized material into private Storage; it is never exposed to Next.js.
2. Put `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` in `frontend/.env.local`.
3. In Supabase Auth, enable email/password. Set site URL to the deployed application origin and add these redirect URLs: `https://your-domain/auth/confirm` and `https://your-domain/auth/reset`. Enable Google in Auth Providers only after entering its OAuth client credentials and matching redirect URL in Google Cloud.
4. Apply the checked-in schema from the repository root: `npx supabase db push --project-ref YOUR_PROJECT_REF`. It creates the private `learning-materials` bucket, all tables, indexes, RLS policies, and the security-invoker vector-match RPC.
5. Deploy the API and frontend over HTTPS. Set `COOKIE_SECURE=true` only for the local SQLite fallback; Supabase browser sessions use its managed cookies/tokens.

## Data model and access boundary

The existing runtime names are intentionally retained: `sessions` is the learning-session entity; `files` is documents; `chunks` plus `embeddings` is the document-chunk/vector index; `questions` and `attempts` implement quizzes and attempts. `profiles`, `conversations`, `messages`, `mastery_records`, and `voice_sessions` cover the remaining production entities. Every exposed table has RLS enabled. Child tables authorize through the owning session, and Storage paths start with the authenticated user UUID.

The API validates every Supabase access token with Auth before loading a session. Its direct Postgres connection is server-only; browser reads and writes are constrained by RLS. The private bucket has no public URL policy. Use a signed URL only when adding the PDF viewer; generate it after confirming the document belongs to the bearer user.

## Migration and rollback

The migration is additive and never reads, deletes, or modifies `storage/learning.db`. Back up the local file before a cutover. Importing existing local accounts cannot preserve password hashes in Supabase Auth; create verified Supabase accounts and migrate only a user's documents after that identity exists. Run the import as an audited, one-time server job keyed by old account email and new Auth UUID.

To roll back application traffic, remove `SUPABASE_DATABASE_URL` and the Supabase Auth environment variables, then redeploy; the local SQLite fallback remains intact. Do not drop the Supabase schema as a rollback mechanism. Database restoration should use a Supabase backup or a tested inverse migration in a maintenance window.

## Processing reliability

Document records move through `UPLOADED`, `QUEUED`, `EXTRACTING`, `ANALYZING`, `INDEXING`, `READY`, or `ERROR`; failed extraction and provider failures preserve the original private object. The current worker is FastAPI background work, suitable for a single-instance deployment. Before horizontally scaling, move `ingest` and `analyze` to a durable queue and claim jobs in Postgres so a process restart cannot abandon queued work.
