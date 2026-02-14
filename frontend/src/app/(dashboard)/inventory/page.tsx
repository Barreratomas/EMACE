import { getProducts, InventoryList } from '@/features/inventory';

export const dynamic = 'force-dynamic'; 

export default async function InventoryPage() {
  const products = await getProducts();

  return (
    <div className="container mx-auto py-10 px-4">
      <InventoryList initialProducts={products} />
    </div>
  );
}
