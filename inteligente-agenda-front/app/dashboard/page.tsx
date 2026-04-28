"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCookie, deleteCookie } from "cookies-next";

export default function AdminDashboard() {
  const router = useRouter();
  
  // Estados para gestão de dados e interface
  const [abaAtiva, setAbaAtiva] = useState("empresas");
  const [dados, setDados] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // Estado para os campos do formulário
  const [formData, setFormData] = useState({
    nome: "",
    whatsapp: "",
    usuario: "",
    senha: "",
    perfil: "barbeiro",
    id_empresa: ""
  });

  // Função para carregar os dados da API
  const carregarDados = async (tipo: string) => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/admin/${tipo}`);
      if (res.ok) {
        const json = await res.json();
        setDados(json);
      }
    } catch (err) {
      console.error("Erro ao carregar dados:", err);
    } finally {
      setLoading(false);
    }
  };

  // Carrega os dados sempre que a aba mudar
  useEffect(() => {
    carregarDados(abaAtiva);
  }, [abaAtiva]);

  // Função para Logout (Limpa cookies e redireciona)
  const handleLogout = () => {
    deleteCookie('auth_token');
    deleteCookie('user_nome');
    deleteCookie('user_perfil');
    router.push('/');
  };

  // Função para guardar novo registo via POST
  const handleSalvar = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`http://localhost:8000/admin/${abaAtiva}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        setIsModalOpen(false);
        setFormData({ nome: "", whatsapp: "", usuario: "", senha: "", perfil: "barbeiro", id_empresa: "" });
        carregarDados(abaAtiva);
        alert("Registo guardado com sucesso!");
      }
    } catch (err) {
      alert("Erro ao comunicar com o servidor.");
    }
  };

  // Função para remover um registo
  const deletarItem = async (id: number) => {
    if (confirm("Tem a certeza que deseja remover este registo?")) {
      try {
        const res = await fetch(`http://localhost:8000/admin/${abaAtiva}/${id}`, { 
          method: "DELETE" 
        });
        if (res.ok) carregarDados(abaAtiva);
      } catch (err) {
        alert("Erro ao eliminar.");
      }
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-100 font-sans">
      
      {/* SIDEBAR */}
      <aside className="w-64 bg-[#0F2639] text-white p-6 shadow-2xl flex flex-col">
        <div className="mb-10 text-center">
          <h2 className="text-xl font-bold text-[#F37125] tracking-tighter uppercase">
            Painel Central
          </h2>
          <p className="text-[10px] text-gray-400 mt-1">SISTEMA DE GESTÃO</p>
        </div>

        <nav className="space-y-2 flex-1">
          <button 
            onClick={() => setAbaAtiva("empresas")} 
            className={`w-full text-left p-3 rounded-lg transition-all ${abaAtiva === 'empresas' ? 'bg-[#F37125] font-bold' : 'hover:bg-gray-800 text-gray-300'}`}
          >
            🏢 Empresas
          </button>
          <button 
            onClick={() => setAbaAtiva("usuarios")} 
            className={`w-full text-left p-3 rounded-lg transition-all ${abaAtiva === 'usuarios' ? 'bg-[#F37125] font-bold' : 'hover:bg-gray-800 text-gray-300'}`}
          >
            👥 Utilizadores
          </button>
          <button 
            onClick={() => setAbaAtiva("profissionais")} 
            className={`w-full text-left p-3 rounded-lg transition-all ${abaAtiva === 'profissionais' ? 'bg-[#F37125] font-bold' : 'hover:bg-gray-800 text-gray-300'}`}
          >
            ✂️ Profissionais
          </button>
        </nav>

        <button 
          onClick={handleLogout}
          className="mt-auto border border-red-500/50 text-red-400 p-3 rounded-lg hover:bg-red-500 hover:text-white transition-all text-sm font-bold uppercase"
        >
          Sair do Sistema
        </button>
      </aside>

      {/* CONTEÚDO PRINCIPAL */}
      <main className="flex-1 p-10">
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-black text-gray-800 uppercase tracking-tighter">
              Gestão de {abaAtiva}
            </h1>
            <p className="text-gray-500 text-sm">Visualize e gira os registos da base de dados.</p>
          </div>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="bg-[#F37125] text-white px-6 py-3 rounded-xl font-bold shadow-lg hover:scale-105 active:scale-95 transition-all uppercase text-sm"
          >
            + Adicionar Novo
          </button>
        </div>

        {/* TABELA DE DADOS */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 border-b text-gray-400 text-[10px] font-black uppercase tracking-widest">
              <tr>
                <th className="p-5">ID</th>
                <th className="p-5">Informação Principal</th>
                <th className="p-5">Detalhes</th>
                <th className="p-5 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr><td colSpan={4} className="p-10 text-center text-gray-400">A carregar dados...</td></tr>
              ) : dados.length > 0 ? (
                dados.map((item: any) => (
                  <tr key={item.id} className="hover:bg-blue-50/50 transition-colors group">
                    <td className="p-5 text-gray-300 font-mono text-xs">#{item.id}</td>
                    <td className="p-5">
                      <div className="flex flex-col">
                        <span className="font-bold text-gray-700">
                          {item.nome || item.usuario || item.nome_empresa}
                        </span>
                        <span className="text-xs text-gray-400">{item.whatsapp || item.email || ""}</span>
                      </div>
                    </td>
                    <td className="p-5">
                      <span className="bg-gray-100 text-gray-500 text-[10px] px-2 py-1 rounded font-black uppercase">
                        {item.plano || item.perfil || "Ativo"}
                      </span>
                    </td>
                    <td className="p-5 text-right">
                      <button 
                        onClick={() => deletarItem(item.id)}
                        className="text-red-400 hover:text-red-600 font-bold text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        REMOVER
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={4} className="p-10 text-center text-gray-400 italic">Sem registos encontrados.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* MODAL DE CADASTRO */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl animate-in fade-in zoom-in duration-200">
              <h2 className="text-2xl font-bold mb-6 text-gray-800 uppercase tracking-tighter">
                Novo: {abaAtiva}
              </h2>
              
              <form onSubmit={handleSalvar} className="space-y-4">
                {abaAtiva === "empresas" ? (
                  <>
                    <input type="text" placeholder="Nome da Empresa" className="w-full p-4 bg-gray-50 border rounded-xl" required 
                      onChange={(e) => setFormData({...formData, nome: e.target.value})} />
                    <input type="text" placeholder="WhatsApp (ex: 351...)" className="w-full p-4 bg-gray-50 border rounded-xl" required 
                      onChange={(e) => setFormData({...formData, whatsapp: e.target.value})} />
                  </>
                ) : (
                  <>
                    <input type="text" placeholder="Nome Completo" className="w-full p-4 bg-gray-50 border rounded-xl" required 
                      onChange={(e) => setFormData({...formData, nome: e.target.value})} />
                    <input type="text" placeholder="Utilizador / Login" className="w-full p-4 bg-gray-50 border rounded-xl" required 
                      onChange={(e) => setFormData({...formData, usuario: e.target.value})} />
                    <input type="password" placeholder="Senha" className="w-full p-4 bg-gray-50 border rounded-xl" required 
                      onChange={(e) => setFormData({...formData, senha: e.target.value})} />
                  </>
                )}

                <div className="flex gap-3 mt-8">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 p-4 bg-gray-100 text-gray-500 rounded-xl font-bold hover:bg-gray-200 transition-all">
                    CANCELAR
                  </button>
                  <button type="submit" className="flex-1 p-4 bg-[#F37125] text-white rounded-xl font-bold shadow-lg hover:bg-[#e0611d] transition-all">
                    GUARDAR
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}