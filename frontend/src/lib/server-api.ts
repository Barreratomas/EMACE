import { cookies } from 'next/headers';

export const API_BASE_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000/api/v1';

export async function getServerAuthHeaders(): Promise<Record<string, string>> {
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function buildApiUrl(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>
): string {
  const base = API_BASE_URL.replace(/\/+$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${base}${p}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    });
  }
  return url.toString();
}

export async function apiRequest<T = any>(
  pathOrUrl: string,
  init: RequestInit = {}
): Promise<T> {
  const isAbsolute = /^https?:\/\//i.test(pathOrUrl);
  const url = isAbsolute ? pathOrUrl : buildApiUrl(pathOrUrl);
  const auth = await getServerAuthHeaders();
  const headers = { ...auth, ...(init.headers || {}) } as Record<string, string>;
  const res = await fetch(url, { ...init, headers });
  if (!res.ok) {
    let detail = `API error: ${res.status}`;
    try {
      const data = await res.json();
      detail = (data as any)?.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}
