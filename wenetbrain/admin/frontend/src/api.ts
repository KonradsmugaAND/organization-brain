const API_BASE = ""; // served from same origin

function getToken() {
  return localStorage.getItem("wenetbrain_admin_token");
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
    localStorage.removeItem("wenetbrain_admin_token");
    window.location.href = "/login.html";
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    localStorage.removeItem("wenetbrain_admin_token");
    window.location.href = "/login.html";
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    localStorage.removeItem("wenetbrain_admin_token");
    window.location.href = "/login.html";
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
    localStorage.removeItem("wenetbrain_admin_token");
    window.location.href = "/login.html";
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export interface Space {
  id: string;
  name: string;
  bank_id: string;
  space_type: string;
  description?: string;
  parent_id?: string | null;
}

export interface User {
  id: string;
  name: string;
  email?: string;
  role: string;
  team?: string;
  company?: string;
  created_at?: string;
}

export interface SpaceUser {
  id: string;
  name: string;
  email?: string;
  user_role: string;
  acl_role: string;
}

export interface Note {
  chunk_id: string;
  title?: string;
  text: string;
  user_id?: string;
  created_at?: string;
}
