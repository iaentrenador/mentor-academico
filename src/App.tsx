import React, { useState, useEffect } from 'react';
import { AppState, WritingCorrectionInput, HistoryEntry, CognitiveMapData } from './types';
import Welcome from './components/Welcome'; 
import HistoryView from './components/HistoryView';
import CognitiveMapView from './components/CognitiveMapView';
import ActivitySelection from './components/ActivitySelection'; // IMPORTADO
import { BookOpen, ChevronLeft, Send, Loader2 } from 'lucide-react';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>(AppState.WELCOME);
  const [loading, setLoading] = useState(false);
  const [userStats, setUserStats] = useState({ logueado: false, restantes: 0 });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [writingInput, setWritingInput] = useState<WritingCorrectionInput>({
    writing: '',
    materia: 'higiene',
    activityType: '' // Agregado para rastrear qué actividad se eligió
  });
  const [resultado, setResultado] = useState<any>(null);

  useEffect(() => {
    fetch('/api/usuario')
      .then(res => res.json())
      .then(data => setUserStats(data))
      .catch(err => console.error("Error al cargar usuario:", err));

    const savedHistory = localStorage.getItem('academic_history');
    if (savedHistory) {
      try { setHistory(JSON.parse(savedHistory)); } 
      catch (e) { console.error('Error loading history', e); }
    }
  }, []);

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

  const getCognitiveMapData = (): CognitiveMapData => {
    const evaluations = history.filter(h => h.score !== undefined);
    const averageScore = evaluations.length > 0 
      ? evaluations.reduce((acc, curr) => acc + (curr.score || 0), 0) / evaluations.length 
      : 0;
    
    const masteredConceptsSet = new Set<string>();
    const weakAreasSet = new Set<string>();

    history.forEach(h => {
      if (h.score && h.score >= 8) masteredConceptsSet.add(h.title.replace('Corrección: ', ''));
      else if (h.score && h.score < 6) weakAreasSet.add(h.title.replace('Corrección: ', ''));
    });

    return {
      totalExercises: history.length,
      averageScore: averageScore,
      masteredConcepts: Array.from(masteredConceptsSet).slice(0, 5),
      weakAreas: Array.from(weakAreasSet).slice(0, 5),
      progressOverTime: evaluations.map(e => ({ date: e.date, score: e.score || 0 })).reverse(),
      concepts: Array.from(masteredConceptsSet).slice(0, 5),
      connections: [],
      areas: Array.from(weakAreasSet).slice(0, 5)
    };
  };

  const handleViewHistoryItem = (item: HistoryEntry) => {
    setResultado(item.data);
    if (item.type === 'CORRECTION') {
      setState(AppState.WRITING_CORRECTION_INPUT);
    }
  };

  // NUEVA FUNCIÓN: Maneja la selección de la tarjeta
  const handleActivitySelect = (activityId: string) => {
    setWritingInput(prev => ({ ...prev, activityType: activityId }));
    // Por ahora, todas llevan al input de texto manual, excepto si implementamos PDF después
    setState(AppState.WRITING_CORRECTION_INPUT);
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
        saveToHistory(
          'CORRECTION', 
          `${writingInput.activityType || 'Corrección'}: ${writingInput.materia}`, 
          data.resultado, 
          Number(data.resultado.grade)
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
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-200">
            <BookOpen size={18} />
          </div>
          <h1 className="font-black text-slate-800 text-lg tracking-tighter uppercase italic">MENTOR IA</h1>
        </div>
        
        {state !== AppState.WELCOME && (
          <button 
            onClick={() => { setResultado(null); setState(AppState.WELCOME); }}
            className="flex items-center gap-1 text-slate-500 hover:text-indigo-600 transition-all text-xs font-black uppercase tracking-widest"
          >
            <ChevronLeft size={16} strokeWidth={3} /> VOLVER
          </button>
        )}
      </header>

      <main className="flex-1 flex flex-col w-full max-w-5xl mx-auto p-6">
        
        {state === AppState.WELCOME && (
          <Welcome 
            onStart={() => setState(AppState.ACTIVITY_SELECTION)} // CAMBIADO: Ahora va al menú
            onViewHistory={() => setState(AppState.HISTORY)}
            onViewCognitiveMap={() => setState(AppState.COGNITIVE_MAP)}
            restantes={userStats.restantes}
          />
        )}

        {/* NUEVA SECCIÓN: Menú de Actividades */}
        {state === AppState.ACTIVITY_SELECTION && (
          <ActivitySelection onSelect={handleActivitySelect} />
        )}

        {state === AppState.HISTORY && (
          <HistoryView 
            history={history} 
            onBack={() => setState(AppState.WELCOME)} 
            onViewItem={handleViewHistoryItem}
          />
        )}

        {state === AppState.COGNITIVE_MAP && (
          <CognitiveMapView 
            data={getCognitiveMapData()} 
            onBack={() => setState(AppState.WELCOME)} 
          />
        )}

        {state === AppState.WRITING_CORRECTION_INPUT && !resultado && (
          <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-bottom-4 duration-500">
             <div className="flex items-center gap-2 mb-2">
                <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-[10px] font-black uppercase">
                  Modo: {writingInput.activityType}
                </span>
             </div>
            <textarea 
              className="flex-1 w-full p-8 text-xl border-2 border-slate-200 rounded-[2.5rem] focus:border-indigo-500 outline-none shadow-inner bg-white resize-none transition-all focus:ring-8 focus:ring-indigo-50"
              placeholder="Pega tu texto aquí para que el Mentor lo procese..."
              value={writingInput.writing}
              onChange={(e) => setWritingInput({...writingInput, writing: e.target.value})}
            />
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <select 
                className="w-full sm:w-auto bg-white border-2 border-slate-200 rounded-2xl px-6 py-4 font-black text-slate-700 outline-none focus:border-indigo-600 uppercase text-xs tracking-widest"
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
                className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white px-12 py-4 rounded-2xl font-black transition-all shadow-xl shadow-indigo-200 flex items-center justify-center gap-2 uppercase tracking-widest italic"
              >
                {loading ? <Loader2 className="animate-spin" /> : <Send size={20} />}
                {loading ? "PROCESANDO..." : "ANALIZAR AHORA"}
              </button>
            </div>
          </div>
        )}

        {resultado && state === AppState.WRITING_CORRECTION_INPUT && (
           <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
            <div className="bg-indigo-600 p-8 text-white flex justify-between items-center">
              <div>
                <h3 className="text-3xl font-black tracking-tighter uppercase italic">Evaluación Técnica</h3>
                <p className="opacity-80 font-bold text-xs uppercase tracking-widest">Materia: {writingInput.materia}</p>
              </div>
              <div className="text-center bg-white/20 p-4 rounded-2xl backdrop-blur-md min-w-[100px] border border-white/20">
                <span className="block text-4xl font-black">{resultado.grade}</span>
                <span className="text-[10px] uppercase font-bold tracking-tighter">Nota Final</span>
              </div>
            </div>
            
            <div className="p-8 space-y-6 overflow-y-auto max-h-[60vh]">
               <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                  <h4 className="font-black text-slate-800 mb-3 uppercase text-xs tracking-widest">Análisis de Desempeño</h4>
                  <p className="text-slate-600 leading-relaxed font-medium">{resultado.performanceAnalysis}</p>
               </div>
               <button 
                onClick={() => {setResultado(null); setState(AppState.WELCOME)}} 
                className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black uppercase tracking-widest hover:bg-indigo-600 transition-all shadow-lg"
               >
                 Finalizar Revisión
               </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
  
