import React, { useState, useEffect } from 'react';
import { AppState, WritingCorrectionInput, HistoryEntry, CognitiveMapData, ConceptualNetworkResult, UniversityText, MathExplainerInput, MathCorrectionInput, ExamData, ExamEvaluation, ExamQuestionType } from './types';
import Welcome from './components/Welcome'; 
import HistoryView from './components/HistoryView';
import CognitiveMapView from './components/CognitiveMapView';
import ActivitySelection from './components/ActivitySelection'; 
import DataEntryView from './components/DataEntryView';
import SummaryToolSelection from './components/SummaryToolSelection';
import SummaryGenerationInputView from './components/SummaryGenerationInputView';
import SummaryCorrectionInputView from './components/SummaryCorrectionInputView';
import SummaryGenerationResultsView from './components/SummaryGenerationResultsView';
import SummaryCorrectionResultsView from './components/SummaryCorrectionResultsView';
import ConceptualNetworkInputView from './components/ConceptualNetworkInputView';
import ConceptualNetworkView from './components/ConceptualNetworkView';
import WritingCorrectionForm from './components/WritingCorrectionForm';
import CorrectionResultsView from './components/CorrectionResultsView';
import MathExplainerForm from './components/math/MathExplainerForm';
import MathExplainerResults from './components/math/MathExplainerResults';
import MathCorrectionForm from './components/math/MathCorrectionForm';
import MathCorrectionResults from './components/math/MathCorrectionResults';
import ExamInputView from './components/ExamInputView';
import ExamTakingView from './components/ExamTakingView';
import ExamResultsView from './components/ExamResultsView';
import { examService } from './services/examService';
import { BookOpen, ChevronLeft, ExternalLink, Clock, CheckCircle2 } from 'lucide-react';

enum MathAppState {
  MATH_EXPLAINER_INPUT = 'MATH_EXPLAINER_INPUT',
  MATH_EXPLAINER_RESULTS = 'MATH_EXPLAINER_RESULTS',
  MATH_CORRECTION_INPUT = 'MATH_CORRECTION_INPUT',
  MATH_CORRECTION_RESULTS = 'MATH_CORRECTION_RESULTS'
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState | MathAppState | string>(AppState.WELCOME);
  const [loading, setLoading] = useState(false);
  const [userStats, setUserStats] = useState({ logueado: false, restantes: 0, url_ad: '', bloques_ad: 0 });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  
  // --- ESTADOS PARA PUBLICIDAD ---
  const [showAdModal, setShowAdModal] = useState(false);
  const [adCounter, setAdCounter] = useState(0);
  const [canConfirmAd, setCanConfirmAd] = useState(false);

  const [writingInput, setWritingInput] = useState<WritingCorrectionInput>({
    writing: '', prompt: '', sourceText: '', materia: 'higiene_upe', activityType: '', activityTitle: '' 
  });
  
  const [resultado, setResultado] = useState<any>(null);
  const [networkResult, setNetworkResult] = useState<ConceptualNetworkResult | null>(null);
  const [examData, setExamData] = useState<ExamData | null>(null);
  const [examEvaluation, setExamEvaluation] = useState<ExamEvaluation | null>(null);
  const [currentMaterial, setCurrentMaterial] = useState('');

  const fetchUserStats = () => {
    fetch('/api/usuario')
      .then(res => res.json())
      .then(data => setUserStats(data))
      .catch(err => console.error("Error al cargar usuario:", err));
  };

  useEffect(() => {
    fetchUserStats();
    const savedHistory = localStorage.getItem('academic_history');
    if (savedHistory) {
      try { setHistory(JSON.parse(savedHistory)); } 
      catch (e) { console.error('Error loading history', e); }
    }
  }, []);

  // Lógica del contador de publicidad
  useEffect(() => {
    let timer: number;
    if (showAdModal && adCounter > 0) {
      timer = window.setInterval(() => {
        setAdCounter(prev => prev - 1);
      }, 1000);
    } else if (adCounter === 0 && showAdModal) {
      setCanConfirmAd(true);
    }
    return () => clearInterval(timer);
  }, [showAdModal, adCounter]);

  const handleOpenAd = () => {
    window.open(userStats.url_ad, '_blank');
    setAdCounter(15);
    setCanConfirmAd(false);
  };

