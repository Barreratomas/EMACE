'use client';

import Cookies from 'js-cookie';
import { 
  loginApiV1AuthLoginPost, 
  registerApiV1AuthRegisterPost, 
  getMeApiV1AuthMeGet,
  logoutApiV1AuthLogoutPost
} from '@/lib/api/generated/sdk.gen';
import { User } from '../types';

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
  Cookies.set('refresh_token', data.refresh_token, { expires: 7 }); // 7 days

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
