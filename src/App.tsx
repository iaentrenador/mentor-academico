import React, { useState, useEffect } from 'react';
import { AppState, WritingCorrectionInput, HistoryEntry, CognitiveMapData, ConceptualNetworkResult, UniversityText, MathExplainerInput, MathCorrectionInput, ExamData, ExamEvaluation, ExamQuestionType } from './types';
import Welcome from './components/Welcome'; 
import HistoryView from './components/HistoryView';
import CognitiveMapView from './components/CognitiveMapView';
import ActivitySelection from './components/ActivitySelection'; 
import DataEntryView from './components/DataEntryView';
// IMPORTACIÓN DE COMPONENTES DE RESÚMENES
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

// --- IMPORTACIÓN MÓDULO MATEMÁTICAS ---
import MathExplainerForm from './components/math/MathExplainerForm';
import MathExplainerResults from './components/math/MathExplainerResults';
import MathCorrectionForm from './components/math/MathCorrectionForm';
import MathCorrectionResults from './components/math/MathCorrectionResults';

// --- IMPORTACIÓN MÓDULO EXAMEN ---
import ExamInputView from './components/ExamInputView';
import ExamTakingView from './components/ExamTakingView';
import ExamResultsView from './components/ExamResultsView';
import { examService } from './services/examService';

import { BookOpen, ChevronLeft } from 'lucide-react';

// Extendemos el AppState si no está extendido en tus types
enum MathAppState {
  MATH_EXPLAINER_INPUT = 'MATH_EXPLAINER_INPUT',
  MATH_EXPLAINER_RESULTS = 'MATH_EXPLAINER_RESULTS',
  MATH_CORRECTION_INPUT = 'MATH_CORRECTION_INPUT',
  MATH_CORRECTION_RESULTS = 'MATH_CORRECTION_RESULTS'
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState | MathAppState | string>(AppState.WELCOME);
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

