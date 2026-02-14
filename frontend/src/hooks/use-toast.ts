import { create } from 'zustand';
import { useNotificationCenterStore } from './use-notifications';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  title?: string;
}

interface ToastStore {
  toasts: Toast[];
  addToast: (message: string, type: ToastType, title?: string) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (message, type, title) => {
    const id = Math.random().toString(36).substring(2, 9);
    set((state) => ({
      toasts: [...state.toasts, { id, message, type, title }],
    }));
    useNotificationCenterStore.getState().addEvent(type, message, title);

    // Auto remove after 5 seconds
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
    }, 5000);
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));

export const toast = {
  info: (message: string, title?: string) => useToastStore.getState().addToast(message, 'info', title),
  success: (message: string, title?: string) => useToastStore.getState().addToast(message, 'success', title),
  warning: (message: string, title?: string) => useToastStore.getState().addToast(message, 'warning', title),
  error: (message: string, title?: string) => useToastStore.getState().addToast(message, 'error', title),
};
