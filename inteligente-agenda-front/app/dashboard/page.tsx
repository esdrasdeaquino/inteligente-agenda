"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { deleteCookie } from "cookies-next";

export default function AdminDashboard() {
  const router = useRouter();
  
  // Incluídas todas as 10 tabelas
  const abas = [
    { id: "empresas", nome: "Empresas", icone: "🏢" },
    { id: "usuarios", nome: "Usuários", icone: "👥" },
    { id: "profissionais", nome: "Profissionais", icone: "✂️" },
    { id: "servicos", nome: "Serviços", icone: "🛠️" },
    { id: "agendamentos", nome: "Agendamentos", icone: "📅" },
    { id: "horarios_funcionamento", nome: "Horários Func.", icone: "⏰" },
    { id: "disponibilidades_empresa_excecao", nome: "Exc. Empresa", icone: "🚫" },
    { id: "disponibilidades_excecao", nome: "Exc. Profissional", icone: "🚫" },
    { id: "servicos_profissionais", nome: "Vínculo Serv/Prof", icone: "🔗" },
    { id: "historico_mensagens", nome: "Histórico Msgs", icone: "💬" }
  ];

  const [abaAtiva, setAbaAtiva] = useState("empresas");
  const [dados, setDados] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editId, setEditId] = useState<any>(null);
  const [termoBusca, setTermoBusca] = useState("");
  const [formData, setFormData] = useState<any>({});

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
    setTermoBusca("");
  }, [abaAtiva]);

  // Filtro genérico robusto para procurar em vários campos possíveis
  const dadosFiltrados = dados.filter((item: any) => {
    const busca = termoBusca.toLowerCase();
    const textoItem = JSON.stringify(item).toLowerCase();
    return textoItem.includes(busca);
  });

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
      } else {
        const erro = await res.json();
        alert(`Erro: ${JSON.stringify(erro.detail)}`);
      }
    } catch (err) {
      alert("Erro ao salvar dados.");
    }
  };

  const abrirModalEdicao = (item: any) => {
    setEditId(item.id);
    
    // Converte datas para o formato esperado pelo input type="datetime-local" se existirem
    const formDataTratado = { ...item };
    if (formDataTratado.data_hora_inicio) formDataTratado.data_hora_inicio = formDataTratado.data_hora_inicio.slice(0, 16);
    if (formDataTratado.data_hora_fim) formDataTratado.data_hora_fim = formDataTratado.data_hora_fim.slice(0, 16);
    if (formDataTratado.data_inicio) formDataTratado.data_inicio = formDataTratado.data_inicio.slice(0, 16);
    if (formDataTratado.data_fim) formDataTratado.data_fim = formDataTratado.data_fim.slice(0, 16);

    setFormData(formDataTratado);
    setIsModalOpen(true);
  };

  const fecharModal = () => {
    setIsModalOpen(false);
    setEditId(null);
    setFormData({});
  };

  const deletarItem = async (id: any) => {
    if (confirm("Deseja realmente remover este registro?")) {
      try {
        const res = await fetch(`http://localhost:8000/admin/${abaAtiva}/${id}`, { method: "DELETE" });
        if (res.ok) carregarDados(abaAtiva);
      } catch (err) {
        alert("Erro ao remover.");
      }
    }
  };

  const handleLogout = () => {
    deleteCookie('auth_token');
    router.push('/');
  };

  // Função para renderizar detalhes básicos baseados na tabela
  const renderResumo = (item: any) => {
    if (item.nome_empresa) return item.nome_empresa;
    if (item.nome_cliente) return `${item.nome_cliente} (${item.status})`;
    if (item.usuario) return item.usuario;
    if (item.nome) return item.nome;
    if (item.dia_semana !== undefined) return `Dia: ${item.dia_semana} (${item.horario_abertura} às ${item.horario_fechamento})`;
    if (item.whatsapp_cliente) return `Msg: ${item.whatsapp_cliente} (${item.role})`;
    if (item.motivo) return `Exceção: ${item.motivo}`;
    return "Registro ID: " + item.id;
  };

  return (
    <div className="flex min-h-screen bg-gray-100 font-sans">
      <aside className="w-64 bg-[#0F2639] text-white p-6 flex flex-col shadow-xl overflow-y-auto">
        <div className="mb-10 text-center">
          <h2 className="text-xl font-bold text-[#F37125] uppercase tracking-tighter">Painel Admin</h2>
          <p className="text-[10px] text-gray-400">INTELIGENTE AGENDA</p>
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
        <button onClick={handleLogout} className="mt-8 border border-red-500/50 text-red-400 p-3 rounded-lg hover:bg-red-500 hover:text-white transition-all text-xs font-bold uppercase">
          Sair do Sistema
        </button>
      </aside>

      <main className="flex-1 p-10 h-screen overflow-y-auto">
        <div className="flex justify-between items-end mb-10">
          <div>
            <h1 className="text-3xl font-black text-gray-800 uppercase tracking-tighter">Gestão de {abaAtiva.replace(/_/g, ' ')}</h1>
          </div>
          <div className="flex gap-4">
            <input 
              type="text" 
              placeholder="Buscar em todos os campos..." 
              value={termoBusca}
              onChange={(e) => setTermoBusca(e.target.value)}
              className="pl-4 pr-4 py-3 bg-white border border-gray-200 rounded-xl w-72 shadow-sm focus:ring-2 focus:ring-[#F37125] outline-none text-sm"
            />
            <button onClick={() => setIsModalOpen(true)} className="bg-[#F37125] text-white px-8 py-3 rounded-xl font-bold shadow-lg hover:scale-105 transition-all uppercase text-xs">
              + Adicionar Novo
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b text-gray-400 text-[10px] font-black uppercase tracking-widest">
              <tr>
                <th className="p-5 w-32">ID</th>
                <th className="p-5">Empresa/Relacionamento</th>
                <th className="p-5">Resumo do Registro</th>
                <th className="p-5 text-right w-48">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr><td colSpan={4} className="p-10 text-center text-gray-400">Carregando...</td></tr>
              ) : dadosFiltrados.map((item: any) => (
                <tr key={item.id} className="hover:bg-blue-50/30 transition-colors">
                  <td className="p-5 text-gray-300 font-mono text-xs">#{String(item.id).slice(0, 8)}</td>
                  <td className="p-5 text-xs text-gray-500">
                    {item.empresas?.nome_empresa || item.empresa_id || "Geral/Mestre"}
                  </td>
                  <td className="p-5 font-bold text-gray-700 text-sm">
                    {renderResumo(item)}
                  </td>
                  <td className="p-5 text-right space-x-3">
                    <button onClick={() => abrirModalEdicao(item)} className="text-blue-500 hover:text-blue-700 font-bold text-xs">EDITAR</button>
                    <button onClick={() => deletarItem(item.id)} className="text-red-400 hover:text-red-600 font-bold text-xs">REMOVER</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* MODAL DE CADASTRO / EDIÇÃO */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-3xl p-8 w-full max-w-4xl shadow-2xl overflow-y-auto max-h-[90vh]">
              <h2 className="text-2xl font-bold mb-6 text-gray-800 uppercase">{editId ? "Editar" : "Novo"} {abaAtiva.replace(/_/g, ' ')}</h2>
              
              <form onSubmit={handleSalvar} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {abaAtiva === "empresas" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome da Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome_empresa || ""} onChange={e => setFormData({...formData, nome_empresa: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">WhatsApp Sistema</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.whatsapp_numero || ""} onChange={e => setFormData({...formData, whatsapp_numero: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">WhatsApp Dono</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.whatsapp_dono || ""} onChange={e => setFormData({...formData, whatsapp_dono: e.target.value})} />
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
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Status</label>
                      <select className="p-3 bg-gray-50 border rounded-xl" value={formData.status || "ativo"} onChange={e => setFormData({...formData, status: e.target.value})}>
                        <option value="ativo">Ativo</option>
                        <option value="trial">Trial</option>
                        <option value="inativo">Inativo</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Segmento</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.segmento || "Salão"} onChange={e => setFormData({...formData, segmento: e.target.value})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Instância API</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.instancia || ""} onChange={e => setFormData({...formData, instancia: e.target.value})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome da IA</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.ia_nome || ""} onChange={e => setFormData({...formData, ia_nome: e.target.value})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Estilo da IA</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.ia_estilo || ""} onChange={e => setFormData({...formData, ia_estilo: e.target.value})} />
                    </div>
                    <div className="flex items-center gap-2 mt-4 md:col-span-2 bg-gray-50 p-4 rounded-xl border">
                      <input type="checkbox" id="verificar_cliente" checked={formData.verificar_cliente || false} onChange={e => setFormData({...formData, verificar_cliente: e.target.checked})} className="w-5 h-5 accent-[#F37125]" />
                      <label htmlFor="verificar_cliente" className="text-sm font-bold text-gray-600 cursor-pointer">Verificar cliente antes de agendar?</label>
                    </div>
                  </>
                )}

                {abaAtiva === "usuarios" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome || ""} onChange={e => setFormData({...formData, nome: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Usuário (Login)</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.usuario || ""} onChange={e => setFormData({...formData, usuario: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Senha</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="password" onChange={e => setFormData({...formData, senha: e.target.value})} required={!editId} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.id_empresas || ""} onChange={e => setFormData({...formData, id_empresas: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Perfil</label>
                      <select className="p-3 bg-gray-50 border rounded-xl" value={formData.perfil || "user"} onChange={e => setFormData({...formData, perfil: e.target.value})}>
                        <option value="user">Usuário</option>
                        <option value="admin">Administrador</option>
                      </select>
                    </div>
                  </>
                )}

                {abaAtiva === "profissionais" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome do Profissional</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome || ""} onChange={e => setFormData({...formData, nome: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex items-center gap-2 mt-4 bg-gray-50 p-4 rounded-xl border">
                      <input type="checkbox" id="ativo" checked={formData.ativo !== false} onChange={e => setFormData({...formData, ativo: e.target.checked})} className="w-5 h-5 accent-[#F37125]" />
                      <label htmlFor="ativo" className="text-sm font-bold text-gray-600 cursor-pointer">Profissional Ativo?</label>
                    </div>
                  </>
                )}

                {abaAtiva === "servicos" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Nome do Serviço</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.nome || ""} onChange={e => setFormData({...formData, nome: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Preço (Ex: 45.00)</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="text" value={formData.preco || ""} onChange={e => setFormData({...formData, preco: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Duração (Minutos)</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.duracao_minutos || ""} onChange={e => setFormData({...formData, duracao_minutos: parseInt(e.target.value)})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: parseInt(e.target.value)})} required />
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
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Contato (WhatsApp)</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.cliente_contato || ""} onChange={e => setFormData({...formData, cliente_contato: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Data e Hora Inicial</label>
                      <input type="datetime-local" className="p-3 bg-gray-50 border rounded-xl" value={formData.data_hora_inicio || ""} onChange={e => setFormData({...formData, data_hora_inicio: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Data e Hora Final</label>
                      <input type="datetime-local" className="p-3 bg-gray-50 border rounded-xl" value={formData.data_hora_fim || ""} onChange={e => setFormData({...formData, data_hora_fim: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Status</label>
                      <select className="p-3 bg-gray-50 border rounded-xl" value={formData.status || "pendente"} onChange={e => setFormData({...formData, status: e.target.value})}>
                        <option value="pendente">Pendente</option>
                        <option value="confirmado">Confirmado</option>
                        <option value="cancelado">Cancelado</option>
                        <option value="concluido">Concluído</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: parseInt(e.target.value)})} required />
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

                {abaAtiva === "horarios_funcionamento" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Dia da Semana (0-Dom a 6-Sab)</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" min="0" max="6" value={formData.dia_semana ?? ""} onChange={e => setFormData({...formData, dia_semana: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Abertura</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="time" value={formData.horario_abertura || ""} onChange={e => setFormData({...formData, horario_abertura: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Fechamento</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="time" value={formData.horario_fechamento || ""} onChange={e => setFormData({...formData, horario_fechamento: e.target.value})} required />
                    </div>
                  </>
                )}

                {abaAtiva === "disponibilidades_empresa_excecao" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Motivo</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.motivo || ""} onChange={e => setFormData({...formData, motivo: e.target.value})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Data e Hora Inicial</label>
                      <input type="datetime-local" className="p-3 bg-gray-50 border rounded-xl" value={formData.data_inicio || ""} onChange={e => setFormData({...formData, data_inicio: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Data e Hora Final</label>
                      <input type="datetime-local" className="p-3 bg-gray-50 border rounded-xl" value={formData.data_fim || ""} onChange={e => setFormData({...formData, data_fim: e.target.value})} required />
                    </div>
                  </>
                )}

                {abaAtiva === "disponibilidades_excecao" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Profissional</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.profissional_id || ""} onChange={e => setFormData({...formData, profissional_id: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Motivo</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.motivo || ""} onChange={e => setFormData({...formData, motivo: e.target.value})} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Data e Hora Inicial</label>
                      <input type="datetime-local" className="p-3 bg-gray-50 border rounded-xl" value={formData.data_inicio || ""} onChange={e => setFormData({...formData, data_inicio: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Data e Hora Final</label>
                      <input type="datetime-local" className="p-3 bg-gray-50 border rounded-xl" value={formData.data_fim || ""} onChange={e => setFormData({...formData, data_fim: e.target.value})} required />
                    </div>
                  </>
                )}

                {abaAtiva === "servicos_profissionais" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Profissional</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.profissional_id || ""} onChange={e => setFormData({...formData, profissional_id: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Serviço</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.servico_id || ""} onChange={e => setFormData({...formData, servico_id: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: parseInt(e.target.value)})} required />
                    </div>
                  </>
                )}

                {abaAtiva === "historico_mensagens" && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">ID Empresa</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" type="number" value={formData.empresa_id || ""} onChange={e => setFormData({...formData, empresa_id: parseInt(e.target.value)})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">WhatsApp Cliente</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.whatsapp_cliente || ""} onChange={e => setFormData({...formData, whatsapp_cliente: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Role (user, assistant, system)</label>
                      <input className="p-3 bg-gray-50 border rounded-xl" value={formData.role || ""} onChange={e => setFormData({...formData, role: e.target.value})} required />
                    </div>
                    <div className="flex flex-col gap-1 md:col-span-2">
                      <label className="text-[10px] font-bold text-gray-400 uppercase">Conteúdo (Content)</label>
                      <textarea className="p-3 bg-gray-50 border rounded-xl h-24" value={formData.content || ""} onChange={e => setFormData({...formData, content: e.target.value})} required />
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