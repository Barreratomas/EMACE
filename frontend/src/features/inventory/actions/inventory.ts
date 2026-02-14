'use server'

import { revalidatePath } from 'next/cache';
import { cookies } from 'next/headers';
import { client } from '@/lib/api';
import { 
  readProductsApiV1InventoryProductsGet,
  createProductApiV1InventoryProductsPost,
  updateProductApiV1InventoryProductsProductIdPatch,
  deleteProductApiV1InventoryProductsProductIdDelete,
  getLowStockProductsApiV1InventoryProductsStockLowGet,
  adjustStockApiV1InventoryProductsProductIdStockAdjustPost,
  bulkUpdateProductStatusApiV1InventoryProductsBulkStatusPost
} from '@/lib/api/generated/sdk.gen';

// Asegurar que el cliente tenga la URL base configurada (especialmente importante para Server Actions)
if (!client.getConfig().baseURL) {
  client.setConfig({
    baseURL: (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/api\/v1\/?$/, ''),
  });
}
import { 
  Product as ApiProduct, 
  ProductUpdate, 
  BulkStatusUpdateRequest
} from '@/lib/api/generated/types.gen';
import { Product } from '../types';

async function getAuthHeaders() {
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Helper para manejar errores de la API de forma consistente
 */
function handleApiError(response: any, context: string): never {
  if (!response) {
    throw new Error(`Error fatal en ${context}: No se recibió respuesta del servidor.`);
  }

  const errorData = response.error as { 
    code?: string; 
    message?: string; 
    detail?: string; 
    errors?: Array<{ field: string; message: string }> 
  };
  
  // Extraer el código de estado HTTP de varias posibles ubicaciones
  const status = response.status || response.response?.status;
  
  console.error(`Error en ${context}:`, {
    status,
    errorData,
    message: response.message || 'Sin mensaje de error'
  });

  // 1. Manejar errores de validación personalizados
  if (errorData?.code === 'VALIDATION_ERROR' && errorData.errors) {
    const fieldErrors = errorData.errors.map((e) => `${e.field}: ${e.message}`).join(', ');
    throw new Error(`Error de validación: ${fieldErrors}`);
  }

  // 2. Manejar errores de FastAPI (detail puede ser string o array)
  if (errorData?.detail) {
    if (typeof errorData.detail === 'string') {
      throw new Error(errorData.detail);
    }
    if (Array.isArray(errorData.detail)) {
      const details = (errorData.detail as Array<{ msg?: string }>).map((d) => d.msg || String(d)).join(', ');
      throw new Error(`Error de validación: ${details}`);
    }
  }

  // 3. Manejar mensaje de error genérico o de red
  const errorMsg = errorData?.message || response.message;
  if (errorMsg) {
    throw new Error(`${errorMsg} (Status: ${status || 'Error de Red'})`);
  }

  // 4. Fallback final
  throw new Error(`Error del servidor (${status || 'Desconocido'})`);
}

export async function getProducts(): Promise<Product[]> {
  try {
    const headers = await getAuthHeaders();
    const response = await readProductsApiV1InventoryProductsGet({
      headers,
    });
    
    if (response.error) {
      handleApiError(response, 'getProducts');
    }
    
    return (response.data as Product[]) || [];
  } catch (error: any) {
    // Si ya es un error lanzado por handleApiError, lo relanzamos
    if (error.message.includes('Error de validación') || error.message.includes('Error del servidor') || error.message.includes('Status:')) {
      throw error;
    }
    console.error('getProducts exception:', error);
    throw new Error('No se pudieron cargar los productos. Verifique la conexión con el servidor.');
  }
}

export async function createProduct(data: Partial<Product>) {
  const headers = await getAuthHeaders();
  const response = await createProductApiV1InventoryProductsPost({
    headers,
    body: data as ApiProduct,
  });
  
  if (response.error) {
    handleApiError(response, 'createProduct');
  }
  
  revalidatePath('/inventory');
  return response.data;
}

export async function updateProduct(id: number, data: Partial<Product>) {
  const headers = await getAuthHeaders();
  const response = await updateProductApiV1InventoryProductsProductIdPatch({
    headers,
    path: { product_id: id },
    body: data as ProductUpdate,
  });

  if (response.error) {
    handleApiError(response, 'updateProduct');
  }

  revalidatePath('/inventory');
  return response.data;
}

export async function deleteProduct(id: number) {
  const headers = await getAuthHeaders();
  const response = await deleteProductApiV1InventoryProductsProductIdDelete({
    headers,
    path: { product_id: id },
  });

  if (response.error) {
    handleApiError(response, 'deleteProduct');
  }

  revalidatePath('/inventory');
  return { ok: true };
}

export async function getLowStockProducts(): Promise<Product[]> {
  try {
    const headers = await getAuthHeaders();
    const response = await getLowStockProductsApiV1InventoryProductsStockLowGet({
      headers,
    });
    
    if (response.error) {
      handleApiError(response, 'getLowStockProducts');
    }
    
    return (response.data as Product[]) || [];
  } catch (error: any) {
    console.error('getLowStockProducts exception:', error);
    return [];
  }
}

export async function adjustStock(id: number, quantity_change: number): Promise<Product> {
  const headers = await getAuthHeaders();
  const response = await adjustStockApiV1InventoryProductsProductIdStockAdjustPost({
    headers,
    path: { product_id: id },
    query: { quantity_change },
  });

  if (response.error) {
    handleApiError(response, 'adjustStock');
  }

  revalidatePath('/inventory');
  return response.data as Product;
}

export async function bulkUpdateProductStatus(product_ids: number[], new_status: 'active' | 'paused' | 'archived') {
  const headers = await getAuthHeaders();
  const response = await bulkUpdateProductStatusApiV1InventoryProductsBulkStatusPost({
    headers,
    body: { product_ids, new_status } as BulkStatusUpdateRequest,
  });

  if (response.error) {
    handleApiError(response, 'bulkUpdateProductStatus');
  }

  revalidatePath('/inventory');
  return response.data;
}
