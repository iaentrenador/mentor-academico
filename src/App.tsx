import React, { useState, useEffect } from 'react';
import { AppState, WritingCorrectionInput } from './types';
import { PenTool, ChevronLeft, Send, Loader2, Award, AlertCircle } from 'lucide-react';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>(AppState.WELCOME);
  const [loading, setLoading] = useState(false);
  const [userStats, setUserStats] = useState({ logueado: false, restantes: 0 });
  const [writingInput, setWritingInput] = useState<WritingCorrectionInput>({
    writing: '',
    materia: 'higiene'
  });
  const [resultado, setResultado] = useState<any>(null);

  // 1. Cargar info del usuario al iniciar (Créditos del app.py)
  useEffect(() => {
    fetch('/api/usuario')
      .then(res => res.json())
      .then(data => setUserStats(data))
      .catch(err => console.error("Error cargando usuario:", err));
  }, []);

  const goBack = () => {
    setResultado(null);
    setState(AppState.WELCOME);
  };

  // 2. Función para enviar el escrito al backend
  const handleEnviar = async () => {
    if (!writingInput.writing.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/corregir_escrito', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(writingInput)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setResultado(data.resultado);
        setUserStats(prev => ({ ...prev, restantes: data.restantes }));
      } else {
        alert(data.error || "Error en la consulta");
      }
    } catch (error) {
      alert("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      {/* HEADER */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded flex items-center justify-center text-white font-bold">M</div>
          <h1 className="font-bold text-slate-800 text-lg tracking-tight">Mentor IA</h1>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-xs font-semibold bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full border border-indigo-100">
            Consultas: {userStats.restantes}
          </span>
          {state !== AppState.WELCOME && (
            <button onClick={goBack} className="flex items-center gap-1 text-slate-500 hover:text-indigo-600 transition-colors text-sm font-medium">
              <ChevronLeft size={18} /> Volver
            </button>
          )}
        </div>
      </header>

      <main className="flex-1 flex flex-col w-full max-w-5xl mx-auto p-6 overflow-hidden">
        
        {/* PANTALLA 1: BIENVENIDA */}
        {state === AppState.WELCOME && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in duration-500">
            <div className="col-span-full mb-4">
              <h2 className="text-3xl font-extrabold text-slate-800">¿Qué entrenamos hoy, Seba?</h2>
              <p className="text-slate-500">Tu entrenador con IA para Higiene, Seguridad y Política.</p>
            </div>
            
            <button 
              onClick={() => setState(AppState.WRITING_CORRECTION_INPUT)}
              className="bg-white p-8 rounded-2xl border-2 border-transparent hover:border-indigo-500 shadow-sm hover:shadow-xl transition-all text-left group"
            >
              <div className="w-14 h-14 bg-indigo-50 rounded-xl flex items-center justify-center text-indigo-600 mb-4 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <PenTool size={28} />
              </div>
              <h3 className="font-bold text-slate-800 text-xl">Corrección de Escritos</h3>
              <p className="text-slate-500 mt-2">Evaluación técnica de informes y parciales con rigor legal.</p>
            </button>
          </div>
        )}

        {/* PANTALLA 2: INPUT Y RESULTADO */}
        {state === AppState.WRITING_CORRECTION_INPUT && (
          <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-bottom-4 duration-500">
            {!resultado ? (
              <>
                <div className="flex flex-col flex-1">
                  <label className="block text-sm font-bold text-slate-700 mb-2">Área de Redacción Académica</label>
                  <textarea 
                    className="flex-1 w-full p-6 text-lg border-2 border-slate-200 rounded-3xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50/50 outline-none shadow-inner bg-white resize-none transition-all"
                    placeholder="Pega tu informe o respuesta aquí..."
                    value={writingInput.writing}
                    onChange={(e) => setWritingInput({...writingInput, writing: e.target.value})}
                  />
                </div>

                <div className="flex flex-wrap items-center justify-end gap-4">
                  <select 
                    className="bg-white border-2 border-slate-200 rounded-xl px-4 py-3 text-sm font-bold outline-none focus:border-indigo-500"
                    value={writingInput.materia}
                    onChange={(e) => setWritingInput({...writingInput, materia: e.target.value})}
                  >
                    <option value="higiene">Higiene y Seguridad</option>
                    <option value="politica">Ciencia Política</option>
                    <option value="alfabetizacion">Alfabetización Académica</option>
                    <option value="abogacia">Derecho (UNLZ)</option>
                  </select>
                  
                  <button 
                    onClick={handleEnviar}
                    disabled={loading || !writingInput.writing}
                    className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white px-10 py-3 rounded-xl font-bold transition-all shadow-lg flex items-center gap-2"
                  >
                    {loading ? <Loader2 className="animate-spin" /> : <Send size={20} />}
                    {loading ? "Evaluando..." : "Enviar a Evaluación"}
                  </button>
                </div>
              </>
            ) : (
              /* VISTA DE RESULTADOS (Lo que devuelve la IA) */
              <div className="bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
                <div className="bg-indigo-600 p-6 text-white flex justify-between items-center">
                  <div>
                    <h3 className="text-2xl font-bold">Evaluación Finalizada</h3>
                    <p className="opacity-80 text-sm italic">Perfil: {writingInput.materia.toUpperCase()}</p>
                  </div>
                  <div className="text-center bg-white/20 p-3 rounded-2xl backdrop-blur-md min-w-[80px]">
                    <span className="block text-3xl font-black">{resultado.grade}</span>
                    <span className="text-[10px] uppercase font-bold">Nota</span>
                  </div>
                </div>
                
                <div className="p-8 space-y-6 overflow-y-auto max-h-[60vh]">
                  <section>
                    <h4 className="flex items-center gap-2 font-bold text-slate-800 mb-2"><Award className="text-indigo-500" size={20}/> Análisis del Desempeño</h4>
                    <p className="text-slate-600 leading-relaxed">{resultado.performanceAnalysis}</p>
                  </section>

                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-emerald-50 p-4 rounded-2xl border border-emerald-100">
                      <h5 className="font-bold text-emerald-700 text-sm mb-2">Fortalezas</h5>
                      <ul className="list-disc list-inside text-sm text-emerald-800 space-y-1">
                        {resultado.strengths?.map((s: string, i: number) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                    <div className="bg-amber-50 p-4 rounded-2xl border border-amber-100">
                      <h5 className="font-bold text-amber-700 text-sm mb-2">Aspectos a mejorar</h5>
                      <ul className="list-disc list-inside text-sm text-amber-800 space-y-1">
                        {resultado.weaknesses?.map((w: string, i: number) => <li key={i}>{w}</li>)}
                      </ul>
                    </div>
                  </div>

                  <section className="bg-slate-50 p-5 rounded-2xl border border-slate-200">
                    <h4 className="font-bold text-slate-800 mb-2">Versión Mejorada Sugerida</h4>
                    <p className="text-slate-600 text-sm whitespace-pre-wrap italic">"{resultado.improvedVersion}"</p>
                  </section>
                </div>

                <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-center">
                  <button onClick={goBack} className="text-indigo-600 font-bold hover:underline">Intentar con otro texto</button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
      
