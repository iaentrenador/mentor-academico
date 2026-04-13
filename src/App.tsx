import React, { useState, useEffect } from 'react';
import { AppState, WritingCorrectionInput, HistoryEntry, CognitiveMapData } from './types';
import Welcome from './components/Welcome'; 
import HistoryView from './components/HistoryView';
import CognitiveMapView from './components/CognitiveMapView';
import ActivitySelection from './components/ActivitySelection'; 
import DataEntryView from './components/DataEntryView'; // IMPORTADO EL NUEVO COMPONENTE
import { BookOpen, ChevronLeft } from 'lucide-react';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>(AppState.WELCOME);
  const [loading, setLoading] = useState(false);
  const [userStats, setUserStats] = useState({ logueado: false, restantes: 0 });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  
  // Ajustado para manejar el perfil y la duda específica (query)
  const [writingInput, setWritingInput] = useState<WritingCorrectionInput & { query?: string; profile?: string }>({
    writing: '',
    materia: 'higiene_upe',
    activityType: '',
    query: '',
    profile: 'higiene_upe'
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
    
    return {
      totalExercises: history.length,
      averageScore: averageScore,
      masteredConcepts: [],
      weakAreas: [],
      progressOverTime: evaluations.map(e => ({ date: e.date, score: e.score || 0 })).reverse(),
      concepts: [],
      connections: [],
      areas: []
    };
  };

  const handleViewHistoryItem = (item: HistoryEntry) => {
    setResultado(item.data);
    setState(AppState.WRITING_CORRECTION_INPUT);
  };

  // 1. Maneja la selección de la tarjeta
  const handleActivitySelect = (activityId: string) => {
    const activityTitles: Record<string, string> = {
      EXPLAINER: 'Explicador de Conceptos',
      SUMMARY: 'Gestión de Resúmenes',
      NETWORK: 'Red Conceptual',
      CORRECTION: 'Corregir Escrito',
      RAP: 'Rap Técnico Académico',
      EXAM: 'Examen Parcial',
      MASTER: 'Sintetizador Maestro'
    };

    setWritingInput(prev => ({ 
      ...prev, 
      activityType: activityId,
      activityTitle: activityTitles[activityId] || 'Actividad'
    }));
    setState(AppState.WRITING_CORRECTION_INPUT);
  };

  // 2. Maneja el envío desde DataEntryView
  const handleDataSubmit = async (data: { text: string; query?: string; profile: string }) => {
    setLoading(true);
    
    // Sincronizamos el estado local con lo que viene del formulario
    const payload = {
      ...writingInput,
      writing: data.text,
      query: data.query,
      materia: data.profile, // Usamos el ID del perfil como materia para el backend
      profile: data.profile
    };

    try {
      const response = await fetch('/api/corregir_escrito', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const resData = await response.json();
      
      if (response.ok) {
        setResultado(resData.resultado);
        setUserStats(prev => ({ ...prev, restantes: resData.restantes }));
        saveToHistory(
          'CORRECTION', 
          `${writingInput.activityType}: ${data.profile}`, 
          resData.resultado, 
          Number(resData.resultado.grade || 0)
        );
      } else {
        alert(resData.error || "Error en la evaluación");
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

      <main className="flex-1 flex flex-col w-full max-w-6xl mx-auto p-6">
        
        {state === AppState.WELCOME && (
          <Welcome 
            onStart={() => setState(AppState.ACTIVITY_SELECTION)}
            onViewHistory={() => setState(AppState.HISTORY)}
            onViewCognitiveMap={() => setState(AppState.COGNITIVE_MAP)}
            restantes={userStats.restantes}
          />
        )}

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

        {/* REEMPLAZO: Ahora usamos DataEntryView en lugar del textarea genérico */}
        {state === AppState.WRITING_CORRECTION_INPUT && !resultado && (
          <DataEntryView 
            activityId={writingInput.activityType}
            activityTitle={(writingInput as any).activityTitle}
            onBack={() => setState(AppState.ACTIVITY_SELECTION)}
            onSubmit={handleDataSubmit}
            loading={loading}
          />
        )}

        {/* Vista de Resultados (Se mantiene igual, pero ahora recibe datos más ricos) */}
        {resultado && state === AppState.WRITING_CORRECTION_INPUT && (
           <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
            <div className="bg-indigo-600 p-8 text-white flex justify-between items-center">
              <div>
                <h3 className="text-3xl font-black tracking-tighter uppercase italic">Evaluación Técnica</h3>
                <p className="opacity-80 font-bold text-xs uppercase tracking-widest">
                  Perfil: {writingInput.materia}
                </p>
              </div>
              <div className="text-center bg-white/20 p-4 rounded-2xl backdrop-blur-md min-w-[100px] border border-white/20">
                <span className="block text-4xl font-black">{resultado.grade || '-'}</span>
                <span className="text-[10px] uppercase font-bold tracking-tighter">Nota / Nivel</span>
              </div>
            </div>
            
            <div className="p-8 space-y-6 overflow-y-auto max-h-[60vh]">
               <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 prose prose-indigo max-w-none">
                  <h4 className="font-black text-slate-800 mb-3 uppercase text-xs tracking-widest">Respuesta del Mentor</h4>
                  {/* Aquí podríamos estructurar según si es EXPLAINER o no */}
                  <p className="text-slate-600 leading-relaxed font-medium whitespace-pre-wrap">
                    {resultado.explanation || resultado.performanceAnalysis}
                  </p>
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
          
