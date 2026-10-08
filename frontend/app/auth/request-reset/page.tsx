'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { sendPasswordReset } from '@/lib/auth';

export default function RequestResetPage() {
  const [message, setMessage] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = String(new FormData(event.currentTarget).get('email') || '');
    try { await sendPasswordReset(email); setMessage('Password reset link sent. Check your inbox.'); }
    catch (error) { setMessage((error as Error).message); }
  }
  return <main className="wrap start-section"><span className="eyebrow">PASSWORD RESET</span><h1>Recover your account.</h1><form className="auth-form" onSubmit={submit}><label htmlFor="email">Email address</label><input id="email" name="email" type="email" required/><button className="button">Send reset link</button>{message&&<p className="form-note">{message}</p>}</form><Link className="text-link" href="/">Return to Learnova</Link></main>;
}