  // Estados de Examen
  const [examData, setExamData] = useState<ExamData | null>(null);
  const [examEvaluation, setExamEvaluation] = useState<ExamEvaluation | null>(null);
  const [currentMaterial, setCurrentMaterial] = useState('');

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
    else if (item.type === 'MATH_EXP') setState(MathAppState.MATH_EXPLAINER_RESULTS);
    else if (item.type === 'MATH_CORR') setState(MathAppState.MATH_CORRECTION_RESULTS);
    else if (item.type === 'EXAM') {
      setExamEvaluation(item.data);
      setState(AppState.EXAM_RESULTS);
    }
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
      MATH: 'Módulo de Matemáticas',
      EXAM: 'Examen Parcial'
    };

    if (activityId === 'SUMMARY') {
      setState(AppState.SUMMARY_SELECTION);
    } else if (activityId === 'NETWORK') {
      setNetworkResult(null);
      setState(AppState.TEXT_DISPLAY);
    } else if (activityId === 'CORRECTION') {
      setWritingInput(prev => ({ ...prev, activityType: 'CORRECTION', activityTitle: activityTitles[activityId] }));
      setState(AppState.WRITING_CORRECTION_INPUT);
    } else if (activityId === 'MATH') {
      setState(MathAppState.MATH_EXPLAINER_INPUT);
    } else if (activityId === 'EXAM') {
      setState(AppState.EXAM_INPUT);
    } else {
      setWritingInput(prev => ({ ...prev, activityType: activityId, activityTitle: activityTitles[activityId] }));
      setState(AppState.WRITING_CORRECTION_INPUT);
    }
  };

  // HANDLERS EXAMEN
  const handleStartExam = async (material: string, count: number, types: ExamQuestionType[]) => {
    setLoading(true);
    setCurrentMaterial(material);
    try {
      const data = await examService.generateExam(material, count, types);
      setExamData(data);
      setState(AppState.EXAM_TAKING);
    } catch (e) { alert("Error al generar examen"); }
    finally { setLoading(false); }
  };

  const handleSubmitExam = async (answers: Record<string, string>) => {
    setLoading(true);
    try {
      const evaluation = await examService.evaluateExam(answers, currentMaterial);
      setExamEvaluation(evaluation);
      saveToHistory('EXAM', 'Simulacro de Examen', evaluation, evaluation.grade);
      setState(AppState.EXAM_RESULTS);
    } catch (e) { alert("Error al corregir examen"); }
    finally { setLoading(false); }
  };

  const handleMathExplain = async (input: MathExplainerInput) => {
    setLoading(true);
    try {
      const response = await fetch('/api/math/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input)
      });
      const data = await response.json();
      if (response.ok) {
        setResultado(data.resultado);
        setUserStats(prev => ({ ...prev, restantes: data.restantes }));
        saveToHistory('MATH_EXP', `Matemáticas: ${input.topic}`, data.resultado);
        setState(MathAppState.MATH_EXPLAINER_RESULTS);
      } else alert(data.error);
    } catch (e) { alert("Error de conexión"); }
    finally { setLoading(false); }
  };

  const handleMathCorrection = async (input: MathCorrectionInput) => {
    setLoading(true);
    try {
      const response = await fetch('/api/math/correct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input)
      });
      const data = await response.json();
      if (response.ok) {
        setResultado(data.resultado);
        setUserStats(prev => ({ ...prev, restantes: data.restantes }));
        saveToHistory('MATH_CORR', 'Corrección Matemáticas', data.resultado, data.resultado.grade);
        setState(MathAppState.MATH_CORRECTION_RESULTS);
      } else alert(data.error);
    } catch (e) { alert("Error de conexión"); }
    finally { setLoading(false); }
  };

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
        saveToHistory('ACTIVITY', writingInput.activityTitle || 'Actividad', resData.resultado);
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

        {/* --- RENDERIZADO DE EXAMEN --- */}
        {state === AppState.EXAM_INPUT && (
          <ExamInputView 
            onStart={handleStartExam} 
            onBack={() => setState(AppState.ACTIVITY_SELECTION)} 
            isLoading={loading} 
          />
        )}

        {state === AppState.EXAM_TAKING && examData && (
          <ExamTakingView 
            examData={examData} 
            onSubmit={handleSubmitExam} 
            isLoading={loading} 
          />
        )}

        {state === AppState.EXAM_RESULTS && examEvaluation && (
          <ExamResultsView 
            evaluation={examEvaluation} 
            onRetry={() => setState(AppState.EXAM_INPUT)} 
            onFinish={() => setState(AppState.WELCOME)} 
          />
        )}

        {/* --- RENDERIZADO DE MATEMÁTICAS --- */}
        {state === MathAppState.MATH_EXPLAINER_INPUT && (
          <MathExplainerForm 
            onBack={() => setState(AppState.ACTIVITY_SELECTION)}
            onSubmit={handleMathExplain}
            onGoToCorrection={() => setState(MathAppState.MATH_CORRECTION_INPUT)}
          />
        )}

        {state === MathAppState.MATH_EXPLAINER_RESULTS && resultado && (
          <MathExplainerResults 
            result={resultado}
            onBack={() => setState(MathAppState.MATH_EXPLAINER_INPUT)}
            onRetry={() => setState(MathAppState.MATH_EXPLAINER_INPUT)}
            onRestart={() => setState(AppState.WELCOME)}
          />
        )}

        {state === MathAppState.MATH_CORRECTION_INPUT && (
          <MathCorrectionForm 
            onBack={() => setState(MathAppState.MATH_EXPLAINER_INPUT)}
            onSubmit={handleMathCorrection}
          />
        )}

        {state === MathAppState.MATH_CORRECTION_RESULTS && resultado && (
          <MathCorrectionResults 
            result={resultado}
            onRestart={() => setState(AppState.ACTIVITY_SELECTION)}
            onRetry={() => setState(MathAppState.MATH_CORRECTION_INPUT)}
          />
        )}

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
