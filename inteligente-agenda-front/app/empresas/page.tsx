"use client";

import { useState, useEffect } from "react";
import { getCookie, deleteCookie } from "cookies-next";
import { useRouter } from "next/navigation";

export default function EmpresaDashboard() {
  const router = useRouter();
  const salaoId = getCookie("salao_id");
  const nomeUsuario = getCookie("user_nome");

  const abas = [
    { id: "meu_perfil", nome: "Gerenciar Salão", icone: "⚙️" },
    { id: "agendamentos", nome: "Agenda", icone: "📅" },
    { id: "profissionais", nome: "Equipe", icone: "✂️" },
    { id: "servicos", nome: "Serviços", icone: "🛠️" },
    { id: "horarios_funcionamento", nome: "Horários", icone: "⏰" },
    { id: "usuarios", nome: "Acessos", icone: "👥" }
  ];

  const [abaAtiva, setAbaAtiva] = useState("agendamentos");
  const [dados, setDados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editId, setEditId] = useState<any>(null);
  const [formData, setFormData] = useState<any>({});

  const carregarDados = async () => {
    setLoading(true);
    try {
      const endpoint = abaAtiva === "meu_perfil" ? "empresas" : abaAtiva;
      const res = await fetch(`http://localhost:8000/admin/${endpoint}`);
      
      if (res.ok) {
        let json = await res.json();
        
        // Filtro por ID do Salão
        json = json.filter((item: any) => {
            const idVinculo = item.empresa_id || item.id_empresas || item.id;
            return String(idVinculo) === String(salaoId);
        });

        // Filtro exclusivo para a aba Agenda (Somente próximos de hoje)
        if (abaAtiva === "agendamentos") {
          const agora = new Date();
          const fimDoDia = new Date();
          fimDoDia.setHours(23, 59, 59, 999);

          json = json.filter((item: any) => {
            const dataInicio = new Date(item.data_hora_inicio);
            return dataInicio >= agora && dataInicio <= fimDoDia;
          });

          json.sort((a: any, b: any) => 
            new Date(a.data_hora_inicio).getTime() - new Date(b.data_hora_inicio).getTime()
          );
        }
        
        setDados(json);
      }
    } catch (err) {
      console.error("Erro:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { carregarDados(); }, [abaAtiva]);

  const handleSalvar = async (e: React.FormEvent) => {
    e.preventDefault();
    const isEditing = !!editId;
    const endpoint = abaAtiva === "meu_perfil" ? "empresas" : abaAtiva;
    const url = `http://localhost:8000/admin/${endpoint}${isEditing ? `/${editId}` : ""}`;
    
    const payload = { ...formData };
    if (!isEditing && abaAtiva !== "meu_perfil") {
        if (abaAtiva === "usuarios") payload.id_empresas = parseInt(String(salaoId));
        else payload.empresa_id = parseInt(String(salaoId));
    }

    try {
      const res = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setIsModalOpen(false);
        setEditId(null);
        setFormData({});
        carregarDados();
        alert("Salvo com sucesso!");
      }
    } catch (err) {
      alert("Erro ao salvar.");
    }
  };

  const abrirModalEdicao = (item: any) => {
    setEditId(item.id);
    const formDataTratado = { ...item };
    if (formDataTratado.data_hora_inicio) formDataTratado.data_hora_inicio = formDataTratado.data_hora_inicio.slice(0, 16);
    if (formDataTratado.data_hora_fim) formDataTratado.data_hora_fim = formDataTratado.data_hora_fim.slice(0, 16);
    setFormData(formDataTratado);
    setIsModalOpen(true);
  };

  const handleLogout = () => {
    deleteCookie("auth_token");
    deleteCookie("salao_id");
    router.push("/login");
  };

  return (
    <div className="flex min-h-screen bg-gray-50 font-sans">
      <aside className="w-64 bg-[#0F2639] text-white p-6 flex flex-col shadow-xl">
        <div className="mb-10 text-center">
          <h2 className="text-[#F37125] font-black uppercase tracking-tighter text-xl">Painel Empresa</h2>
          <p className="text-[10px] text-gray-400">Olá, {nomeUsuario}</p>
        </div>

        <nav className="space-y-2 flex-1">
          {abas.map((aba) => (
            <button 
              key={aba.id}
              onClick={() => setAbaAtiva(aba.id)} 
              className={`w-full text-left p-3 rounded-lg text-sm transition-all ${abaAtiva === aba.id ? 'bg-[#F37125] font-bold shadow-lg' : 'hover:bg-gray-800 text-gray-300'}`}
            >
              <span className="mr-2">{aba.icone}</span> {aba.nome}
            </button>
          ))}
        </nav>

        <button onClick={handleLogout} className="mt-auto border border-red-500/30 text-red-400 p-3 rounded-lg hover:bg-red-500 hover:text-white transition-all text-xs font-bold uppercase">
          Sair
        </button>
      </aside>

      <main className="flex-1 p-10 overflow-y-auto h-screen">
        <div className="flex justify-between items-center mb-10">
          <h1 className="text-3xl font-black text-gray-800 uppercase tracking-tighter">
            {abas.find(a => a.id === abaAtiva)?.nome}
          </h1>
          {abaAtiva !== "meu_perfil" && (
            <button 
              onClick={() => { setEditId(null); setFormData({}); setIsModalOpen(true); }}
              className="bg-[#F37125] text-white px-6 py-2 rounded-xl font-bold shadow-lg uppercase text-xs"
            >
              + Adicionar
            </button>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-10 text-center text-gray-400 font-bold uppercase">Carregando...</div>
          ) : (
            <table className="w-full text-left">
              <thead className="bg-gray-50 border-b text-gray-400 text-[10px] font-black uppercase">
                <tr>
                  <th className="p-5">{abaAtiva === "agendamentos" ? "Nome do Cliente" : "Informação"}</th>
                  {abaAtiva === "agendamentos" && (
                    <>
                      <th className="p-5">Horário</th>
                      <th className="p-5">Profissional</th>
                      <th className="p-5">Serviço</th>
                      <th className="p-5">Valor</th>
                      <th className="p-5">Duração</th>
                    </>
                  )}
                  <th className="p-5">Status/Detalhe</th>
                  <th className="p-5 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 text-sm">
                {dados.length > 0 ? dados.map((item: any) => (
                  <tr key={item.id} className="hover:bg-blue-50/30 transition-colors">
                    <td className="p-5 font-bold text-gray-700">
                      {item.nome_cliente || item.nome_empresa || item.nome || item.usuario}
                    </td>
                    {abaAtiva === "agendamentos" && (
                      <>
                        <td className="p-5 font-mono text-[#F37125] font-bold">
                          {new Date(item.data_hora_inicio).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td className="p-5 text-gray-600">{item.profissionais?.nome || "N/A"}</td>
                        <td className="p-5 text-gray-600 font-bold">{item.servicos?.nome || "N/A"}</td>
                        <td className="p-5 text-green-600 font-bold">R$ {item.servicos?.preco || "0,00"}</td>
                        <td className="p-5 text-gray-400 text-xs">{item.servicos?.duracao_minutos || "30"} min</td>
                      </>
                    )}
                    <td className="p-5">
                      <span className="bg-gray-100 text-[10px] px-2 py-1 rounded font-black uppercase text-gray-500">
                        {item.status || (item.ativo ? "Ativo" : "Inativo") || "Configurado"}
                      </span>
                    </td>
                    <td className="p-5 text-right">
                      <button onClick={() => abrirModalEdicao(item)} className="text-[#F37125] font-bold text-xs hover:underline">EDITAR</button>
                    </td>
                  </tr>
                )) : (
                  <tr><td colSpan={abaAtiva === "agendamentos" ? 7 : 4} className="p-10 text-center text-gray-400 italic">Nenhum registro encontrado.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* MODAL DE EDIÇÃO */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-3xl p-8 w-full max-w-2xl shadow-2xl overflow-y-auto max-h-[90vh]">
              <h2 className="text-2xl font-bold mb-6 text-gray-800 uppercase">
                {editId ? "Editar" : "Novo"} {abas.find(a => a.id === abaAtiva)?.nome}
              </h2>
              
              <form onSubmit={handleSalvar} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* MANTIDOS OS CAMPOS DA ÚLTIMA VERSÃO APROVADA[cite: 3] */}
                {abaAtiva === "meu_perfil" && (
                  <>
                    <div className="flex flex-col gap-1 md:col-span-2">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome da Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome_empresa || ""} onChange={e => setFormData({...formData, nome_empresa: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">WhatsApp Número</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.whatsapp_numero || ""} onChange={e => setFormData({...formData, whatsapp_numero: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Segmento</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.segmento || ""} onChange={e => setFormData({...formData, segmento: e.target.value})} />
                    </div>
                    <div className="flex items-center gap-2 mt-4 md:col-span-2 bg-gray-50 p-4 rounded-xl border">
                      <input type="checkbox" id="verificar_cliente" checked={formData.verificar_cliente || false} onChange={e => setFormData({...formData, verificar_cliente: e.target.checked})} className="w-5 h-5 accent-[#F37125]" />
                      <label htmlFor="verificar_cliente" className="text-xs font-bold text-gray-600 uppercase cursor-pointer">Verificar cliente antes de agendar?</label>
                    </div>
                  </>
                )}

                {abaAtiva === "agendamentos" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome do Cliente</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome_cliente || ""} onChange={e => setFormData({...formData, nome_cliente: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">WhatsApp</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.cliente_contato || ""} onChange={e => setFormData({...formData, cliente_contato: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Início</label>
                      <input type="datetime-local" className="p-3 bg-gray-50 border rounded-xl" value={formData.data_hora_inicio || ""} onChange={e => setFormData({...formData, data_hora_inicio: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Fim</label>
                      <input type="datetime-local" className="p-3 bg-gray-50 border rounded-xl" value={formData.data_hora_fim || ""} onChange={e => setFormData({...formData, data_hora_fim: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Status</label>
                      <select className="p-3 bg-gray-50 border rounded-xl" value={formData.status || "pendente"} onChange={e => setFormData({...formData, status: e.target.value})}>
                        <option value="pendente">Pendente</option>
                        <option value="confirmado">Confirmado</option>
                        <option value="cancelado">Cancelado</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Profissional</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.profissional_id || ""} onChange={e => setFormData({...formData, profissional_id: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Serviço</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.servico_id || ""} onChange={e => setFormData({...formData, servico_id: parseInt(e.target.value)})} required />
                    </div>
                  </>
                )}

                {abaAtiva === "profissionais" && (
                  <div className="flex flex-col gap-1 md:col-span-2">
                    <label className="text-[10px] font-bold text-gray-400 uppercase">Nome</label>
                    <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome || ""} onChange={e => setFormData({...formData, nome: e.target.value})} required />
                  </div>
                )}

                <div className="md:col-span-2 flex gap-3 mt-6">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 p-4 bg-gray-100 text-gray-500 rounded-xl font-bold uppercase text-xs">Cancelar</button>
                  <button type="submit" className="flex-1 p-4 bg-[#F37125] text-white rounded-xl font-bold uppercase text-xs">Salvar</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}