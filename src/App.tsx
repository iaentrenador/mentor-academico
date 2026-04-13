import React, { useState, useEffect } from 'react';
import { AppState, WritingCorrectionInput, WritingCorrectionResult, HistoryEntry, CognitiveMapData, SummaryGenerationResult, SummaryCorrectionResult, ConceptualNetworkResult, UniversityText } from './types';
import Welcome from './components/Welcome'; 
import HistoryView from './components/HistoryView';
import CognitiveMapView from './components/CognitiveMapView';
import ActivitySelection from './components/ActivitySelection'; 
import DataEntryView from './components/DataEntryView';
// IMPORTACIÓN DE NUEVOS COMPONENTES
import SummaryToolSelection from './components/SummaryToolSelection';
import SummaryGenerationInputView from './components/SummaryGenerationInputView';
import SummaryCorrectionInputView from './components/SummaryCorrectionInputView';
import SummaryGenerationResultsView from './components/SummaryGenerationResultsView';
import SummaryCorrectionResultsView from './components/SummaryCorrectionResultsView';
// IMPORTACIÓN COMPONENTES RED CONCEPTUAL
import ConceptualNetworkInputView from './components/ConceptualNetworkInputView';
import ConceptualNetworkView from './components/ConceptualNetworkView';
// IMPORTACIÓN NUEVA CORRECCIÓN DE ESCRITOS
import WritingCorrectionForm from './components/WritingCorrectionForm';
import CorrectionResultsView from './components/CorrectionResultsView';

