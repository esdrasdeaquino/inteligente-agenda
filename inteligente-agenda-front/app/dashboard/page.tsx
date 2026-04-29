"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { deleteCookie } from "cookies-next";

export default function AdminDashboard() {
  const router = useRouter();
  
  // Estados de controle
  const [abaAtiva, setAbaAtiva] = useState("empresas");
  const [dados, setDados] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editId, setEditId] = useState<any>(null);
  const [termoBusca, setTermoBusca] = useState("");

  // Estado unificado para o formulário
  const [formData, setFormData] = useState<any>({});

  // Carregar dados da API
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

  useEffect(() => {
    carregarDados(abaAtiva);
    setTermoBusca(""); // Limpa o filtro ao trocar de aba
  }, [abaAtiva]);

  // Lógica de Filtro em tempo real
  const dadosFiltrados = dados.filter((item: any) => {
    const busca = termoBusca.toLowerCase();
    const nome = (item.nome || item.nome_empresa || item.usuario || "").toLowerCase();
    const extra = (item.whatsapp_numero || item.perfil || "").toLowerCase();
    return nome.includes(busca) || extra.includes(busca);
  });

  const handleLogout = () => {
    deleteCookie('auth_token');
    router.push('/');
  };

  const abrirModalEdicao = (item: any) => {
    setEditId(item.id);
    setFormData({ ...item });
    setIsModalOpen(true);
  };

  const fecharModal = () => {
    setIsModalOpen(false);
    setEditId(null);
    setFormData({});
  };

  const handleSalvar = async (e: React.FormEvent) => {
    e.preventDefault();
    const isEditing = !!editId;
    const url = `http://localhost:8000/admin/${abaAtiva}${isEditing ? `/${editId}` : ""}`;
    
    try {
      const res = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        fecharModal();
        carregarDados(abaAtiva);
        alert(isEditing ? "Atualizado com sucesso!" : "Cadastrado com sucesso!");
      }
    } catch (err) {
      alert("Erro ao salvar dados.");
    }
  };

  const deletarItem = async (id: any) => {
    if (confirm("Deseja realmente remover este registro?")) {
      try {
        const res = await fetch(`http://localhost:8000/admin/${abaAtiva}/${id}`, { 
          method: "DELETE" 
        });
        if (res.ok) carregarDados(abaAtiva);
      } catch (err) {
        alert("Erro ao remover.");
      }
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-100 font-sans">
      
      {/* SIDEBAR */}
      <aside className="w-64 bg-[#0F2639] text-white p-6 flex flex-col shadow-xl">
        <div className="mb-10 text-center">
          <h2 className="text-xl font-bold text-[#F37125] uppercase tracking-tighter">Painel Admin</h2>
          <p className="text-[10px] text-gray-400">INTELLIGENT AGENDA</p>
        </div>

        <nav className="space-y-2 flex-1">
          {["empresas", "usuarios", "profissionais", "servicos"].map((aba) => (
            <button 
              key={aba}
              onClick={() => setAbaAtiva(aba)} 
              className={`w-full text-left p-3 rounded-lg capitalize transition-all ${abaAtiva === aba ? 'bg-[#F37125] font-bold shadow-lg' : 'hover:bg-gray-800 text-gray-300'}`}
            >
              {aba === "empresas" && "🏢 "}
              {aba === "usuarios" && "👥 "}
              {aba === "profissionais" && "✂️ "}
              {aba === "servicos" && "🛠️ "}
              {aba}
            </button>
          ))}
        </nav>

        <button onClick={handleLogout} className="mt-auto border border-red-500/50 text-red-400 p-3 rounded-lg hover:bg-red-500 hover:text-white transition-all text-xs font-bold uppercase">
          Sair do Sistema
        </button>
      </aside>

      {/* CONTEÚDO */}
      <main className="flex-1 p-10">
        <div className="flex justify-between items-end mb-10">
          <div>
            <h1 className="text-3xl font-black text-gray-800 uppercase tracking-tighter">Gestão de {abaAtiva}</h1>
            <p className="text-gray-500 text-sm">Administre todos os registros do sistema.</p>
          </div>

          {/* FILTRO E BOTÃO ADICIONAR */}
          <div className="flex gap-4">
            <div className="relative">
              <input 
                type="text" 
                placeholder={`Buscar ${abaAtiva}...`} 
                value={termoBusca}
                onChange={(e) => setTermoBusca(e.target.value)}
                className="pl-4 pr-4 py-3 bg-white border border-gray-200 rounded-xl w-72 shadow-sm focus:ring-2 focus:ring-[#F37125] outline-none transition-all text-sm"
              />
            </div>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="bg-[#F37125] text-white px-8 py-3 rounded-xl font-bold shadow-lg hover:scale-105 active:scale-95 transition-all uppercase text-xs"
            >
              + Adicionar Novo
            </button>
          </div>
        </div>

        {/* TABELA */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b text-gray-400 text-[10px] font-black uppercase tracking-widest">
              <tr>
                <th className="p-5">ID</th>
                <th className="p-5">Informação</th>
                <th className="p-5">Detalhes</th>
                <th className="p-5 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr><td colSpan={4} className="p-10 text-center text-gray-400">Carregando dados...</td></tr>
              ) : dadosFiltrados.length > 0 ? (
                dadosFiltrados.map((item: any) => (
                  <tr key={item.id} className="hover:bg-blue-50/30 transition-colors group">
                    <td className="p-5 text-gray-300 font-mono text-xs">#{String(item.id).slice(0, 8)}</td>
                    <td className="p-5 font-bold text-gray-700">
                      {item.nome_empresa || item.nome || item.usuario}
                    </td>
                    <td className="p-5">
                      <span className="bg-gray-100 text-gray-500 text-[10px] px-2 py-1 rounded font-black uppercase">
                        {item.plano || item.perfil || (item.preco ? `${item.preco} R$` : "Ativo")}
                      </span>
                    </td>
                    <td className="p-5 text-right space-x-3">
                      <button onClick={() => abrirModalEdicao(item)} className="text-blue-500 hover:text-blue-700 font-bold text-xs">EDITAR</button>
                      <button onClick={() => deletarItem(item.id)} className="text-red-400 hover:text-red-600 font-bold text-xs">REMOVER</button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={4} className="p-10 text-center text-gray-400 italic font-sm">Nenhum resultado encontrado para "{termoBusca}".</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* MODAL DINÂMICO */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-3xl p-8 w-full max-w-2xl shadow-2xl overflow-y-auto max-h-[90vh]">
              <h2 className="text-2xl font-bold mb-6 text-gray-800 uppercase tracking-tighter">
                {editId ? "Editar" : "Novo"} {abaAtiva}
              </h2>
              
              <form onSubmit={handleSalvar} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* CAMPOS PARA EMPRESAS */}
                {abaAtiva === "empresas" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome da Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome_empresa || ""} onChange={e => setFormData({...formData, nome_empresa: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">WhatsApp Número</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.whatsapp_numero || ""} onChange={e => setFormData({...formData, whatsapp_numero: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Cidade</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.cidade || ""} onChange={e => setFormData({...formData, cidade: e.target.value})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Plano</label>
                      <select className="p-3 bg-gray-50 border rounded-xl" value={formData.plano || "essencial"} onChange={e => setFormData({...formData, plano: e.target.value})}>
                        <option value="essencial">Essencial</option>
                        <option value="pro">Profissional</option>
                        <option value="enterprise">Enterprise</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome da IA</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.ia_nome || ""} onChange={e => setFormData({...formData, ia_nome: e.target.value})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Estilo da IA</label>
                      <select className="p-3 bg-gray-50 border rounded-xl" value={formData.ia_estilo || "Amigável"} onChange={e => setFormData({...formData, ia_estilo: e.target.value})}>
                        <option value="Amigável">Amigável</option>
                        <option value="Profissional">Profissional</option>
                        <option value="Sério">Sério</option>
                      </select>
                    </div>
                  </>
                )}

                {/* CAMPOS PARA USUÁRIOS */}
                {abaAtiva === "usuarios" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome Exibição</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome || ""} onChange={e => setFormData({...formData, nome: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Usuário/Login</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.usuario || ""} onChange={e => setFormData({...formData, usuario: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Senha</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="password" placeholder="Nova senha" onChange={e => setFormData({...formData, senha: e.target.value})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Perfil</label>
                      <select className="p-3 bg-gray-50 border rounded-xl" value={formData.perfil || "user"} onChange={e => setFormData({...formData, perfil: e.target.value})}>
                        <option value="admin">Administrador</option>
                        <option value="user">Usuário Comum</option>
                        <option value="barbeiro">Barbeiro</option>
                      </select>
                    </div>
                  </>
                )}

                {/* CAMPOS PARA PROFISSIONAIS */}
                {abaAtiva === "profissionais" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome Profissional</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome || ""} onChange={e => setFormData({...formData, nome: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID da Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: e.target.value})} required />
                    </div>
                  </>
                )}

                {/* CAMPOS PARA SERVIÇOS */}
                {abaAtiva === "servicos" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome do Serviço</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome || ""} onChange={e => setFormData({...formData, nome: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Preço (R$)</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" step="0.01" value={formData.preco || ""} onChange={e => setFormData({...formData, preco: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Duração (Minutos)</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.duracao_minutos || ""} onChange={e => setFormData({...formData, duracao_minutos: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID da Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: e.target.value})} required />
                    </div>
                  </>
                )}

                <div className="md:col-span-2 flex gap-3 mt-6">
                  <button type="button" onClick={fecharModal} className="flex-1 p-4 bg-gray-100 text-gray-500 rounded-xl font-bold hover:bg-gray-200 transition-all uppercase text-xs">Cancelar</button>
                  <button type="submit" className="flex-1 p-4 bg-[#F37125] text-white rounded-xl font-bold shadow-lg hover:bg-[#e0611d] transition-all uppercase text-xs">Salvar Registro</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}