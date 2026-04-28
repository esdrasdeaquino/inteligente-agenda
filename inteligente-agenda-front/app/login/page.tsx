"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { setCookie } from 'cookies-next';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Chamada para sua API Python
      const response = await fetch('http://localhost:8000/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            usuario: username, 
            senha: password 
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // --- SEGURANÇA REFORÇADA ---
        // Diferente do localStorage, o Cookie é lido pelo Servidor (Middleware)
        // Guardamos o status de autenticação e os dados do usuário por 24 horas
        setCookie('auth_token', 'active_session', { maxAge: 60 * 60 * 24 });
        setCookie('user_nome', data.nome, { maxAge: 60 * 60 * 24 });
        setCookie('user_perfil', data.perfil, { maxAge: 60 * 60 * 24 });
        setCookie('salao_id', data.salao_id, { maxAge: 60 * 60 * 24 });

        // Redireciona para o Dashboard protegido
        router.push('/dashboard');
      } else {
        alert(data.detail || 'Falha na autenticação. Verifique suas credenciais.');
      }
    } catch (error) {
      console.error(error);
      alert('Não foi possível conectar ao servidor. Verifique se a API está ativa.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4 font-sans">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl overflow-hidden border-t-4 border-[#0F2639]">
        
        <div className="p-8">
          <div className="text-center mb-10">
            <h1 className="text-2xl font-bold text-[#0F2639] tracking-tight uppercase">
              INTELIGENTE <span className="text-[#F37125]">AGENDA</span>
            </h1>
            <p className="text-gray-600 text-sm mt-2">Acesso ao Painel Administrativo</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Usuário
              </label>
              <input 
                type="text" 
                required
                value={username}
                className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-md text-gray-900 focus:outline-none focus:border-[#F37125] focus:ring-1 focus:ring-[#F37125] transition"
                placeholder="Digite seu usuário"
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Senha
              </label>
              <input 
                type="password" 
                required
                value={password}
                className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-md text-gray-900 focus:outline-none focus:border-[#F37125] focus:ring-1 focus:ring-[#F37125] transition"
                placeholder="Digite sua senha"
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button 
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[#F37125] hover:bg-[#e0611d] text-white font-bold rounded-md shadow-md transition duration-200 ease-in-out transform active:scale-95 disabled:opacity-50 uppercase tracking-widest"
            >
              {loading ? 'AUTENTICANDO...' : 'ENTRAR'}
            </button>
          </form>
        </div>
        
        <div className="bg-gray-50 py-4 text-center border-t border-gray-100">
          <p className="text-xs text-gray-400">
            © 2026 Inteligente Agenda - Todos os direitos reservados.
          </p>
        </div>
      </div>
    </div>
  );
}