import { BookOpen, ChevronLeft } from 'lucide-react';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>(AppState.WELCOME);
  const [loading, setLoading] = useState(false);
  const [userStats, setUserStats] = useState({ logueado: false, restantes: 0 });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  
  const [writingInput, setWritingInput] = useState<WritingCorrectionInput>({
    writing: '',
    prompt: '',
    sourceText: '',
    materia: 'higiene_upe',
    activityType: '',
    activityTitle: '' 
  });
  
  const [resultado, setResultado] = useState<any>(null);
  const [networkResult, setNetworkResult] = useState<ConceptualNetworkResult | null>(null);

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
    if (item.type === 'SUMMARY_GEN') setState(AppState.SUMMARY_GENERATION_RESULTS);
    else if (item.type === 'SUMMARY_CORR') setState(AppState.SUMMARY_CORRECTION_RESULTS);
    else if (item.type === 'WRITING_CORR') setState(AppState.WRITING_CORRECTION_RESULTS);
    else if (item.type === 'NETWORK') {
      setNetworkResult(item.data);
      setResultado(null);
    }
    else setState(AppState.WRITING_CORRECTION_INPUT);
  };

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

    if (activityId === 'SUMMARY') {
      setState(AppState.SUMMARY_SELECTION);
    } else if (activityId === 'NETWORK') {
      setNetworkResult(null);
      setState(AppState.TEXT_DISPLAY);
    } else if (activityId === 'CORRECTION') {
      setWritingInput(prev => ({ ...prev, activityType: 'CORRECTION' }));
      setState(AppState.WRITING_CORRECTION_INPUT);
    } else {
      setWritingInput(prev => ({ ...prev, activityType: activityId, activityTitle: activityTitles[activityId] }));
      setState(AppState.WRITING_CORRECTION_INPUT);
    }
  };

  // --- LÓGICA CORRECCIÓN DE ESCRITOS (NUEVA) ---
  const handleWritingCorrection = async (input: WritingCorrectionInput) => {
    setLoading(true);
    try {
      const response = await fetch('/api/corregir_escrito', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input)
      });
      const data = await response.json();
      if (response.ok) {
        setResultado(data.resultado);
        setUserStats(prev => ({ ...prev, restantes: data.restantes }));
        saveToHistory('WRITING_CORR', `Corrección: ${input.materia}`, data.resultado, data.resultado.grade);
        setState(AppState.WRITING_CORRECTION_RESULTS);
      } else alert(data.error);
    } catch (e) { alert("Error de conexión"); }
    finally { setLoading(false); }
  };

  // --- LÓGICA ESPECÍFICA PARA RESÚMENES ---
  const handleSummaryGeneration = async (title: string, content: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/generar_resumen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content })
      });
      const data = await response.json();
      if (response.ok) {
        setResultado(data.resultado);
        saveToHistory('SUMMARY_GEN', title, data.resultado);
        setState(AppState.SUMMARY_GENERATION_RESULTS);
      } else alert(data.error);
    } catch (e) { alert("Error de conexión"); }
    finally { setLoading(false); }
  };

  const handleSummaryCorrection = async (sourceText: string, userSummary: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/corregir_resumen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sourceText, userSummary })
      });
      const data = await response.json();
      if (response.ok) {
        setResultado(data.resultado);
        saveToHistory('SUMMARY_CORR', 'Corrección de Resumen', data.resultado, data.resultado.grade);
        setState(AppState.SUMMARY_CORRECTION_RESULTS);
      } else alert(data.error);
    } catch (e) { alert("Error de conexión"); }
    finally { setLoading(false); }
  };

  // --- LÓGICA RED CONCEPTUAL ---
  const handleGenerateNetwork = async (data: UniversityText) => {
    setLoading(true);
    try {
      const response = await fetch('/api/generar_red', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          texto: data.content,
          query: data.title,
          materia: writingInput.materia
        }),
      });
      const resData = await response.json();
      if (response.ok) {
        setNetworkResult(resData.resultado);
        saveToHistory('NETWORK', data.title, resData.resultado);
        setUserStats(prev => ({ ...prev, restantes: resData.restantes }));
      } else alert(resData.error);
    } catch (e) { alert("Error de conexión"); }
    finally { setLoading(false); }
  };

  // --- LÓGICA DATA ENTRY GENERAL (MANTENIDA PARA OTROS MÓDULOS) ---
  const handleDataSubmit = async (data: { text: string; query?: string; profile: string }) => {
    setLoading(true);
    const payload = { ...writingInput, writing: data.text, query: data.query || '', materia: data.profile };
    try {
      const response = await fetch(`/api/${writingInput.activityType?.toLowerCase()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const resData = await response.json();
      if (response.ok) {
        setResultado(resData.resultado);
        setUserStats(prev => ({ ...prev, restantes: resData.restantes }));
        saveToHistory('ACTIVITY', writingInput.activityTitle, resData.resultado);
      } else alert(resData.error);
    } catch (error) { alert("Error de conexión"); }
    finally { setLoading(false); }
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
            onClick={() => { setResultado(null); setNetworkResult(null); setState(AppState.WELCOME); }}
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

        {/* --- MÓDULO CORRECCIÓN DE ESCRITOS --- */}
        {state === AppState.WRITING_CORRECTION_INPUT && writingInput.activityType === 'CORRECTION' && (
          <WritingCorrectionForm 
            isLoading={loading}
            onSubmit={handleWritingCorrection}
          />
        )}

        {state === AppState.WRITING_CORRECTION_RESULTS && resultado && (
          <CorrectionResultsView 
            result={resultado}
            onRetry={() => { setResultado(null); setState(AppState.WRITING_CORRECTION_INPUT); }}
          />
        )}

        {/* --- RENDERING MÓDULO RED CONCEPTUAL --- */}
        {state === AppState.TEXT_DISPLAY && !networkResult && (
          <ConceptualNetworkInputView 
            onBack={() => setState(AppState.ACTIVITY_SELECTION)}
            onSubmit={handleGenerateNetwork}
          />
        )}

        {networkResult && (
          <ConceptualNetworkView 
            result={networkResult}
            onRestart={() => { setNetworkResult(null); setState(AppState.ACTIVITY_SELECTION); }}
          />
        )}

        {/* --- RENDERING MÓDULO RESÚMENES --- */}
        {state === AppState.SUMMARY_SELECTION && (
          <SummaryToolSelection 
            onBack={() => setState(AppState.ACTIVITY_SELECTION)}
            onStartAutomatic={() => setState(AppState.SUMMARY_GENERATION_INPUT)}
            onStartCorrection={() => setState(AppState.SUMMARY_CORRECTION_INPUT)}
          />
        )}

        {state === AppState.SUMMARY_GENERATION_INPUT && (
          <SummaryGenerationInputView 
            onBack={() => setState(AppState.SUMMARY_SELECTION)}
            onSubmit={handleSummaryGeneration}
            loading={loading}
          />
        )}

        {state === AppState.SUMMARY_CORRECTION_INPUT && (
          <SummaryCorrectionInputView 
            onBack={() => setState(AppState.SUMMARY_SELECTION)}
            onSubmit={handleSummaryCorrection}
            loading={loading}
          />
        )}

        {state === AppState.SUMMARY_GENERATION_RESULTS && resultado && (
          <SummaryGenerationResultsView 
            result={resultado}
            onRestart={() => { setResultado(null); setState(AppState.SUMMARY_SELECTION); }}
          />
        )}

        {state === AppState.SUMMARY_CORRECTION_RESULTS && resultado && (
          <SummaryCorrectionResultsView 
            result={resultado}
            onRestart={() => { setResultado(null); setState(AppState.SUMMARY_SELECTION); }}
          />
        )}

        {/* --- OTROS ESTADOS --- */}
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

        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            <p className="mt-4 text-slate-600 font-medium">Procesando material académico...</p>
          </div>
        )}

        {state === AppState.WRITING_CORRECTION_INPUT && writingInput.activityType !== 'CORRECTION' && !resultado && !loading && (
          <DataEntryView 
            activityId={writingInput.activityType || ''}
            activityTitle={writingInput.activityTitle || ''}
            onBack={() => setState(AppState.ACTIVITY_SELECTION)}
            onSubmit={handleDataSubmit}
            loading={loading}
          />
        )}

        {resultado && state === AppState.WRITING_CORRECTION_INPUT && (
          <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
            {/* ... visualizador antiguo para otras tareas ... */}
            <div className="bg-indigo-600 p-8 text-white">
              <h3 className="text-3xl font-black italic uppercase">Resultado</h3>
            </div>
            <div className="p-8">
              <p className="text-slate-600 whitespace-pre-wrap">{resultado.explanation || JSON.stringify(resultado)}</p>
              <button onClick={() => setResultado(null)} className="mt-6 w-full py-4 bg-slate-900 text-white rounded-2xl font-bold">Cerrar</button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
      
