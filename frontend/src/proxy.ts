import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function proxy(request: NextRequest) {
  const accessToken = request.cookies.get('access_token')?.value;
  const refreshToken = request.cookies.get('refresh_token')?.value;
  const { pathname } = request.nextUrl;

  const isPublicPath = pathname.startsWith('/auth') || pathname === '/';

  // Sin ningún token y ruta protegida → login directo
  if (!accessToken && !refreshToken && !isPublicPath) {
    const url = request.nextUrl.clone();
    url.pathname = '/auth/login';
    return NextResponse.redirect(url);
  }

  // Sin access_token pero con refresh_token en ruta protegida → intentar refrescar en backend
  if (!accessToken && refreshToken && !isPublicPath) {
    try {
      const base =
        process.env.BACKEND_INTERNAL_URL ||
        process.env.NEXT_PUBLIC_API_URL ||
        'http://localhost:8000/api/v1';

      const normalizedBase = base.replace(/\/+$/, '');
      const refreshUrl = `${normalizedBase}/auth/refresh?token_str=${encodeURIComponent(
        refreshToken,
      )}`;

      const res = await fetch(refreshUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (res.ok) {
        const data = (await res.json()) as {
          access_token?: string;
          refresh_token?: string;
        };
        const { access_token, refresh_token } = data || {};

        if (access_token) {
          const response = NextResponse.next();

          const accessExpires = new Date(Date.now() + 30 * 60 * 1000);
          response.cookies.set('access_token', access_token, {
            path: '/',
            expires: accessExpires,
          });

          if (refresh_token) {
            const refreshExpires = new Date(
              Date.now() + 15 * 24 * 60 * 60 * 1000,
            );
            response.cookies.set('refresh_token', refresh_token, {
              path: '/',
              expires: refreshExpires,
            });
          }

          return response;
        }
      }
    } catch {
      // Si falla el refresh, continuamos al flujo de logout
    }

    const url = request.nextUrl.clone();
    url.pathname = '/auth/login';
    const response = NextResponse.redirect(url);
    response.cookies.delete('access_token');
    response.cookies.delete('refresh_token');
    return response;
  }

  if (accessToken && isPublicPath && pathname !== '/') {
    const url = request.nextUrl.clone();
    url.pathname = '/inventory';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// See "Matching Paths" below to learn more
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
