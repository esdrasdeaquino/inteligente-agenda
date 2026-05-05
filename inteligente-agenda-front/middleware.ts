import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token');
  const perfil = request.cookies.get('user_perfil')?.value;

  const isDashboardAdmin = request.nextUrl.pathname.startsWith('/dashboard');
  const isDashboardBarbearia = request.nextUrl.pathname.startsWith('/empresas');

  // Se não estiver logado, manda para o login
  if (!token && (isDashboardAdmin || isDashboardBarbearia)) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Se for "user" tentando entrar no dashboard mestre (admin), bloqueia
  if (perfil === 'user' && isDashboardAdmin) {
    return NextResponse.redirect(new URL('/empresas', request.url));
  }

  // Se for "admin" tentando entrar na rota de cliente, permite ou redireciona
  if (perfil === 'admin' && isDashboardBarbearia) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/empresas/:path*'],
};