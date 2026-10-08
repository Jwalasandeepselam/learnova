'use client';

import { api, post } from './learning';
import { hasSupabase, supabaseBrowser } from './supabase/browser';

export type AuthUser = { id?: string; email: string };

export async function currentUser(): Promise<AuthUser> {
  if (!hasSupabase()) return api<AuthUser>('/auth/me');
  const { data, error } = await supabaseBrowser()!.auth.getUser();
  if (error || !data.user?.email) throw error || new Error('Sign in to continue.');
  return { id: data.user.id, email: data.user.email };
}

export async function signUp(email: string, password: string) {
  if (!hasSupabase()) return post<AuthUser>('/auth/register', { email, password });
  const { data, error } = await supabaseBrowser()!.auth.signUp({ email, password, options: { emailRedirectTo: `${window.location.origin}/auth/confirm` } });
  if (error) throw error;
  if (!data.session) throw new Error('Check your email to confirm your account, then sign in.');
  return { id: data.user?.id, email: data.user?.email || email };
}

export async function signIn(email: string, password: string) {
  if (!hasSupabase()) return post<AuthUser>('/auth/login', { email, password });
  const { data, error } = await supabaseBrowser()!.auth.signInWithPassword({ email, password });
  if (error || !data.user?.email) throw error || new Error('Sign in failed.');
  return { id: data.user.id, email: data.user.email };
}

export async function signOut() {
  if (!hasSupabase()) return post('/auth/logout');
  const { error } = await supabaseBrowser()!.auth.signOut();
  if (error) throw error;
}

export async function sendPasswordReset(email: string) {
  if (!hasSupabase()) throw new Error('Password reset requires Supabase Auth to be configured.');
  const { error } = await supabaseBrowser()!.auth.resetPasswordForEmail(email, { redirectTo: `${window.location.origin}/auth/reset` });
  if (error) throw error;
}
