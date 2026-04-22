import React from 'react';
import { MathExplainerResult } from '../../types';
import { Lightbulb, BookOpen, Zap, ArrowRight, RotateCcw, Home, ChevronLeft } from 'lucide-react';

interface MathExplainerResultsProps {
  result: MathExplainerResult;
  onRestart: () => void;
  onRetry: () => void;
  onBack: () => void;
}

const MathExplainerResults: React.FC<MathExplainerResultsProps> = ({ result, onRestart, onRetry, onBack }) => {
  return (
    <div className="space-y-8 animate-in fade-in zoom-in-95 duration-500 max-w-4xl mx-auto p-4">
      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
        {/* Encabezado de Resultados */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center">
              <Lightbulb className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-slate-800">Explicación del Método</h3>
              <p className="text-slate-500 text-sm font-medium">Conceptos clave y ejercicio guía.</p>
            </div>
          </div>
          <button 
            onClick={onBack}
            className="p-2 text-slate-400 hover:text-indigo-600 transition-colors"
            title="Volver"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
        </div>

        {/* Marco Teórico */}
        {result.theoreticalContext && (
          <div className="space-y-4">
            <h4 className="font-bold text-slate-800 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-500" />
              Marco Teórico
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
              {result.theoreticalContext}
            </p>
          </div>
        )}

        {/* Ejercicio Clon / Ejemplo */}
        {result.similarExample && (
          <div className="space-y-4">
            <h4 className="font-bold text-slate-800 flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" />
              Ejercicio Similar (Ejemplo Guía)
            </h4>
            <div className="p-6 bg-amber-50/30 border border-amber-100 rounded-2xl space-y-4">
              <div className="p-4 bg-white rounded-xl border border-amber-100 shadow-sm">
                <p className="text-[10px] font-bold text-amber-600 uppercase mb-2 tracking-widest">Problema Clon</p>
                <p className="font-mono text-sm text-slate-800">{result.similarExample.problem}</p>
              </div>

              {result.similarExample.solutionSteps && (
                <div className="space-y-3">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resolución Paso a Paso</p>
                  {result.similarExample.solutionSteps.map((step, idx) => (
                    <div key={idx} className="flex gap-3 items-start">
                      <div className="w-6 h-6 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                        {idx + 1}
                      </div>
                      <p className="text-sm text-slate-700 leading-relaxed">{step}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
                <p className="text-[10px] font-bold text-emerald-600 uppercase mb-1 tracking-widest">Resultado Final</p>
                <p className="font-mono font-bold text-emerald-900">{result.similarExample.finalResult}</p>
              </div>
            </div>
          </div>
        )}

        {/* Fórmulas y Tips */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100">
          <div className="space-y-3">
            <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2 italic">
              <ArrowRight className="w-4 h-4 text-indigo-500" />
              Fórmulas Clave
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.keyFormulas?.map((formula, idx) => (
                <code key={idx} className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-mono border border-indigo-100">
                  {formula}
                </code>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2 italic">
              <ArrowRight className="w-4 h-4 text-amber-500" />
              Tips de Resolución
            </h4>
            <ul className="space-y-1.5">
              {result.tips?.map((tip, idx) => (
                <li key={idx} className="text-xs text-slate-600 flex gap-2">
                  <span className="text-amber-500 font-bold">•</span>
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Botones de Acción */}
      <div className="flex flex-col md:flex-row gap-4">
        <button 
          onClick={onRetry}
          className="flex-1 py-4 bg-white border-2 border-slate-200 text-slate-600 font-bold rounded-2xl hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
        >
          <RotateCcw className="w-5 h-5" />
          Nueva Consulta
        </button>
        <button 
          onClick={onRestart}
          className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-900 transition-all shadow-lg shadow-slate-200 flex items-center justify-center gap-2"
        >
          <Home className="w-5 h-5" />
          Volver al Inicio
        </button>
      </div>
    </div>
  );
};

export default MathExplainerResults;
