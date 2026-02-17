import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import TelegramSettingsPage from '../page';

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockDelete = vi.fn();

vi.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}));

const mockToastSuccess = vi.fn();
const mockToastError = vi.fn();
const mockToastInfo = vi.fn();

vi.mock('@/hooks/use-toast', () => ({
  toast: {
    success: (...args: any[]) => mockToastSuccess(...args),
    error: (...args: any[]) => mockToastError(...args),
    info: (...args: any[]) => mockToastInfo(...args),
  },
}));

describe('TelegramSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockImplementation((url: string) => {
      if (url === '/vendors/me/integrations/telegram/status') {
        return Promise.resolve({ data: { has_integration: false } });
      }
      if (url === '/vendors/me/integrations/telegram/mtproto/status') {
        return Promise.resolve({
          data: {
            vendor_id: 1,
            allowed: true,
            mtproto_enabled: false,
            mtproto_status: 'inactive',
            last_heartbeat_at: null,
            last_error: null,
          },
        });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('llama al endpoint de estado al montar', async () => {
    render(<TelegramSettingsPage />);
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/vendors/me/integrations/telegram/status');
    });
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith(
        '/vendors/me/integrations/telegram/mtproto/status',
      );
    });
  });

it('requiere consentimiento antes de enviar userbot', async () => {
    render(<TelegramSettingsPage />);

  const consentButton = screen.getByRole('button', {
      name: /Guardar consentimiento y habilitar userbot/i,
    });
    fireEvent.click(consentButton);

    expect(mockToastError).toHaveBeenCalled();
    expect(mockPost).not.toHaveBeenCalledWith(
      '/vendors/me/integrations/telegram/mtproto/consent',
      expect.anything(),
    );
  });

  it('envía el consentimiento de userbot cuando el checkbox está marcado', async () => {
    render(<TelegramSettingsPage />);

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    mockPost.mockResolvedValueOnce({ data: { ok: true, terms_version: 'v1' } });

    const consentButton = screen.getByRole('button', {
      name: /Guardar consentimiento y habilitar userbot/i,
    });
    fireEvent.click(consentButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/vendors/me/integrations/telegram/mtproto/consent', {
        accepted: true,
        terms_version: 'v1',
      });
    });
  });

  it('envía el número de teléfono al iniciar el login MTProto', async () => {
    render(<TelegramSettingsPage />);

    const phoneInput = await screen.findByPlaceholderText(/Número de teléfono/i);
    fireEvent.change(phoneInput, { target: { value: '+5491123456789' } });

    mockPost.mockResolvedValueOnce({
      data: {
        challenge_id: 'abc123',
        mode: 'code_or_qr',
        expires_in_seconds: 300,
        message: 'ok',
      },
    });

    const sendCodeButton = screen.getByRole('button', { name: /Enviar código/i });

    await waitFor(() => {
      expect(sendCodeButton).not.toBeDisabled();
    });

    fireEvent.click(sendCodeButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        '/vendors/me/integrations/telegram/mtproto/session/init',
        {
          phone_number: '+5491123456789',
        },
      );
    });
  });

  it('envía el código MTProto al confirmar', async () => {
    render(<TelegramSettingsPage />);

    const phoneInput = await screen.findByPlaceholderText(/Número de teléfono/i);
    fireEvent.change(phoneInput, { target: { value: '+5491123456789' } });

    mockPost.mockResolvedValueOnce({
      data: {
        challenge_id: 'abc123',
        mode: 'code_or_qr',
        expires_in_seconds: 300,
        message: 'ok',
      },
    });

    const sendCodeButton = screen.getByRole('button', { name: /Enviar código/i });

    await waitFor(() => {
      expect(sendCodeButton).not.toBeDisabled();
    });

    fireEvent.click(sendCodeButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        '/vendors/me/integrations/telegram/mtproto/session/init',
        {
          phone_number: '+5491123456789',
        },
      );
    });

    mockPost.mockResolvedValueOnce({
      data: {
        ok: true,
        status: 'ready',
      },
    });

    const codeInput = screen.getByPlaceholderText(/Código de Telegram/i);
    fireEvent.change(codeInput, { target: { value: '12345' } });

    const confirmButton = screen.getByRole('button', { name: /Confirmar código/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        '/vendors/me/integrations/telegram/mtproto/session/confirm',
        {
          code: '12345',
          phone_number: '+5491123456789',
        },
      );
    });
  });
});
