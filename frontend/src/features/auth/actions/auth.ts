'use client';

import Cookies from 'js-cookie';
import { 
  loginApiV1AuthLoginPost, 
  registerApiV1AuthRegisterPost, 
  getMeApiV1AuthMeGet,
  logoutApiV1AuthLogoutPost
} from '@/lib/api/generated/sdk.gen';
import { User } from '../types';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');

function decodeJwtPayload(token: string): any | null {
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const payload = atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decodeURIComponent(escape(payload)));
  } catch {
    return null;
  }
}

function persistTokenClaims(accessToken: string) {
  const payload = decodeJwtPayload(accessToken) || {};
  const userType = payload.user_type || payload.type || null;
  const vendorParentId = payload.vendor_parent_id || null;
  if (userType) Cookies.set('user_type', String(userType), { expires: 1/48 });
  if (vendorParentId !== null && vendorParentId !== undefined) Cookies.set('vendor_parent_id', String(vendorParentId), { expires: 1/48 });
}

export async function loginAction(formData: FormData) {
  const email = formData.get('email') as string;
  const password = formData.get('password') as string;

  const response = await loginApiV1AuthLoginPost({
    body: {
      username: email,
      password: password,
    },
  });

  if (response.error) {
    const errorDetail = (response.error as { detail?: string })?.detail || 'Error en la autenticación';
    throw new Error(errorDetail);
  }

  const data = response.data;
  if (!data) throw new Error('No se recibió respuesta del servidor');
  
  // Store tokens in cookies
  Cookies.set('access_token', data.access_token, { expires: 1/48 }); // 30 mins
  Cookies.set('refresh_token', data.refresh_token, { expires: 15 }); // 15 days
  persistTokenClaims(data.access_token);

  return data;
}

export async function loginIamAction(formData: FormData) {
  const email = formData.get('email') as string;
  const password = formData.get('password') as string;
  const vendor_identifier = formData.get('vendor_identifier') as string;

  const res = await fetch(`${API_URL}/auth/login-iam`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, vendor_identifier }),
  });

  if (!res.ok) {
    let detail = 'Error en la autenticación';
    try {
      const err = await res.json();
      detail = err?.detail || detail;
    } catch {}
    throw new Error(detail);
  }

  const data = await res.json();
  Cookies.set('access_token', data.access_token, { expires: 1/48 });
  Cookies.set('refresh_token', data.refresh_token, { expires: 15 });
  persistTokenClaims(data.access_token);
  return data;
}

export async function registerAction(userData: { email: string; password: string; name: string }) {
  const response = await registerApiV1AuthRegisterPost({
    body: {
      email: userData.email,
      password: userData.password,
      name: userData.name,
    },
  });

  if (response.error) {
    const errorData = response.error as { code?: string; detail?: string; message?: string; errors?: Array<{ field: string; message: string }> };
    
    // Si es nuestro error estándar de validación
    if (errorData.code === 'VALIDATION_ERROR' && errorData.errors) {
      const fieldErrors = errorData.errors.map((e: { field: string; message: string }) => `${e.field}: ${e.message}`).join(', ');
      throw new Error(`Error de validación: ${fieldErrors}`);
    }

    const errorDetail = errorData.detail || errorData.message || 'Error en el registro';
    throw new Error(errorDetail);
  }

  return response.data;
}

export async function getCurrentUser(): Promise<User | null> {
  const token = Cookies.get('access_token');
  if (!token) return null;

  const response = await getMeApiV1AuthMeGet({});

  if (response.error) {
    Cookies.remove('access_token');
    return null;
  }

  return response.data as User;
}

export async function logout() {
  const token = Cookies.get('refresh_token');
  if (token) {
    await logoutApiV1AuthLogoutPost({
      query: {
        token_str: token
      }
    });
  }
  
  Cookies.remove('access_token');
  Cookies.remove('refresh_token');
  window.location.href = '/auth/login';
}
