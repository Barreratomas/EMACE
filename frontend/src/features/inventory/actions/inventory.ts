'use server'

import { revalidatePath } from 'next/cache';
import { Product } from '../types';
import { apiRequest, buildApiUrl } from '@/lib/server-api';

export async function getProducts(): Promise<Product[]> {
  const data = await apiRequest<Product[]>('/inventory/products/', {
    cache: 'no-store',
  });
  return data;
}

export async function createProduct(data: Partial<Product>) {
  const result = await apiRequest('/inventory/products/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  revalidatePath('/inventory');
  return result;
}

export async function importProducts(formData: FormData, conflictStrategy: string = 'skip', dryRun: boolean = false) {
  try {
    const url = buildApiUrl('/inventory/import', {
      conflict_strategy: conflictStrategy,
      dry_run: dryRun.toString(),
    });
    const response = await apiRequest(url, {
      method: 'POST',
      body: formData,
    });
    revalidatePath('/inventory');
    return { success: true, ...response };
  } catch (error: any) {
    console.error('[Exception] importProducts:', error);
    return { success: false, error: error.message };
  }
}

export async function updateProduct(id: number, data: Partial<Product>) {
  const result = await apiRequest(`/inventory/products/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  revalidatePath('/inventory');
  return result as Product;
}

export async function deleteProduct(id: number) {
  await apiRequest(`/inventory/products/${id}`, {
    method: 'DELETE',
  });
  revalidatePath('/inventory');
  return { ok: true };
}

export async function getLowStockProducts(): Promise<Product[]> {
  try {
    const data = await apiRequest<Product[]>('/inventory/products/stock/low', {
      cache: 'no-store',
    });
    return data as Product[];
  } catch (error: any) {
    console.error('getLowStockProducts exception:', error);
    return [];
  }
}

export async function adjustStock(id: number, quantity_change: number): Promise<Product> {
  const url = buildApiUrl(`/inventory/products/${id}/stock/adjust`, {
    quantity_change: quantity_change.toString(),
  });
  const data = await apiRequest<Product>(url, {
    method: 'POST',
  });
  revalidatePath('/inventory');
  return data as Product;
}

export async function bulkUpdateProductStatus(product_ids: number[], new_status: 'active' | 'paused' | 'archived') {
  const data = await apiRequest('/inventory/products/bulk/status', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ product_ids, new_status }),
  });
  revalidatePath('/inventory');
  return data;
}
