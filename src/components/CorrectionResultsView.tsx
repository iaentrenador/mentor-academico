import React from 'react';
import { WritingCorrectionResult } from '../types';
import { CheckCircle2, AlertCircle, ArrowRight, Award, BarChart3, RotateCcw } from 'lucide-react';

interface Props {
  result: WritingCorrectionResult;
  onRetry: () => void;
}

const CorrectionResultsView: React.FC<Props> = ({ result, onRetry }) => {
  // Función para determinar el color de la nota
  const getGradeColor = (grade: number) => {
    if (grade >= 7) return 'text-emerald-600 bg-emerald-50 border-emerald-100';
    if (grade >= 4) return 'text-amber-600 bg-amber-50 border-amber-100';
    return 'text-rose-600 bg-rose-50 border-rose-100';
  };

  const criteriaLabels: Record<string, string> = {
    understanding: 'Comprensión del Tema',
    promptAdequacy: 'Adecuación a la Consigna',
    coherence: 'Coherencia y Estructura',
    vocabulary: 'Vocabulario Técnico',
    fundamentation: 'Fundamentación Teórica'
  };

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-8 animate-in zoom-in-95 duration-500 pb-20">
      {/* Header de Puntaje */}
      <div className={`p-8 rounded-3xl border-2 text-center space-y-2 ${getGradeColor(Number(result.grade))}`}>
        <p className="text-xs font-black uppercase tracking-[0.2em]">Calificación Final</p>
        <h2 className="text-6xl font-black">{result.grade}</h2>
        <p className="font-bold text-lg">{result.status}</p>
      </div>

      {/* Análisis Docente */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-slate-800 font-bold">
          <Award className="w-5 h-5 text-indigo-500" />
          <h3>Devolución del Profesor</h3>
        </div>
        <p className="text-slate-600 leading-relaxed text-sm italic">
          "{result.performanceAnalysis}"
        </p>
      </div>

      {/* Rúbrica de Criterios (Barras de Progreso) */}
      {result.criteria && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
          <div className="flex items-center gap-2 text-slate-800 font-bold mb-4">
            <BarChart3 className="w-5 h-5 text-indigo-500" />
            <h3>Rúbrica de Evaluación</h3>
          </div>
          <div className="space-y-5">
            {Object.entries(result.criteria).map(([key, data]) => (
              <div key={key} className="space-y-2">
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500">
                  <span>{criteriaLabels[key] || key}</span>
                  <span className="text-indigo-600">{data.score}/10</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-indigo-500 transition-all duration-1000" 
                    style={{ width: `${data.score * 10}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 leading-tight">{data.feedback}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fortalezas y Debilidades */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-emerald-50 p-5 rounded-2xl border border-emerald-100 space-y-3">
          <div className="flex items-center gap-2 text-emerald-700 font-bold text-sm">
            <CheckCircle2 className="w-4 h-4" />
            <h4>Fortalezas</h4>
          </div>
          <ul className="space-y-2">
            {result.strengths?.map((s, i) => (
              <li key={i} className="text-xs text-emerald-800 flex gap-2">
                <span className="text-emerald-400">•</span> {s}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-rose-50 p-5 rounded-2xl border border-rose-100 space-y-3">
          <div className="flex items-center gap-2 text-rose-700 font-bold text-sm">
            <AlertCircle className="w-4 h-4" />
            <h4>Puntos a Mejorar</h4>
          </div>
          <ul className="space-y-2">
            {result.weaknesses?.map((w, i) => (
              <li key={i} className="text-xs text-rose-800 flex gap-2">
                <span className="text-rose-400">•</span> {w}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Plan de Acción */}
      <div className="bg-indigo-900 p-6 rounded-2xl text-white space-y-4 shadow-xl shadow-indigo-100">
        <h4 className="font-bold flex items-center gap-2">
          <ArrowRight className="w-5 h-5" />
          Plan de Mejora Sugerido
        </h4>
        <div className="space-y-3">
          {result.improvementSuggestions?.map((s, i) => (
            <div key={i} className="flex gap-3 items-start bg-white/10 p-3 rounded-xl border border-white/10">
              <span className="bg-white/20 w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold">{i+1}</span>
              <p className="text-xs leading-relaxed">{s}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Botón de Reintento */}
      <button
        onClick={onRetry}
        className="w-full py-4 bg-slate-800 text-white rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-slate-900 transition-colors shadow-lg"
      >
        <RotateCcw className="w-5 h-5" />
        Corregir otro texto
      </button>
    </div>
  );
};

export default CorrectionResultsView;
