export const API = `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')}/api/v2`;
export type Citation = { document_id: string; filename: string; page: number | null; text: string };
export type Concept = { id: string; title: string; summary: string; source_ids: string[]; prerequisites: string[]; state: string; mastery: number | null };
export type Session = { id: string; title: string; status: string; error?: string; files: {id:string; name:string; status:string; pages:number; error?:string}[]; concepts: Concept[]; messages: {role:string; content:string; citations?:Citation[]}[]; created_at:string };
export type Question = { id:string; prompt:string; type:string; options:string[]; difficulty:number|string; concept_id:string };
export type Answer = { correct:boolean; score:number; feedback:string; explanation:string; difficulty:number|string; next_step:string; mastery:number|null };
export type Report = {score:number; total:number; percentage:number; difficulty:number|string; strong:string[]; weak:string[]; next_step:string; answered:number; concepts:unknown[]};
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try { response = await fetch(`${API}${path}`, { ...options, credentials:'include', headers: { ...(options.body instanceof FormData ? {} : {'Content-Type':'application/json'}), ...options.headers } }); }
  catch { throw new Error('Cannot reach Learnova. Check your connection and that the server is running.'); }
  if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status}). Please try again.`); }
  return response.status === 204 ? undefined as T : response.json();
}
export const post = <T,>(path:string, data:unknown = {}) => api<T>(path,{method:'POST',body:JSON.stringify(data)});
