'use client';

import Link from 'next/link';

export default function ConfirmEmailPage() {
  return <main className="wrap start-section"><span className="eyebrow">EMAIL VERIFICATION</span><h1>Confirm your email.</h1><p>Open the confirmation link sent by Supabase, then return here to sign in. The link may take a minute to arrive.</p><Link className="button" href="/">Return to Learnova</Link></main>;
}
