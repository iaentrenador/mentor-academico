// src/components/SummaryCorrectionResultsView.tsx
import React from 'react';
import { SummaryCorrectionResult } from '../types';
import { CheckCircle2, AlertTriangle, XCircle, Star, RefreshCcw, ArrowRight, Lightbulb } from 'lucide-react';

interface SummaryCorrectionResultsViewProps {
  result: SummaryCorrectionResult;
  onFinish: () => void; // Cambiado de onRestart a onFinish
}

const SummaryCorrectionResultsView: React.FC<SummaryCorrectionResultsViewProps> = ({ result, onFinish }) => {
  // Lógica de colores según la nota
  const getGradeStyles = (grade: number) => {
    if (grade >= 9) return { text: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100' };
    if (grade >= 7) return { text: 'text-indigo-600', bg: 'bg-indigo-50', border: 'border-indigo-100' };
    if (grade >= 5) return { text: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100' };
    return { text: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-100' };
  };

  const styles = getGradeStyles(result.grade);

  return (
    <div className="space-y-12 animate-in fade-in zoom-in-95 duration-700 max-w-5xl mx-auto w-full pb-20">
      
      {/* Tarjeta de Calificación Principal */}
      <div className={`bg-white rounded-[3rem] border-2 ${styles.border} p-10 shadow-2xl text-center relative overflow-hidden`}>
        <div className="absolute top-6 left-6">
          <span className={`px-4 py-1.5 border-2 ${styles.border} ${styles.bg} ${styles.text} text-[10px] font-black uppercase rounded-full tracking-widest`}>
            {result.status}
          </span>
        </div>
        
        <h3 className="text-sm font-black text-slate-400 uppercase tracking-[0.3em] mb-2">Calificación Académica</h3>
        <div className={`text-9xl font-black mb-6 ${styles.text} tracking-tighter italic`}>
          {result.grade.toFixed(1)}
        </div>
        
        <div className="max-w-2xl mx-auto space-y-8 text-left mt-10 border-t border-slate-100 pt-10">
          <div>
            <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Análisis del Instructor</h4>
            <p className="text-xl text-slate-700 leading-relaxed italic font-serif">
              "{result.performanceAnalysis}"
            </p>
          </div>

          {/* Fortalezas y Debilidades */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-emerald-50/50 border-2 border-emerald-100 p-6 rounded-[2rem]">
              <div className="flex items-center gap-2 mb-4 text-emerald-700">
                <CheckCircle2 size={18} />
                <h4 className="font-black text-[10px] uppercase tracking-widest">Fortalezas</h4>
              </div>
              <ul className="space-y-3">
                {result.strengths.map((s, i) => (
                  <li key={i} className="text-xs text-emerald-800 font-bold flex gap-2">
                    <span className="opacity-50">•</span> {s}
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-rose-50/50 border-2 border-rose-100 p-6 rounded-[2rem]">
              <div className="flex items-center gap-2 mb-4 text-rose-700">
                <XCircle size={18} />
                <h4 className="font-black text-[10px] uppercase tracking-widest">Debilidades</h4>
              </div>
              <ul className="space-y-3">
                {result.weaknesses.map((w, i) => (
                  <li key={i} className="text-xs text-rose-800 font-bold flex gap-2">
                    <span className="opacity-50">•</span> {w}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Ideas Omitidas */}
          <div className="bg-amber-50 border-2 border-amber-100 p-8 rounded-[2rem] relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10 text-amber-600">
              <AlertTriangle size={60} />
            </div>
            <h4 className="font-black text-amber-800 text-[10px] uppercase mb-4 tracking-widest flex items-center gap-2">
              <AlertTriangle size={14} /> Ideas Omitidas Clave
            </h4>
            <ul className="space-y-3 relative z-10">
              {result.omissions.map((o, i) => (
                <li key={i} className="text-sm text-amber-900 font-bold flex gap-3 bg-white/40 p-3 rounded-xl border border-amber-200/50">
                  <ArrowRight size={16} className="text-amber-500 shrink-0" /> {o}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Versión Ideal */}
      <div className="space-y-6">
        <div className="text-center">
          <h4 className="text-2xl font-black text-slate-800 uppercase tracking-tighter italic">Versión Superadora Propuesta</h4>
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Modelo de síntesis óptima según la cátedra</p>
        </div>
        
        <div className="bg-slate-900 text-slate-100 p-10 md:p-14 rounded-[3rem] shadow-2xl font-serif relative overflow-hidden italic shadow-indigo-200/20">
          <div className="absolute top-0 right-0 p-6 opacity-5">
             <Star size={120} strokeWidth={1} />
          </div>
          <p className="text-xl leading-relaxed indent-12 relative z-10">
            {result.improvedVersion}
          </p>
          <div className="mt-10 pt-8 border-t border-white/10 flex items-center gap-4 text-indigo-400">
             <Lightbulb size={20} />
             <p className="text-xs font-bold uppercase tracking-widest">Sugerencia: {result.suggestedRetry}</p>
          </div>
        </div>
      </div>

      {/* Acción Final */}
      <div className="flex justify-center pb-10">
        <button 
          onClick={onFinish}
          className="group px-12 py-5 bg-indigo-600 text-white font-black rounded-[2rem] hover:bg-slate-900 transition-all shadow-xl shadow-indigo-200 active:scale-95 flex items-center gap-3 uppercase tracking-[0.2em] text-xs"
        >
          <RefreshCcw size={18} className="group-hover:rotate-180 transition-transform duration-700" />
          Nuevo Entrenamiento
        </button>
      </div>
    </div>
  );
};

export default SummaryCorrectionResultsView;
