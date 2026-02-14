import { create } from 'zustand';
import type { ToastType } from './use-toast';

export interface NotificationEvent {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  time: string;
  status: 'pending' | 'done';
}

interface NotificationCenterStore {
  events: NotificationEvent[];
  addEvent: (type: ToastType, message: string, title?: string) => void;
  markDone: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationCenterStore = create<NotificationCenterStore>((set) => ({
  events: [],
  addEvent: (type, message, title) => {
    const id = Math.random().toString(36).substring(2, 9);
    const time = new Date().toLocaleString();
    set((state) => ({
      events: [{ id, type, title, message, time, status: 'pending' as const }, ...state.events].slice(0, 200),
    }));
  },
  markDone: (id) =>
    set((state) => ({
      events: state.events.map((e) => (e.id === id ? { ...e, status: 'done' } : e)),
    })),
  clearAll: () =>
    set(() => ({
      events: [],
    })),
}));
