"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { setCookie } from "cookies-next";

export default function LoginPage() {
  const router = useRouter();
  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const res = await fetch("http://localhost:8000/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario, senha }),
      });

      if (res.ok) {
        const data = await res.json();
        
        // Salva as informações essenciais nos cookies para o Middleware e Dashboards
        setCookie("auth_token", "true"); // Simulação de token
        setCookie("user_perfil", data.perfil);
        setCookie("salao_id", data.salao_id);
        setCookie("user_nome", data.nome);

        // Lógica de Redirecionamento Baseada no Perfil[cite: 2]
        if (data.perfil === "admin") {
          router.push("/dashboard"); // Tela mestre que você já tem
        } else {
          router.push("/empresas"); // Nova tela do cliente
        }
      } else {
        setError("Usuário ou senha incorretos.");
      }
    } catch (err) {
      setError("Erro ao conectar com o servidor.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F2639] p-4">
      <div className="bg-white p-10 rounded-3xl shadow-2xl w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-black text-gray-800 uppercase tracking-tighter">Inteligente Agenda</h1>
          <p className="text-gray-400 text-xs uppercase font-bold">Acesse sua conta</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold text-gray-400 uppercase">Usuário</label>
            <input 
              type="text" 
              className="p-3 bg-gray-50 border rounded-xl outline-none focus:ring-2 focus:ring-[#F37125]" 
              value={usuario} 
              onChange={e => setUsuario(e.target.value)} 
              required 
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold text-gray-400 uppercase">Senha</label>
            <input 
              type="password" 
              className="p-3 bg-gray-50 border rounded-xl outline-none focus:ring-2 focus:ring-[#F37125]" 
              value={senha} 
              onChange={e => setSenha(e.target.value)} 
              required 
            />
          </div>
          
          {error && <p className="text-red-500 text-xs font-bold text-center">{error}</p>}

          <button 
            type="submit" 
            className="w-full bg-[#F37125] text-white p-4 rounded-xl font-black uppercase shadow-lg hover:scale-105 transition-all"
          >
            Entrar no Painel
          </button>
        </form>
      </div>
    </div>
  );
}