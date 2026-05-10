export const API_BASE = "http://localhost:8000";

function getToken() {
  return localStorage.getItem("wenetbrain_token");
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: authHeaders() });
  if (res.status === 401) {
    localStorage.removeItem("wenetbrain_token");
    window.location.href = `/login.html?api=${encodeURIComponent(API_BASE)}&app=Aplikacja&redirect=/&key=wenetbrain_token`;
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.status === 204 ? ({} as T) : res.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    localStorage.removeItem("wenetbrain_token");
    window.location.href = `/login.html?api=${encodeURIComponent(API_BASE)}&app=Aplikacja&redirect=/&key=wenetbrain_token`;
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (res.status === 401) {
    localStorage.removeItem("wenetbrain_token");
    window.location.href = `/login.html?api=${encodeURIComponent(API_BASE)}&app=Aplikacja&redirect=/&key=wenetbrain_token`;
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export interface Space {
  bank_id: string;
  name: string;
  space_type: string;
  role?: string;
}

export interface Note {
  chunk_id: string;
  text: string;
  payload?: {
    title?: string;
    type?: string;
    user_id?: string;
    created_at?: string;
    proposal_for_bank?: string;
    proposal_status?: "pending_approval" | "approved" | "rejected";
  };
  space_name?: string;
  space_bank_id?: string;
}

export interface NoteCreateResponse {
  status: "created" | "pending_approval";
  mode: "direct" | "proposal";
  chunk_id?: string;
  inbox_id?: string;
  private_chunk_id?: string;
}

export interface InboxItem {
  id: string;
  item_type: string;
  bank_id: string;
  content: string | Record<string, unknown>;
  status?: "pending_approval" | "approved" | "rejected" | string;
  proposed_by?: string;
  approved_by?: string | null;
  user_id?: string;
  is_mine?: boolean;
  can_approve?: boolean;
  created_at?: string;
}

export interface User {
  id: string;
  name: string;
  email?: string;
  role: string;
  team?: string;
}

export interface SearchResult {
  bank_id: string;
  score: number;
  payload?: {
    title?: string;
    chunk_text?: string;
    user_id?: string;
    created_at?: string;
    meeting_title?: string;
    meeting_date?: string;
  };
}
