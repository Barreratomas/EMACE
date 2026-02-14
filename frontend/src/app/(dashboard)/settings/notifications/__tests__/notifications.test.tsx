import { render, screen, fireEvent } from '@testing-library/react';
import NotificationCenterPage from '../page';
import { useNotificationCenterStore, NotificationEvent } from '@/hooks/use-notifications';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';

// Mock del store de Zustand
vi.mock('@/hooks/use-notifications', () => ({
  useNotificationCenterStore: vi.fn(),
}));

describe('NotificationCenterPage', () => {
  const mockEvents: NotificationEvent[] = [
    { id: '1', type: 'info', title: 'Test Info', message: 'Message 1', status: 'pending', time: '1m ago' },
    { id: '2', type: 'success', title: 'Test Success', message: 'Message 2', status: 'done', time: '2m ago' },
  ];

  const mockMarkDone = vi.fn();
  const mockClearAll = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useNotificationCenterStore as unknown as Mock).mockReturnValue({
      events: mockEvents,
      markDone: mockMarkDone,
      clearAll: mockClearAll,
    });
  });

  it('renders notifications correctly', () => {
    render(<NotificationCenterPage />);
    expect(screen.getByText(/CENTRO_DE_NOTIFICACIONES/i)).toBeInTheDocument();
    expect(screen.getByText(/Test Info/i)).toBeInTheDocument();
    expect(screen.getByText(/Test Success/i)).toBeInTheDocument();
  });

  it('filters notifications by status', () => {
    render(<NotificationCenterPage />);
    
    // Initial state: all notifications visible
    expect(screen.getByText(/Test Info/i)).toBeInTheDocument();
    expect(screen.getByText(/Test Success/i)).toBeInTheDocument();

    // Filter by pending
    fireEvent.click(screen.getByRole('button', { name: /Pendientes/i }));
    expect(screen.getByText(/Test Info/i)).toBeInTheDocument();
    expect(screen.queryByText(/Test Success/i)).not.toBeInTheDocument();

    // Filter by done
    fireEvent.click(screen.getByRole('button', { name: /Completadas/i }));
    expect(screen.queryByText(/Test Info/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Test Success/i)).toBeInTheDocument();
  });

  it('calls markDone when clicking the action button', () => {
    render(<NotificationCenterPage />);
    const markButton = screen.getByText(/Marcar/i);
    fireEvent.click(markButton);
    expect(mockMarkDone).toHaveBeenCalledWith('1');
  });

  it('calls clearAll when clicking the clear button', () => {
    render(<NotificationCenterPage />);
    const clearButton = screen.getByText(/Limpiar/i);
    fireEvent.click(clearButton);
    expect(mockClearAll).toHaveBeenCalled();
  });
});
