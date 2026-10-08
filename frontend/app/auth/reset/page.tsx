'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { supabaseBrowser } from '@/lib/supabase/browser';

export default function ResetPasswordPage() {
  const [message, setMessage] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const password = String(new FormData(event.currentTarget).get('password') || '');
    const client = supabaseBrowser();
    if (!client) return setMessage('Supabase Auth is not configured for this deployment.');
    const { error } = await client.auth.updateUser({ password });
    setMessage(error ? error.message : 'Password updated. You can now sign in.');
  }
  return <main className="wrap start-section"><span className="eyebrow">PASSWORD RESET</span><h1>Choose a new password.</h1><form className="auth-form" onSubmit={submit}><label htmlFor="password">New password</label><input id="password" name="password" type="password" minLength={10} required/><button className="button">Save password</button>{message && <p className="form-note">{message}</p>}</form><Link className="text-link" href="/">Return to Learnova</Link></main>;
}
