import React, { useState, useEffect } from 'react';
import { AppState, WritingCorrectionInput } from './types';
// IMPORTAMOS TU NUEVO MÓDULO
import { Welcome } from './components/Welcome';
// Importamos iconos para el resto de la app
import { BookOpen, ChevronLeft, Send, Loader2, Award, Target, Rocket } from 'lucide-react';

const App: React.FC = () => {
  // Estados de la aplicación
  const [state, setState] = useState<AppState>(AppState.WELCOME);
  const [loading, setLoading] = useState(false);
  const [userStats, setUserStats] = useState({ logueado: false, restantes: 0 });
  const [writingInput, setWritingInput] = useState<WritingCorrectionInput>({
    writing: '',
    materia: 'higiene'
  });
  const [resultado, setResultado] = useState<any>(null);

  // Cargar datos del backend (app.py)
  useEffect(() => {
    fetch('/api/usuario')
      .then(res => res.json())
      .then(data => setUserStats(data))
      .catch(err => console.error("Error al cargar usuario:", err));
  }, []);

  // Función para enviar a corregir
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
        alert(data.error || "Error en la evaluación");
      }
    } catch (error) {
      alert("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      
      {/* HEADER SIMPLE (Se mantiene siempre) */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold">
            <BookOpen size={18} />
          </div>
          <h1 className="font-black text-slate-800 text-lg tracking-tighter">MENTOR IA</h1>
        </div>
        
        {state !== AppState.WELCOME && (
          <button 
            onClick={() => { setResultado(null); setState(AppState.WELCOME); }}
            className="flex items-center gap-1 text-slate-500 hover:text-indigo-600 transition-colors text-sm font-bold"
          >
            <ChevronLeft size={18} /> Volver
          </button>
        )}
      </header>

      <main className="flex-1 flex flex-col w-full max-w-5xl mx-auto p-6">
        
        {/* MÓDULO 1: BIENVENIDA (Llamamos a tu nuevo archivo) */}
        {state === AppState.WELCOME && (
          <Welcome 
            onStart={() => setState(AppState.WRITING_CORRECTION_INPUT)}
            onViewHistory={() => alert("Historial próximamente")}
            onViewCognitiveMap={() => alert("Mapa Cognitivo próximamente")}
            restantes={userStats.restantes}
          />
        )}

        {/* MÓDULO 2: EDITOR DE TRABAJO (Aparece al dar 'Comenzar') */}
        {state === AppState.WRITING_CORRECTION_INPUT && !resultado && (
          <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col flex-1">
              <label className="text-sm font-black text-slate-400 uppercase tracking-widest mb-2">Área de Entrenamiento</label>
              <textarea 
                className="flex-1 w-full p-8 text-xl border-2 border-slate-200 rounded-[2.5rem] focus:border-indigo-500 focus:ring-8 focus:ring-indigo-50 outline-none shadow-inner bg-white resize-none transition-all"
                placeholder="Pega tu informe o respuesta técnica aquí..."
                value={writingInput.writing}
                onChange={(e) => setWritingInput({...writingInput, writing: e.target.value})}
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4">
              <select 
                className="bg-white border-2 border-slate-200 rounded-2xl px-6 py-4 font-bold text-slate-700 outline-none focus:border-indigo-600 shadow-sm"
                value={writingInput.materia}
                onChange={(e) => setWritingInput({...writingInput, materia: e.target.value})}
              >
                <option value="higiene">Higiene y Seguridad</option>
                <option value="politica">Ciencia Política</option>
                <option value="alfabetizacion">Alfabetización Académica</option>
              </select>
              
              <button 
                onClick={handleEnviar}
                disabled={loading || !writingInput.writing}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white px-10 py-4 rounded-2xl font-black transition-all shadow-xl flex items-center gap-2"
              >
                {loading ? <Loader2 className="animate-spin" /> : <Send size={20} />}
                {loading ? "ANALIZANDO..." : "ENVIAR A MENTOR"}
              </button>
            </div>
          </div>
        )}

        {/* MÓDULO 3: RESULTADOS (Se muestra tras la respuesta de la IA) */}
        {resultado && (
          <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
            <div className="bg-indigo-600 p-8 text-white flex justify-between items-center">
              <div>
                <h3 className="text-3xl font-black tracking-tighter">Evaluación Final</h3>
                <p className="opacity-80 font-bold text-xs uppercase tracking-widest">Materia: {writingInput.materia}</p>
              </div>
              <div className="text-center bg-white/20 p-4 rounded-2xl backdrop-blur-md min-w-[100px] border border-white/20">
                <span className="block text-4xl font-black leading-none">{resultado.grade}</span>
                <span className="text-[10px] uppercase font-bold tracking-tighter">Nota Final</span>
              </div>
            </div>
            
            <div className="p-8 space-y-6 overflow-y-auto max-h-[60vh]">
              <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                <h4 className="flex items-center gap-2 font-black text-slate-800 mb-3 uppercase text-xs tracking-widest">
                  <Award className="text-indigo-500" size={18}/> Análisis de Desempeño
                </h4>
                <p className="text-slate-600 leading-relaxed font-medium">{resultado.performanceAnalysis}</p>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-100">
                  <h5 className="font-black text-emerald-700 text-xs uppercase tracking-widest mb-3">Fortalezas</h5>
                  <ul className="space-y-2">
                    {resultado.strengths?.map((s: string, i: number) => (
                      <li key={i} className="text-sm text-emerald-800 flex gap-2 font-medium">
                        <span className="text-emerald-500">•</span> {s}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-amber-50 p-6 rounded-2xl border border-amber-100">
                  <h5 className="font-black text-amber-700 text-xs uppercase tracking-widest mb-3">A mejorar</h5>
                  <ul className="space-y-2">
                    {resultado.weaknesses?.map((w: string, i: number) => (
                      <li key={i} className="text-sm text-amber-800 flex gap-2 font-medium">
                        <span className="text-amber-500">•</span> {w}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
