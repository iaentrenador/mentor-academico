import React from 'react';
import { CheckCircle2, Lightbulb, ArrowRight, RefreshCcw, Plus } from 'lucide-react';

interface ConceptExplainerResultsViewProps {
  result: {
    explanation: string;
    examples: string[];
    keyTakeaways: string[];
    relatedConcepts: string[];
  };
  onRestart: () => void;
  onNewQuestion: () => void;
}

const ConceptExplainerResultsView: React.FC<ConceptExplainerResultsViewProps> = ({ result, onRestart, onNewQuestion }) => {
  return (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500 max-w-3xl mx-auto pb-10">
      {/* EXPLICACIÓN PRINCIPAL */}
      <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-xl shadow-slate-100/50 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full -mr-16 -mt-16 opacity-50" />
        
        <h3 className="text-[10px] font-black text-indigo-500 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> Análisis del Mentor
        </h3>
        
        <div className="prose prose-slate max-w-none">
          <p className="text-slate-700 leading-relaxed text-lg font-medium">
            {result.explanation}
          </p>
        </div>
      </div>

      {/* EJEMPLOS Y PUNTOS CLAVE */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-emerald-50/50 border border-emerald-100 p-6 rounded-[2rem]">
          <h4 className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Lightbulb className="w-4 h-4" /> Ejemplos Prácticos
          </h4>
          <ul className="space-y-3">
            {result.examples.map((ex, i) => (
              <li key={i} className="flex gap-3 text-sm text-emerald-900 font-medium leading-tight">
                <span className="text-emerald-400">•</span> {ex}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-indigo-50/50 border border-indigo-100 p-6 rounded-[2rem]">
          <h4 className="text-[10px] font-black text-indigo-600 uppercase tracking-widest mb-4 flex items-center gap-2">
            <ArrowRight className="w-4 h-4" /> Puntos Clave
          </h4>
          <ul className="space-y-3">
            {result.keyTakeaways.map((point, i) => (
              <li key={i} className="flex gap-3 text-sm text-indigo-900 font-medium leading-tight">
                <span className="bg-indigo-200 w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" /> {point}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* CONCEPTOS RELACIONADOS */}
      <div className="flex flex-wrap gap-2 pt-2">
        {result.relatedConcepts.map((tag, i) => (
          <span key={i} className="px-4 py-2 bg-white border border-slate-200 rounded-full text-[10px] font-black text-slate-400 uppercase tracking-tighter">
            # {tag}
          </span>
        ))}
      </div>

      {/* ACCIONES */}
      <div className="grid grid-cols-2 gap-4 pt-6">
        <button 
          onClick={onNewQuestion}
          className="py-4 bg-white border-2 border-slate-200 text-slate-600 rounded-2xl font-black uppercase text-[10px] tracking-widest hover:border-indigo-500 hover:text-indigo-600 transition-all flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" /> Nueva Duda
        </button>
        <button 
          onClick={onRestart}
          className="py-4 bg-indigo-600 text-white rounded-2xl font-black uppercase text-[10px] tracking-widest shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all flex items-center justify-center gap-2"
        >
          <RefreshCcw className="w-4 h-4" /> Finalizar Sesión
        </button>
      </div>
    </div>
  );
};

export default ConceptExplainerResultsView;
