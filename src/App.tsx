import React, { useState, useEffect } from 'react';
import { AppState, WritingCorrectionInput, HistoryEntry, CognitiveMapData } from './types';
import { Welcome } from './components/Welcome';
// Nota: Deberás crear estos componentes luego, por ahora los preparamos en el switch
import { BookOpen, ChevronLeft, Send, Loader2, Award } from 'lucide-react';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>(AppState.WELCOME);
  const [loading, setLoading] = useState(false);
  const [userStats, setUserStats] = useState({ logueado: false, restantes: 0 });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [writingInput, setWritingInput] = useState<WritingCorrectionInput>({
    writing: '',
    materia: 'higiene'
  });
  const [resultado, setResultado] = useState<any>(null);

  // 1. Cargar datos del backend y del Historial Local (ADN IA Studio)
  useEffect(() => {
    // Backend
    fetch('/api/usuario')
      .then(res => res.json())
      .then(data => setUserStats(data))
      .catch(err => console.error("Error al cargar usuario:", err));

    // Historial Local
    const savedHistory = localStorage.getItem('academic_history');
    if (savedHistory) {
      try { setHistory(JSON.parse(savedHistory)); } 
      catch (e) { console.error('Error loading history', e); }
    }
  }, []);

  // 2. Función para guardar en historial (ADN IA Studio)
  const saveToHistory = (type: string, title: string, data: any, score?: number) => {
    const newEntry: HistoryEntry = {
      id: crypto.randomUUID(),
      date: new Date().toISOString(),
      type,
      title,
      data,
      score
    };
    const updatedHistory = [newEntry, ...history];
    setHistory(updatedHistory);
    localStorage.setItem('academic_history', JSON.stringify(updatedHistory));
  };

  // 3. Lógica del Mapa Cognitivo (ADN IA Studio)
  const getCognitiveMapData = (): CognitiveMapData => {
    const evaluations = history.filter(h => h.score !== undefined);
    const averageScore = evaluations.length > 0 
      ? evaluations.reduce((acc, curr) => acc + (curr.score || 0), 0) / evaluations.length 
      : 0;

    const masteredConceptsSet = new Set<string>();
    const weakAreasSet = new Set<string>();

    history.forEach(h => {
      if (h.score && h.score > 8) masteredConceptsSet.add(h.title);
      else if (h.score && h.score < 6) weakAreasSet.add(h.title);
    });

    return {
      totalExercises: history.length,
      averageScore,
      masteredConcepts: Array.from(masteredConceptsSet).slice(0, 5),
      weakAreas: Array.from(weakAreasSet).slice(0, 5),
      progressOverTime: evaluations.map(e => ({ date: e.date, score: e.score || 0 })),
      activityDistribution: {} // Se puede completar luego
    };
  };

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
        
        // GUARDAMOS EN HISTORIAL (ADN IA Studio)
        saveToHistory(
          'CORRECTION', 
          `Corrección: ${writingInput.materia}`, 
          data.resultado, 
          parseFloat(data.resultado.grade)
        );
      } else {
        alert(data.error || "Error en la evaluación");
      }
    } catch (error) {
      alert("Error de conexión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold">
            <BookOpen size={18} />
          </div>
          <h1 className="font-black text-slate-800 text-lg tracking-tighter uppercase">MENTOR IA</h1>
        </div>
        
        {state !== AppState.WELCOME && (
          <button 
            onClick={() => { setResultado(null); setState(AppState.WELCOME); }}
            className="flex items-center gap-1 text-slate-500 hover:text-indigo-600 transition-colors text-sm font-bold uppercase tracking-tighter"
          >
            <ChevronLeft size={18} /> Volver
          </button>
        )}
      </header>

      <main className="flex-1 flex flex-col w-full max-w-5xl mx-auto p-6">
        
        {/* PANTALLA: BIENVENIDA */}
        {state === AppState.WELCOME && (
          <Welcome 
            onStart={() => setState(AppState.WRITING_CORRECTION_INPUT)}
            onViewHistory={() => setState(AppState.HISTORY)}
            onViewCognitiveMap={() => setState(AppState.COGNITIVE_MAP)}
            restantes={userStats.restantes}
          />
        )}

        {/* PANTALLA: EDITOR (Módulo de entrenamiento) */}
        {state === AppState.WRITING_CORRECTION_INPUT && !resultado && (
          <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-bottom-4 duration-500">
            <textarea 
              className="flex-1 w-full p-8 text-xl border-2 border-slate-200 rounded-[2.5rem] focus:border-indigo-500 outline-none shadow-inner bg-white resize-none"
              placeholder="Pega tu informe técnico aquí..."
              value={writingInput.writing}
              onChange={(e) => setWritingInput({...writingInput, writing: e.target.value})}
            />
            <div className="flex justify-between items-center gap-4">
              <select 
                className="bg-white border-2 border-slate-200 rounded-2xl px-6 py-4 font-bold text-slate-700 outline-none focus:border-indigo-600"
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
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-12 py-4 rounded-2xl font-black transition-all shadow-xl flex items-center gap-2"
              >
                {loading ? <Loader2 className="animate-spin" /> : <Send size={20} />}
                {loading ? "PROCESANDO..." : "ANALIZAR"}
              </button>
            </div>
          </div>
        )}

        {/* PANTALLA: RESULTADOS (Igual que antes, pero ya guardado en historial) */}
        {resultado && state === AppState.WRITING_CORRECTION_INPUT && (
           <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
            <div className="bg-indigo-600 p-8 text-white flex justify-between items-center">
              <div>
                <h3 className="text-3xl font-black tracking-tighter tracking-widest uppercase italic">Evaluación Exitosa</h3>
                <p className="opacity-80 font-bold text-xs">Materia: {writingInput.materia}</p>
              </div>
              <div className="text-center bg-white/20 p-4 rounded-2xl backdrop-blur-md min-w-[100px]">
                <span className="block text-4xl font-black">{resultado.grade}</span>
                <span className="text-[10px] uppercase font-bold tracking-tighter">Nota</span>
              </div>
            </div>
            {/* Contenido del resultado... (puedes mantener el que tenías) */}
            <div className="p-8">
               <p className="text-slate-600 leading-relaxed font-medium">{resultado.performanceAnalysis}</p>
               <button onClick={() => {setResultado(null); setState(AppState.WELCOME)}} className="mt-6 text-indigo-600 font-bold hover:underline italic">← Volver al inicio</button>
            </div>
          </div>
        )}

        {/* PANTALLAS FUTURAS: Aquí irán los componentes de Historial y Mapa */}
        {state === AppState.HISTORY && (
          <div className="text-center py-20">
            <h2 className="text-2xl font-black text-slate-400 uppercase tracking-widest">Módulo de Historial</h2>
            <p className="text-slate-500">Próximo paso: Crear HistoryView.tsx con tus {history.length} registros.</p>
          </div>
        )}

        {state === AppState.COGNITIVE_MAP && (
          <div className="text-center py-20">
            <h2 className="text-2xl font-black text-slate-400 uppercase tracking-widest">Mapa Cognitivo</h2>
            <p className="text-slate-500">Promedio actual: {getCognitiveMapData().averageScore.toFixed(1)}</p>
          </div>
        )}

      </main>
    </div>
  );
};

export default App;
      