  const handleConfirmAd = async () => {
    try {
      const res = await fetch('/api/registrar_ad', { method: 'POST' });
      if (res.ok) {
        setShowAdModal(false);
        fetchUserStats();
      } else {
        const data = await res.json();
        alert(data.error);
      }
    } catch (e) { alert("Error al confirmar créditos"); }
  };

  const checkCredits = () => {
    if (userStats.restantes <= 0) {
      setShowAdModal(true);
      return false;
    }
    return true;
  };

  const saveToHistory = (type: string, title: string, data: any, score?: number) => {
    const newEntry: HistoryEntry = {
      id: crypto.randomUUID(), date: new Date().toISOString(),
      type, title, data, score
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
      totalExercises: history.length, averageScore: averageScore, masteredConcepts: [], weakAreas: [],
      progressOverTime: evaluations.map(e => ({ date: e.date, score: e.score || 0 })).reverse(),
      concepts: [], connections: [], areas: []
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
      EXPLAINER: 'Explicador de Conceptos', SUMMARY: 'Gestión de Resúmenes',
      NETWORK: 'Red Conceptual', CORRECTION: 'Corregir Escrito',
      MATH: 'Módulo de Matemáticas', EXAM: 'Examen Parcial'
    };

    if (activityId === 'SUMMARY') setState(AppState.SUMMARY_SELECTION);
    else if (activityId === 'NETWORK') { setNetworkResult(null); setState(AppState.TEXT_DISPLAY); }
    else if (activityId === 'CORRECTION') {
      setWritingInput(prev => ({ ...prev, activityType: 'CORRECTION', activityTitle: activityTitles[activityId] }));
      setState(AppState.WRITING_CORRECTION_INPUT);
    } 
    else if (activityId === 'MATH') setState(MathAppState.MATH_EXPLAINER_INPUT);
    else if (activityId === 'EXAM') setState(AppState.EXAM_INPUT);
    else {
      setWritingInput(prev => ({ ...prev, activityType: activityId, activityTitle: activityTitles[activityId] }));
      setState(AppState.WRITING_CORRECTION_INPUT);
    }
  };

  const handleStartExam = async (material: string, count: number, types: ExamQuestionType[]) => {
    if (!checkCredits()) return;
    setLoading(true);
    setCurrentMaterial(material);
    try {
      const data = await examService.generateExam(material, count, types);
      setExamData(data);
      setState(AppState.EXAM_TAKING);
      fetchUserStats();
    } catch (e) { 
      if (e instanceof Error && e.message === 'CREDITS_EXHAUSTED') {
        setShowAdModal(true);
      } else {
        alert("Error al generar examen");
      }
    }
    finally { setLoading(false); }
  };

  const handleSubmitExam = async (answers: Record<string, string>) => {
    setLoading(true);
    try {
      const evaluation = await examService.evaluateExam(answers, currentMaterial);
      setExamEvaluation(evaluation);
      saveToHistory('EXAM', 'Simulacro de Examen', evaluation, evaluation.grade);
      setState(AppState.EXAM_RESULTS);
      fetchUserStats();
    } catch (e) { alert("Error al corregir examen"); }
    finally { setLoading(false); }
  };

