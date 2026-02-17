import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import InventoryList from '../InventoryList';
import type { Product } from '../../types';

const products: Product[] = [
  { id: 1, name: 'A', category: 'Cat', price: 10, type: 'physical', status: 'active', stock: 2, min_stock_threshold: 5, description: 'Product A description' },
  { id: 2, name: 'B', category: 'Cat', price: 20, type: 'service', status: 'paused', stock: 0, min_stock_threshold: 0, description: 'Service B description' },
  { id: 3, name: 'C', category: 'Other', price: 30, type: 'physical', status: 'archived', stock: 10, min_stock_threshold: 5, description: 'Product C description' },
];

describe('InventoryList filtering', () => {
  it('filters by status: only paused when selecting Pausa', () => {
    render(<InventoryList initialProducts={products} />);
    expect(screen.getByText(/Inventario Central/i)).toBeInTheDocument();
    const pausedButton = screen.getByRole('button', { name: /Pausa/i });
    fireEvent.click(pausedButton);
    expect(screen.queryByText(/^A$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^C$/)).not.toBeInTheDocument();
    expect(screen.getByText(/^B$/)).toBeInTheDocument();
  });
});
