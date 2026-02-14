import { render, screen, fireEvent } from '@testing-library/react';
import TopBar from '../TopBar';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock de next/navigation
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => '/dashboard'),
}));

// Mock de localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('TopBar component', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  it('renders correctly with default values', () => {
    render(<TopBar />);
    expect(screen.getByText(/ADMIN_USER_01/i)).toBeInTheDocument();
    expect(screen.getByText(/CPU:/i)).toBeInTheDocument();
    expect(screen.getByText(/12%/i)).toBeInTheDocument();
  });

  it('toggles theme when clicking the theme button', () => {
    render(<TopBar />);
    const themeButton = screen.getByLabelText(/Cambiar tema/i);
    
    // Default should be dark (no data-theme attribute or 'dark' in localStorage)
    expect(document.documentElement.getAttribute('data-theme')).toBeNull();

    // Toggle to light
    fireEvent.click(themeButton);
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(window.localStorage.getItem('theme')).toBe('light');

    // Toggle back to dark
    fireEvent.click(themeButton);
    expect(document.documentElement.getAttribute('data-theme')).toBeNull();
    expect(window.localStorage.getItem('theme')).toBe('dark');
  });
});
