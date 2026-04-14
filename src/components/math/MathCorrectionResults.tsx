import React from 'react';
import { MathCorrectionResult } from '../../types';
import { CheckCircle2, XCircle, AlertCircle, RotateCcw, Award, BookOpen, Home } from 'lucide-react';

interface MathCorrectionResultsProps {
  result: MathCorrectionResult;
  onRestart: () => void;
  onRetry: () => void;
}

const MathCorrectionResults: React.FC<MathCorrectionResultsProps> = ({ result, onRestart, onRetry }) => {
  const getStatusColor = () => {
    switch (result.status) {
      case 'Excelente':
      case 'Aprobado': 
        return 'text-emerald-600 bg-emerald-50 border-emerald-200';
      case 'Satisfactorio': 
        return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'Insuficiente':
      case 'No aprobado': 
        return 'text-rose-600 bg-rose-50 border-rose-200';
      default: 
        return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in zoom-in-95 duration-500 max-w-4xl mx-auto p-4">
      {/* Cabecera de Calificación */}
      <div className={`p-8 rounded-3xl border-2 ${getStatusColor()} flex flex-col md:flex-row items-center gap-6 shadow-sm bg-white`}>
        <div className="w-24 h-24 rounded-full bg-white flex items-center justify-center text-4xl font-bold shadow-inner border-4 border-current">
          {result.grade}
        </div>
        <div className="flex-1 text-center md:text-left">
          <h3 className="text-2xl font-bold mb-1 text-slate-800">Resultado de la Evaluación</h3>
          <p className="text-lg font-medium opacity-90">{result.status}</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{result.performanceAnalysis}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Desglose Paso a Paso */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
          <h4 className="font-bold text-slate-800 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            Análisis de Resolución
          </h4>
          <div className="space-y-4">
            {result.stepByStepCorrection.map((step, idx) => (
              <div key={idx} className={`p-4 rounded-xl border ${step.isCorrect ? 'bg-emerald-50/30 border-emerald-100' : 'bg-rose-50/30 border-rose-100'}`}>
                <div className="flex items-start gap-3">
                  {step.isCorrect ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 text-rose-500 mt-0.5 shrink-0" />
                  )}
                  <div className="space-y-2">
                    <p className="text-sm font-bold text-slate-700">{step.step}</p>
                    <p className="text-xs text-slate-600 italic">{step.feedback}</p>
                    {step.correction && (
                      <div className="mt-2 p-2 bg-white rounded border border-current/20 text-xs font-mono">
                        <span className="font-bold block mb-1">Corrección sugerida:</span>
                        {step.correction}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Errores, Veredicto y Plan de Mejora */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
            <h4 className="font-bold text-slate-800 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-500" />
              Errores Conceptuales
            </h4>
            <ul className="space-y-2">
              {result.conceptualErrors.map((error, idx) => (
                <li key={idx} className="text-sm text-slate-600 flex gap-2">
                  <span className="text-amber-500 font-bold">•</span>
                  {error}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-indigo-600 p-6 rounded-3xl text-white shadow-lg space-y-2">
            <h4 className="font-bold flex items-center gap-2">
              <Award className="w-5 h-5" />
              Veredicto del Instructor
            </h4>
            <p className="text-sm leading-relaxed italic opacity-90">"{result.finalVerdict}"</p>
          </div>

          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
            <h4 className="font-bold text-slate-800 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-blue-500" />
              Plan de Mejora
            </h4>
            <ul className="space-y-2">
              {result.improvementSuggestions.map((suggestion, idx) => (
                <li key={idx} className="text-sm text-slate-600 flex gap-2">
                  <span className="text-blue-500 font-bold">•</span>
                  {suggestion}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Botones de Navegación */}
      <div className="flex flex-col md:flex-row gap-4 pt-4">
        <button 
          onClick={onRetry}
          className="flex-1 py-4 bg-white border-2 border-slate-200 text-slate-600 font-bold rounded-2xl hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
        >
          <RotateCcw className="w-5 h-5" />
          Reintentar Resolución
        </button>
        <button 
          onClick={onRestart}
          className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-900 transition-all shadow-lg flex items-center justify-center gap-2"
        >
          <Home className="w-5 h-5" />
          Finalizar Sesión
        </button>
      </div>
    </div>
  );
};

export default MathCorrectionResults;