  const handleMathExplain = async (input: MathExplainerInput) => {
    if (!checkCredits()) return;
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
    if (!checkCredits()) return;
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
    if (!checkCredits()) return;
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
    if (!checkCredits()) return;
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
        setUserStats(prev => ({ ...prev, restantes: data.restantes }));
        saveToHistory('SUMMARY_GEN', title, data.resultado);
        setState(AppState.SUMMARY_GENERATION_RESULTS);
      } else alert(data.error);
    } catch (e) { alert("Error de conexión"); }
    finally { setLoading(false); }
  };

  const handleSummaryCorrection = async (sourceText: string, userSummary: string) => {
    if (!checkCredits()) return;
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
        setUserStats(prev => ({ ...prev, restantes: data.restantes }));
        saveToHistory('SUMMARY_CORR', 'Corrección de Resumen', data.resultado, data.resultado.grade);
        setState(AppState.SUMMARY_CORRECTION_RESULTS);
      } else alert(data.error);
    } catch (e) { alert("Error de conexión"); }
    finally { setLoading(false); }
  };

  const handleGenerateNetwork = async (data: UniversityText) => {
    if (!checkCredits()) return;
    setLoading(true);
    try {
      const response = await fetch('/api/generar_red', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: data.content, query: data.title, materia: writingInput.materia }),
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
    if (!checkCredits()) return;
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
      {/* MODAL DE PUBLICIDAD */}
      {showAdModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-white rounded-[2rem] shadow-2xl max-w-md w-full p-8 text-center border border-slate-200 overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-2 bg-indigo-100">
              <div 
                className="h-full bg-indigo-600 transition-all duration-1000 ease-linear" 
                style={{ width: `${(adCounter / 15) * 100}%` }}
              ></div>
            </div>
            
            <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              {canConfirmAd ? <CheckCircle2 size={32} /> : <Clock size={32} />}
            </div>

            <h3 className="text-2xl font-black text-slate-800 mb-2 uppercase italic tracking-tighter">¡Consultas Agotadas!</h3>
            <p className="text-slate-600 mb-8 font-medium">Mira un breve anuncio de 15 segundos para desbloquear más consultas gratuitas.</p>

            <div className="space-y-4">
              <button
                onClick={handleOpenAd}
                className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-100"
              >
                VER ANUNCIO <ExternalLink size={18} />
              </button>

              <button
                onClick={handleConfirmAd}
                disabled={!canConfirmAd}
                className={`w-full py-4 rounded-xl font-bold transition-all ${
                  canConfirmAd 
                  ? 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-100' 
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                }`}
              >
                {adCounter > 0 ? `ESPERA ${adCounter}s...` : 'CONFIRMAR CRÉDITOS'}
              </button>

              <button 
                onClick={() => setShowAdModal(false)}
                className="text-slate-400 text-xs font-bold uppercase tracking-widest hover:text-slate-600 transition-colors"
              >
                CERRAR
              </button>
            </div>
          </div>
        </div>
      )}

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
          <ActivitySelection 
            onSelect={handleActivitySelect} 
            restantes={userStats.restantes} 
          />
        )}

        {state === AppState.EXAM_INPUT && (
          <ExamInputView onStart={handleStartExam} onBack={() => setState(AppState.ACTIVITY_SELECTION)} isLoading={loading} />
        )}

        {state === AppState.EXAM_TAKING && examData && (
          <ExamTakingView examData={examData} onSubmit={handleSubmitExam} isLoading={loading} />
        )}

        {state === AppState.EXAM_RESULTS && examEvaluation && (
          <ExamResultsView evaluation={examEvaluation} onRetry={() => setState(AppState.EXAM_INPUT)} onFinish={() => setState(AppState.WELCOME)} />
        )}

        {state === MathAppState.MATH_EXPLAINER_INPUT && (
          <MathExplainerForm onBack={() => setState(AppState.ACTIVITY_SELECTION)} onSubmit={handleMathExplain} onGoToCorrection={() => setState(MathAppState.MATH_CORRECTION_INPUT)} />
        )}

        {state === MathAppState.MATH_EXPLAINER_RESULTS && resultado && (
          <MathExplainerResults result={resultado} onBack={() => setState(MathAppState.MATH_EXPLAINER_INPUT)} onRetry={() => setState(MathAppState.MATH_EXPLAINER_INPUT)} onRestart={() => setState(AppState.WELCOME)} />
        )}

        {state === MathAppState.MATH_CORRECTION_INPUT && (
          <MathCorrectionForm onBack={() => setState(MathAppState.MATH_EXPLAINER_INPUT)} onSubmit={handleMathCorrection} />
        )}

        {state === MathAppState.MATH_CORRECTION_RESULTS && resultado && (
          <MathCorrectionResults result={resultado} onRestart={() => setState(AppState.ACTIVITY_SELECTION)} onRetry={() => setState(MathAppState.MATH_CORRECTION_INPUT)} />
        )}

        {state === AppState.WRITING_CORRECTION_INPUT && writingInput.activityType === 'CORRECTION' && (
          <WritingCorrectionForm isLoading={loading} onSubmit={handleWritingCorrection} />
        )}

        {state === AppState.WRITING_CORRECTION_RESULTS && resultado && (
          <CorrectionResultsView result={resultado} onRetry={() => { setResultado(null); setState(AppState.WRITING_CORRECTION_INPUT); }} />
        )}

        {state === AppState.TEXT_DISPLAY && (
           <div className="flex-1 flex flex-col">
              {/* Aquí iría la lógica de renderizado para TEXT_DISPLAY si el archivo estuviera completo */}
           </div>
        )}
      </main>
    </div>
  );
};

export default App;

