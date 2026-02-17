'use server'

import { revalidatePath } from 'next/cache';
import { apiRequest } from '@/lib/server-api';

export type IAMUser = {
  id: number;
  email: string;
  name: string;
  role_id?: number | null;
  is_active: boolean;
  plan_type: string;
  parent_id?: number;
  last_login?: string | null;
};

export async function listIAMUsers(): Promise<IAMUser[]> {
  const data = await apiRequest<IAMUser[]>('/iam/users', { cache: 'no-store' });
  return data as IAMUser[];
}

export async function createIAMUser(payload: { email: string; password: string; name: string }): Promise<IAMUser> {
  const data = await apiRequest<IAMUser>('/iam/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  revalidatePath('/settings/iam');
  return data as IAMUser;
}

export async function setUserPolicies(userId: number, policies: string[], operation: 'set' | 'add' | 'remove' = 'set'): Promise<IAMUser> {
  const data = await apiRequest<IAMUser>(`/iam/users/${userId}/policies`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ policies, operation }),
  });
  revalidatePath('/settings/iam');
  return data as IAMUser;
}

export async function getUserPolicies(userId: number): Promise<string[]> {
  const data = await apiRequest<string[]>(`/iam/users/${userId}/policies`, { cache: 'no-store' });
  return data as string[];
}
