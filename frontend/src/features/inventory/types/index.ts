export interface Product {
  id: number;
  name: string;
  category: string;
  price: number;
  type: 'physical' | 'service';
  status: 'active' | 'paused' | 'archived';
  stock?: number;
  min_stock_threshold?: number;
  sla?: string;
  description: string;
}
