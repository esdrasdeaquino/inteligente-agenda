// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token');

  // Se o cara tenta acessar qualquer rota que comece com /dashboard
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    // Se não tem token, tchau!
    if (!token) {
      return NextResponse.redirect(new URL('/', request.url)); 
    }
  }

  return NextResponse.next();
}

// Configura o middleware para rodar APENAS no dashboard
export const config = {
  matcher: ['/dashboard/:path*'],
};