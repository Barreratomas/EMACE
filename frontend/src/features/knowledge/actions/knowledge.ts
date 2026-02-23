'use server'

import { revalidatePath } from 'next/cache';
import { KnowledgeDocument, KnowledgeUsage } from '../types';
import { apiRequest } from '@/lib/server-api';

export async function getKnowledgeDocuments(): Promise<KnowledgeDocument[]> {
  try {
    const data = await apiRequest<KnowledgeDocument[]>('/knowledge/documents', {
      cache: 'no-store'
    });
    return data;
  } catch (error) {
    console.error('Error fetching knowledge docs:', error);
    return [];
  }
}

export async function getKnowledgeUsage(): Promise<KnowledgeUsage | null> {
  try {
    const data = await apiRequest<KnowledgeUsage>('/knowledge/usage', {
      cache: 'no-store'
    });
    return data;
  } catch (error) {
    console.error('Error fetching knowledge usage:', error);
    return null;
  }
}

export async function uploadKnowledgeDocument(formData: FormData) {
  try {
    await apiRequest('/knowledge/upload', {
      method: 'POST',
      body: formData,
    });
    revalidatePath('/knowledge');
    return { success: true };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}

export async function deleteKnowledgeDocument(sourceName: string) {
  try {
    await apiRequest(`/knowledge/documents/${encodeURIComponent(sourceName)}`, {
      method: 'DELETE',
    });
    revalidatePath('/knowledge');
    return { success: true };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}
