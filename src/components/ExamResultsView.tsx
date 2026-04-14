import React from 'react';
import { ExamEvaluation } from '../types';

interface ExamResultsViewProps {
  evaluation: ExamEvaluation;
  onRetry: () => void;
  onFinish: () => void;
}

const ExamResultsView: React.FC<ExamResultsViewProps> = ({ evaluation, onRetry, onFinish }) => {
  // Color según la nota
  const getGradeColor = (grade: number) => {
    if (grade >= 7) return 'text-emerald-600';
    if (grade >= 4) return 'text-amber-500';
    return 'text-rose-600';
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12">
      {/* Resumen de Calificación */}
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 text-center">
        <h2 className="text-2xl font-bold text-slate-800 mb-2">Resultado del Simulacro</h2>
        <div className={`text-6xl font-black mb-4 ${getGradeColor(evaluation.grade)}`}>
          {evaluation.grade}
        </div>
        <div className="inline-block px-4 py-1 rounded-full bg-slate-100 text-slate-600 font-semibold mb-6">
          {evaluation.status}
        </div>
        <p className="text-slate-600 leading-relaxed max-w-xl mx-auto">
          {evaluation.performanceAnalysis}
        </p>
      </div>

      {/* Desglose de Preguntas */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-slate-700 px-2">Análisis por Pregunta</h3>
        {evaluation.questionEvaluations.map((q, idx) => (
          <div key={idx} className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex justify-between items-start mb-4">
              <span className="font-bold text-slate-800">Pregunta {idx + 1}</span>
              <span className={`px-3 py-1 rounded-lg text-xs font-bold ${
                q.isCorrect ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
              }`}>
                {q.isCorrect ? 'CORRECTO' : 'A MEJORAR'}
              </span>
            </div>
            <p className="text-sm text-slate-600 mb-4 bg-slate-50 p-3 rounded-lg border border-slate-100 italic">
              " {q.feedback} "
            </p>
            <div className="text-xs font-medium text-slate-400">
              Puntaje obtenido: {q.score} pts.
            </div>
          </div>
        ))}
      </div>

      {/* Sugerencia de Repaso */}
      <div className="bg-indigo-600 p-6 rounded-2xl shadow-lg text-white">
        <h4 className="font-bold mb-2 flex items-center gap-2">
          <span>💡</span> Recomendación del Mentor
        </h4>
        <p className="text-indigo-100 text-sm italic">
          {evaluation.suggestedRetry}
        </p>
      </div>

      {/* Acciones Finales */}
      <div className="flex gap-4">
        <button
          onClick={onRetry}
          className="flex-1 py-4 bg-white border-2 border-slate-200 text-slate-600 font-bold rounded-xl hover:bg-slate-50 transition-all"
        >
          Reintentar con otro material
        </button>
        <button
          onClick={onFinish}
          className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-900 shadow-md transition-all"
        >
          Volver al Menú Principal
        </button>
      </div>
    </div>
  );
};

export default ExamResultsView;
